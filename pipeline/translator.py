# pipeline/translator.py
import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import argostranslate.package
import argostranslate.translate

print("Initializing NLLB-200 (Primary Engine)...")
# Detect your GTX 1650 Ti (cuda:0). If it fails, fallback to CPU
device = "cuda:0" if torch.cuda.is_available() else "cpu"

try:
    # 1. Load the Tokenizer (Dynamic source language handling applied during execution)
    tokenizer = AutoTokenizer.from_pretrained(
        "facebook/nllb-200-distilled-600M"
    )
    # 2. Load the Model directly onto the GPU
    model = AutoModelForSeq2SeqLM.from_pretrained(
        "facebook/nllb-200-distilled-600M"
    ).to(device)
    
    print(f"NLLB initialized successfully on {device.upper()}")
except Exception as e:
    print(f"Failed to load NLLB: {e}")
    model = None
    tokenizer = None

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
                print(f"Error: Could not find {lang_code.upper()}->EN package for Argos.")

# Run setup
setup_argos()

def translate_text(text, source_lang="ja", engine="nllb"):
    """
    Translates text and tracks exactly which engine succeeded.
    Returns: (translated_text, engine_used)
    """
    if engine == "nllb":
        if model is not None and tokenizer is not None:
            try:
                # Tell the tokenizer what language to expect based on UI selection
                tokenizer.src_lang = "jpn_Jpan" if source_lang == "ja" else "zho_Hans" # adjust map as needed
                inputs = tokenizer(text, return_tensors="pt").to(device)
                
                english_vocab_id = tokenizer.convert_tokens_to_ids("eng_Latn")
                
                translated_tokens = model.generate(
                    **inputs, 
                    forced_bos_token_id=english_vocab_id, 
                    max_length=400,
                    num_beams=4,
                    repetition_penalty=1.2,
                    early_stopping=True
                )
                
                decoded_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
                return decoded_text, "NLLB"
                
            except Exception as e:
                print(f"NLLB failed during translation: {e}. Switching to fallback...")
        else:
            print("NLLB model not loaded. Switching to fallback...")
            
        # Hard Fallback Engine (Argos)
        try:
            argos_lang = "zh" if "zh" in source_lang else "ja"
            decoded_text = argostranslate.translate.translate(text, argos_lang, 'en')
            return decoded_text, "Argos (Fallback)"
        except Exception as e:
            print(f"Argos fallback also failed: {e}")
            return "[TRANSLATION FAILED]", "None"
            
    else:
        # Explicit Argos engine request
        try:
            argos_lang = "zh" if "zh" in source_lang else "ja"
            decoded_text = argostranslate.translate.translate(text, argos_lang, 'en')
            return decoded_text, "Argos"
        except Exception as e:
            print(f"Argos translation failed: {e}")
            return "[TRANSLATION FAILED]", "None"