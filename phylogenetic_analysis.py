import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

# Manual mapping of languages to families (approximate for control)
LANG_FAMILIES = {
    # Indo-European
    "Afrikaans": "Indo-European", "Alemannic": "Indo-European", "Ancient_Greek": "Indo-European",
    "Armenian": "Indo-European", "Bavarian": "Indo-European", "Belarusian": "Indo-European",
    "Bhojpuri": "Indo-European", "Bulgarian": "Indo-European", "Cappadocian": "Indo-European",
    "Catalan": "Indo-European", "Central_Kurdish": "Indo-European", "Classical_Armenian": "Indo-European",
    "Croatian": "Indo-European", "Czech": "Indo-European", "Danish": "Indo-European",
    "Dutch": "Indo-European", "English": "Indo-European", "Faroese": "Indo-European",
    "French": "Indo-European", "Frisian_Dutch": "Indo-European", "Galician": "Indo-European",
    "German": "Indo-European", "Gheg": "Indo-European", "Gothic": "Indo-European",
    "Greek": "Indo-European", "Hindi": "Indo-European", "Icelandic": "Indo-European",
    "Irish": "Indo-European", "Italian": "Indo-European", "Kangri": "Indo-European",
    "Khunsari": "Indo-European", "Latgalian": "Indo-European", "Latin": "Indo-European",
    "Latvian": "Indo-European", "Ligurian": "Indo-European", "Lithuanian": "Indo-European",
    "Low_Saxon": "Indo-European", "Luxembourgish": "Indo-European", "Macedonian": "Indo-European",
    "Manx": "Indo-European", "Marathi": "Indo-European", "Middle_French": "Indo-European",
    "Nayini": "Indo-European", "Neapolitan": "Indo-European", "Norwegian": "Indo-European",
    "Occitan": "Indo-European", "Odia": "Indo-European", "Old_Church_Slavonic": "Indo-European",
    "Old_East_Slavic": "Indo-European", "Old_English": "Indo-European", "Old_French": "Indo-European",
    "Old_Irish": "Indo-European", "Old_Occitan": "Indo-European", "Pashto": "Indo-European",
    "Persian": "Indo-European", "Phrygian": "Indo-European", "Polish": "Indo-European",
    "Pomak": "Indo-European", "Portuguese": "Indo-European", "Romanian": "Indo-European",
    "Russian": "Indo-European", "Sanskrit": "Indo-European", "Scottish_Gaelic": "Indo-European",
    "Serbian": "Indo-European", "Sicilian": "Indo-European", "Sindhi": "Indo-European",
    "Slovak": "Indo-European", "Slovenian": "Indo-European", "Soi": "Indo-European",
    "Southern_Kurdish": "Indo-European", "Spanish": "Indo-European", "Swedish": "Indo-European",
    "Ukrainian": "Indo-European", "Umbrian": "Indo-European", "Upper_Sorbian": "Indo-European",
    "Urdu": "Indo-European", "Welsh": "Indo-European", "Western_Armenian": "Indo-European",
    "Yiddish": "Indo-European",

    # Uralic
    "Erzya": "Uralic", "Estonian": "Uralic", "Finnish": "Uralic", "Hungarian": "Uralic",
    "Karelian": "Uralic", "Komi_Permyak": "Uralic", "Komi_Zyrian": "Uralic", "Livvi": "Uralic",
    "Moksha": "Uralic", "Nenets": "Uralic", "North_Sami": "Uralic", "Skolt_Sami": "Uralic",
    "Veps": "Uralic",

    # Turkic
    "Azerbaijani": "Turkic", "Chuvash": "Turkic", "Kazakh": "Turkic", "Kyrgyz": "Turkic",
    "Old_Turkish": "Turkic", "Ottoman_Turkish": "Turkic", "Tatar": "Turkic", "Turkish": "Turkic",
    "Uyghur": "Turkic", "Uzbek": "Turkic", "Yakut": "Turkic",

    # Afro-Asiatic
    "Akkadian": "Afro-Asiatic", "Amharic": "Afro-Asiatic", "Ancient_Hebrew": "Afro-Asiatic",
    "Arabic": "Afro-Asiatic", "Assyrian": "Afro-Asiatic", "Beja": "Afro-Asiatic",
    "Coptic": "Afro-Asiatic", "Egyptian": "Afro-Asiatic", "Hausa": "Afro-Asiatic",
    "Hebrew": "Afro-Asiatic", "Maltese": "Afro-Asiatic", "South_Levantine_Arabic": "Afro-Asiatic",
    "Zaar": "Afro-Asiatic",

    # Sino-Tibetan
    "Burmese": "Sino-Tibetan", "Cantonese": "Sino-Tibetan", "Chinese": "Sino-Tibetan",
    "Chintang": "Sino-Tibetan", "Classical_Chinese": "Sino-Tibetan", "Naga": "Sino-Tibetan",
    "Shanghainese": "Sino-Tibetan",

    # Austronesian
    "Cebuano": "Austronesian", "Indonesian": "Austronesian", "Javanese": "Austronesian",
    "Tagalog": "Austronesian",

    # Tupian
    "Akuntsu": "Tupian", "Guajajara": "Tupian", "Guarani": "Tupian", "Kaapor": "Tupian",
    "Karo": "Tupian", "Makurap": "Tupian", "Mbya_Guarani": "Tupian", "Munduruku": "Tupian",
    "Nheengatu": "Tupian", "Teko": "Tupian", "Tupinamba": "Tupian",

    # Pama-Nyungan
    "Warlpiri": "Pama-Nyungan",

    # Dravidian
    "Tamil": "Dravidian", "Telugu": "Dravidian", "Malayalam": "Dravidian",

    # Austroasiatic
    "Vietnamese": "Austroasiatic", "Munda": "Austroasiatic",

    # Japonic
    "Japanese": "Japonic",

    # Koreanic
    "Korean": "Koreanic",

    # Kartvelian
    "Georgian": "Kartvelian",

    # Northwest Caucasian
    "Abkhaz": "Northwest Caucasian", "Abaza": "Northwest Caucasian",

    # Nakh-Daghestanian
    "Avar": "Nakh-Daghestanian",

    # Mande
    "Bambara": "Mande",

    # Niger-Congo (non-Mande/Bantu broad)
    "Wolof": "Niger-Congo", "Yoruba": "Niger-Congo", "Tswana": "Niger-Congo",
    "Atlantic": "Niger-Congo", # Placeholder

    # Ubangi
    "Northwest_Gbaya": "Ubangi",

    # Uto-Aztecan
    "Highland_Puebla_Nahuatl": "Uto-Aztecan", "Western_Sierra_Puebla_Nahuatl": "Uto-Aztecan",

    # Mayan
    "Kiche": "Mayan",

    # Quechuan
    "Quechua": "Quechuan",

    # Arawakan
    "Apurina": "Arawakan",

    # Arawan
    "Madi": "Arawan", "Paumari": "Arawan",

    # Bororoan
    "Bororo": "Bororoan",

    # Chibchan
    "Bokota": "Chibchan", "Ika": "Chibchan", "Pesh": "Chibchan",

    # Macro-Je
    "Xavante": "Macro-Je",

    # Tungusic
    "Xibe": "Tungusic", "Evenki": "Tungusic",

    # Mongolic
    "Buryat": "Mongolic", "Kalmyk": "Mongolic",

    # Chukotko-Kamchatkan
    "Chukchi": "Chukotko-Kamchatkan",

    # Eskimo-Aleut
    "Yupik": "Eskimo-Aleut",

    # Na-Dene
    "Gwichin": "Na-Dene",
    
    # Khoisan (Khoe)
    "Khoekhoe": "Khoe",

    # Tai-Kadai
    "Thai": "Tai-Kadai",

    # Isolate / Unclassified / Other
    "Basque": "Basque", "Naija": "Creole", "Haitian_Creole": "Creole",
    "Maghrebi_Arabic_French": "Code-Switching", "Turkish_German": "Code-Switching", "Telugu_English": "Code-Switching"
}

