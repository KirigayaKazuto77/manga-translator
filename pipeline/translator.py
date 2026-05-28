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
    # 1. Load the Tokenizer (Set source language to Japanese)
    tokenizer = AutoTokenizer.from_pretrained(
        "facebook/nllb-200-distilled-600M", 
        src_lang="jpn_Jpan"
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
    """Ensures the JA -> EN translation package is downloaded for Argos."""
    installed = argostranslate.package.get_installed_packages()
    if not any(p.from_code == 'ja' and p.to_code == 'en' for p in installed):
        print("Downloading Argos Translate JA->EN package (First time only)...")
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        ja_en_package = next(
            (x for x in available_packages if x.from_code == 'ja' and x.to_code == 'en'), 
            None
        )
        if ja_en_package:
            argostranslate.package.install_from_path(ja_en_package.download())
            print("Argos package installed.")
        else:
            print("Error: Could not find JA->EN package for Argos.")

print("Initializing Argos Translate (Hard Fallback)...")
setup_argos()

def translate_text(japanese_text):
    """
    Translates text using NLLB natively. If NLLB fails, falls back to Argos Translate.
    """
    if not japanese_text or not japanese_text.strip():
        return ""
        
    # 1. Try Primary Engine (NLLB)
    if model and tokenizer:
        try:
            # Tokenize the input text and move the tensors to the GPU
            inputs = tokenizer(japanese_text, return_tensors="pt").to(device)
            
            # Get the token ID for English so NLLB knows what language to output
            target_lang_id = tokenizer.convert_tokens_to_ids("eng_Latn")
            
            # Generate the translation tokens
            translated_tokens = model.generate(
                **inputs, 
                forced_bos_token_id=target_lang_id, 
                max_length=400,
                num_beams=4,              # Explores 4 different translation paths before picking the best one
                repetition_penalty=1.2,   # Punishes the model if it tries to loop the same phrase
                early_stopping=True       # Stops processing exactly when the sentence ends
            )
            
            # Decode the raw tokens back into readable English text
            return tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
            
        except Exception as e:
            print(f"NLLB failed during translation: {e}. Switching to fallback...")
    
    # 2. Hard Fallback Engine (Argos)
    try:
        return argostranslate.translate.translate(japanese_text, 'ja', 'en')
    except Exception as e:
        print(f"Argos fallback also failed: {e}")
        return "[TRANSLATION FAILED]"

# --- TEST BLOCK ---
if __name__ == "__main__":
    test_phrases = [
        "俺も楽しかった",
        "今日はありがとう",
        "うん！またね〜",
        "やいちさんて案外ライブに耐性あるんだね",
        "楽しかった〜",
        "ほんと？良かった〜",
        "俺で良ければ",
        "じゃあ次のライブもまた誘っちゃおうかな〜したれば",
        "じゃあ誘う！"
    ]
    
    print("\n--- Translation Test ---")
    for i, text in enumerate(test_phrases):
        english = translate_text(text)
        print(f"Bubble {i+1}:")
        print(f"  JP: {text}")
        print(f"  EN: {english}\n")