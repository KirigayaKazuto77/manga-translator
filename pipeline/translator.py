# pipeline/translator.py
import os
import gc
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import argostranslate.package
import argostranslate.translate

def setup_argos():
    """Ensures the JA->EN and ZH->EN translation packages are downloaded for Argos."""
    print("Initializing Argos Translate (Hard Fallback)...")
    argostranslate.package.update_package_index()
    installed = argostranslate.package.get_installed_packages()
    available_packages = argostranslate.package.get_available_packages()
    
    for lang_code in ['ja', 'zh']:
        if not any(p.from_code == lang_code and p.to_code == 'en' for p in installed):
            print(f"Downloading Argos Translate {lang_code.upper()}->EN package...")
            package = next(
                (x for x in available_packages if x.from_code == lang_code and x.to_code == 'en'), 
                None
            )
            if package:
                argostranslate.package.install_from_path(package.download())
                print(f"Argos {lang_code.upper()}->EN package installed.")
            else:
                print(f"[Warning] Could not find {lang_code.upper()}->EN package for Argos.")

# Run Argos setup once on import
setup_argos()

def batch_translate(ocr_results, source_lang="ja", engine="nllb-600m"):
    """
    Dynamically loads the chosen model, processes all text at once, 
    and aggressively frees the GPU memory afterward.
    """
    print(f"\n--- Starting Translation Phase ---")
    print(f"Engine: {engine.upper()} | Source: {source_lang}")
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    # Map UI selections to HuggingFace repo IDs
    model_map = {
        "nllb-600m": "facebook/nllb-200-distilled-600M",
        "nllb-1.3b-distilled": "facebook/nllb-200-distilled-1.3B",
        "nllb-1.3b": "facebook/nllb-200-1.3B"
    }

    tokenizer = None
    model = None

    if "nllb" in engine:
        repo_id = model_map.get(engine, model_map["nllb-600m"])
        print(f"Loading {repo_id} into VRAM (This may take a moment)...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(repo_id)
            # CRITICAL: torch_dtype=torch.float16 cuts memory usage in half.
            # Without this, the 1.3B models will crash a 4GB GPU.
            model = AutoModelForSeq2SeqLM.from_pretrained(
                repo_id, 
                torch_dtype=torch.float16
            ).to(device)
            print("Model successfully mounted to GPU.")
        except Exception as e:
            print(f"❌ Failed to load {repo_id}: {e}")
            model = None

    # Map our UI languages to NLLB specific vocab tokens
    nllb_lang_map = {
        'ja': 'jpn_Jpan',
        'zh-hans': 'zho_Hans',
        'zh-hant': 'zho_Hant',
        'ko': 'kor_Hang'
    }
    
    translated_data = []
    engines_used = set()

    # Process all bubbles
    for item in ocr_results:
        original_text = item['text'].strip()
        
        if not original_text:
            item['english_text'] = ""
            translated_data.append(item)
            continue
            
        english_text = "[TRANSLATION FAILED]"
        used_engine_name = "None"

        # 1. Try NLLB First
        if model is not None:
            try:
                tokenizer.src_lang = nllb_lang_map.get(source_lang, 'jpn_Jpan')
                inputs = tokenizer(original_text, return_tensors="pt").to(device)
                english_vocab_id = tokenizer.convert_tokens_to_ids("eng_Latn")
                
                translated_tokens = model.generate(
                    **inputs, 
                    forced_bos_token_id=english_vocab_id, 
                    max_length=400,
                    num_beams=4,
                    repetition_penalty=1.2,
                    early_stopping=True
                )
                english_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
                used_engine_name = engine
            except Exception as e:
                print(f"[Warning] NLLB inference failed: {e}")
        
        # 2. Hard Fallback to Argos if NLLB wasn't selected or failed
        if english_text == "[TRANSLATION FAILED]" or engine == "argos":
            try:
                # Argos uses 2-letter codes for Chinese (zh) and Korean (ko)
                argos_lang = "zh" if "zh" in source_lang else source_lang
                english_text = argostranslate.translate.translate(original_text, argos_lang, 'en')
                used_engine_name = "Argos (Fallback)" if "nllb" in engine else "Argos"
            except Exception as e:
                print(f"Argos translation failed: {e}")

        engines_used.add(used_engine_name)
        item['english_text'] = english_text
        translated_data.append(item)
        print(f"Result: {english_text}")

    # --- CRITICAL MEMORY MANAGEMENT ---
    # Delete the model and tokenizer from memory to free up VRAM
    if model is not None:
        del model
        del tokenizer
        
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("VRAM flushed successfully post-Translation.")

    return translated_data, list(engines_used)