def main():
    print("Loading data...")
    # Load FunLex results (assuming correct path logic)
    df = pd.read_csv(os.path.join(BASE_DIR, "results_all_funlex.csv"))
    
    # Filter for UD
    df = df[df["Framework"] == "UD"].copy()
    
    # Clean Language names (remove -Treebank suffix)
    df["Lang"] = df["Language"].str.replace(r"-.*", "", regex=True)
    
    # Map families
    df["Family"] = df["Lang"].map(LANG_FAMILIES)
    
    # Check for missing families
    missing = df[df["Family"].isna()]["Lang"].unique()
    if len(missing) > 0:
        print(f"Warning: Missing families for: {missing}")
        # Default to 'Other' for missing to avoid error
        df["Family"] = df["Family"].fillna("Other")
        
    print(f"Loaded {len(df)} languages across {df['Family'].nunique()} families.")
    
    # Melt for regression: ID=Language, Family; Vars=Func_MDD, Lex_MDD -> Type, MDD
    long_df = df.melt(id_vars=["Language", "Family", "Lang"], 
                      value_vars=["Func_MDD", "Lex_MDD"], 
                      var_name="Type", value_name="MDD")
    
    print("\nRunning Mixed Effects Model (MDD ~ Type + (1|Family))...")
    
    try:
        # Fit Mixed Linear Model
        # formula="MDD ~ Type" means Type is Fixed Effect
        # groups="Family" means Family is Random Effect (Random Intercept)
        model = smf.mixedlm("MDD ~ Type", long_df, groups=long_df["Family"])
        result = model.fit()
        print(result.summary())
        
        # Save results to text file
        out_path = os.path.join(BASE_DIR, "phylogenetic_results.txt")
        with open(out_path, "w") as f:
            f.write(result.summary().as_text())
            f.write("\n\n")
            f.write("Method: Mixed Linear Model fitted using statsmodels.\n")
            f.write("Formula: MDD ~ Type (Fixed) + (1|Family) (Random)\n")
            f.write(f"Number of Languages: {len(df)}\n")
            f.write(f"Number of Families: {df['Family'].nunique()}\n")
            
        print(f"\nResults saved to {out_path}")
        
    except Exception as e:
        print(f"Error running model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
