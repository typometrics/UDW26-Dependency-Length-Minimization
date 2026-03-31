import os
import requests

# Updated based on "Typologist" review
TREEBANKS = {
    # INDO-EUROPEAN
    "English-EWT": "https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/master/en_ewt-ud-train.conllu",
    "French-GSD": "https://raw.githubusercontent.com/UniversalDependencies/UD_French-GSD/master/fr_gsd-ud-train.conllu",
    "German-GSD": "https://raw.githubusercontent.com/UniversalDependencies/UD_German-GSD/master/de_gsd-ud-train.conllu",
    "Russian-GSD": "https://raw.githubusercontent.com/UniversalDependencies/UD_Russian-GSD/master/ru_gsd-ud-train.conllu",

    # URALIC
    "Finnish-TDT": "https://raw.githubusercontent.com/UniversalDependencies/UD_Finnish-TDT/master/fi_tdt-ud-train.conllu",
    
    # ALTAIC / TURKIC / JAPONIC
    "Turkish-IMST": "https://raw.githubusercontent.com/UniversalDependencies/UD_Turkish-IMST/master/tr_imst-ud-train.conllu",
    "Japanese-GSD": "https://raw.githubusercontent.com/UniversalDependencies/UD_Japanese-GSD/master/ja_gsd-ud-train.conllu",
    
    # SEMITIC
    "Hebrew-HTB": "https://raw.githubusercontent.com/UniversalDependencies/UD_Hebrew-HTB/master/he_htb-ud-train.conllu",
    "Arabic-PADT": "https://raw.githubusercontent.com/UniversalDependencies/UD_Arabic-PADT/master/ar_padt-ud-train.conllu",
    
    # SINO-TIBETAN
    "Chinese-GSD": "https://raw.githubusercontent.com/UniversalDependencies/UD_Chinese-GSD/master/zh_gsd-ud-train.conllu",
    
    # AUSTRONESIAN
    "Indonesian-GSD": "https://raw.githubusercontent.com/UniversalDependencies/UD_Indonesian-GSD/master/id_gsd-ud-train.conllu",
    
    # NIGER-CONGO
    "Wolof-WTB": "https://raw.githubusercontent.com/UniversalDependencies/UD_Wolof-WTB/master/wo_wtb-ud-train.conllu",
    "Yoruba-YTB": "https://raw.githubusercontent.com/UniversalDependencies/UD_Yoruba-YTB/master/yo_ytb-ud-test.conllu",
    
    # DRAVIDIAN
    "Tamil-TTB": "https://raw.githubusercontent.com/UniversalDependencies/UD_Tamil-TTB/master/ta_ttb-ud-train.conllu",
    
    # ISOLATE / OTHERS
    "Basque-BDT": "https://raw.githubusercontent.com/UniversalDependencies/UD_Basque-BDT/master/eu_bdt-ud-train.conllu",
    "Thai-PUD": "https://raw.githubusercontent.com/UniversalDependencies/UD_Thai-PUD/master/th_pud-ud-test.conllu", 
    "Hindi-HDTB": "https://raw.githubusercontent.com/UniversalDependencies/UD_Hindi-HDTB/master/hi_hdtb-ud-train.conllu"
}

DATA_DIR = "udw2026_paper/data"

def download_file(url, filepath):
    msg = f"Downloading {url} to {filepath}..."
    print(msg)
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Successfully downloaded {filepath}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created directory: {DATA_DIR}")

    for name, url in TREEBANKS.items():
        filename = f"{name}.conllu"
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            print(f"{filename} already exists. Skipping.")
        else:
            download_file(url, filepath)

if __name__ == "__main__":
    main()
