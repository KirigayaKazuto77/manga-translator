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
    Translates raw text natively. Forces NLLB to treat the output as Chinese 
    if the user selected a Chinese option, regardless of the OCR engine.
    """
    if not text or not text.strip():
        return ""

    # Map the UI selection to NLLB's internal language codes
    nllb_lang_mapping = {
        "ja": "jpn_Jpan",
        "zh-hans": "zho_Hans",
        "zh-hant": "zho_Hant"
    }
    target_nllb_lang = nllb_lang_mapping.get(source_lang, "jpn_Jpan")

    # 1. Try Primary Engine (NLLB)
    if engine == "nllb" and model is not None and tokenizer is not None:
        try:
            # Tell the tokenizer what language to expect based on UI selection
            tokenizer.src_lang = target_nllb_lang
            inputs = tokenizer(text, return_tensors="pt").to(device)
            
            # Get the token ID for English so NLLB knows what language to output
            english_vocab_id = tokenizer.convert_tokens_to_ids("eng_Latn")
            
            # Generate the translation tokens
            translated_tokens = model.generate(
                **inputs, 
                forced_bos_token_id=english_vocab_id, 
                max_length=400,
                num_beams=4,              # Explores 4 different translation paths
                repetition_penalty=1.2,   # Punishes looping phrases
                early_stopping=True       # Stops exactly when sentence ends
            )
            
            # Decode the raw tokens back into readable English text
            return tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
            
        except Exception as e:
            print(f"NLLB failed during translation: {e}. Switching to fallback...")
    
    # 2. Hard Fallback Engine (Argos)
    try:
        # Route to Argos using the correct language code
        argos_lang = "zh" if "zh" in source_lang else "ja"
        return argostranslate.translate.translate(text, argos_lang, 'en')
    except Exception as e:
        print(f"Argos fallback also failed: {e}")
        return "[TRANSLATION FAILED]"