#!/usr/bin/env python3
# Generate plots from the full UD+SUD analysis results.
# Reads results_all.csv, results_all_funlex.csv, results_all_relations.csv.
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from adjustText import adjust_text

OUTPUT_DIR = os.path.join(BASE_DIR, "plots")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(os.path.join(BASE_DIR, "results_all.csv"))
    df_fl = pd.read_csv(os.path.join(BASE_DIR, "results_all_funlex.csv"))
    df_rel = pd.read_csv(os.path.join(BASE_DIR, "results_all_relations.csv"))

    # Short language labels (already clean in results_all.csv, but ensuring consistency)
    df["Lang"] = df["Language"]
    df_fl["Lang"] = df_fl["Language"]

    # Separate UD and SUD
    ud = df[df["Framework"] == "UD"].copy()
    sud = df[df["Framework"] == "SUD"].copy()
    fl_ud = df_fl[df_fl["Framework"] == "UD"].copy()
    fl_sud = df_fl[df_fl["Framework"] == "SUD"].copy()

    # ========== Figure 1: UD Functional vs Lexical MDD Histogram ==========
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bins = np.linspace(0.5, 5.5, 30)
    ax.hist(fl_ud["Func_MDD"].dropna(), bins=bins, alpha=0.7, color="#27AE60",
            label=f"Functional (μ={fl_ud['Func_MDD'].mean():.2f})", edgecolor="white")
    ax.hist(fl_ud["Lex_MDD"].dropna(), bins=bins, alpha=0.7, color="#E74C3C",
            label=f"Lexical (μ={fl_ud['Lex_MDD'].mean():.2f})", edgecolor="white")
    ax.set_xlabel("Mean Dependency Distance", fontsize=11)
    ax.set_ylabel("Number of languages", fontsize=11)
    ax.set_title(f"UD: Functional vs. Lexical MDD ({len(fl_ud)} languages)", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "func_lex_histogram.png"), dpi=150)
    print("Saved func_lex_histogram.png")
    plt.close()

    # ... (Figure 2 boxplot remains mostly same, just checking labels if needed) ...

    # ========== Figure 2b: Optimality Ratios Distribution ==========
    fig, ax = plt.subplots(figsize=(8, 5))
    bins_opt = np.linspace(0, 0.7, 25)
    ax.hist(fl_ud["Func_OptRatio"].dropna(), bins=bins_opt, alpha=0.7, color="#27AE60",
            label=f"Functional (μ={fl_ud['Func_OptRatio'].mean():.2f})", edgecolor="white")
    ax.hist(fl_ud["Lex_OptRatio"].dropna(), bins=bins_opt, alpha=0.7, color="#E74C3C",
            label=f"Lexical (μ={fl_ud['Lex_OptRatio'].mean():.2f})", edgecolor="white")
    ax.set_xlabel("Optimality Ratio (Observed / Random)", fontsize=11)
    ax.set_ylabel("Number of languages", fontsize=11)
    ax.set_title(f"UD: Optimality Ratios for Functional vs. Lexical Dependencies\n({len(fl_ud)} languages)", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "optimality_distribution.png"), dpi=150)
    print("Saved optimality_distribution.png")
    plt.close()

    # ========== Figure 3: Scatter — MDD vs Head Finality (SUD Axis) ==========
    fig, ax = plt.subplots(figsize=(12, 12))
    # Merge UD MDD results with SUD HeadFinal values
    # We want to see how UD MDD varies with *syntactic* head directionality (better captured by SUD)
    sud_hf = sud[["Language", "HeadFinal"]].rename(columns={"HeadFinal": "SUD_HeadFinal"})
    merged = fl_ud.merge(sud_hf, on="Language")
    merged["Label"] = merged["Language"].str.replace(r"-.*", "", regex=True)

    # Plot points
    ax.scatter(merged["SUD_HeadFinal"], merged["Lex_MDD"], s=40, alpha=0.7,
               c="#E74C3C", edgecolors="black", linewidths=0.3, label="Lexical MDD")
    ax.scatter(merged["SUD_HeadFinal"], merged["Func_MDD"], s=40, alpha=0.7,
               c="#27AE60", edgecolors="black", linewidths=0.3, marker="s", label="Functional MDD")

    # Add labels
    texts = []
    for _, row in merged.iterrows():
        # Lexical (Label only points < 0.2 or > 0.8 or outliers to avoid clutter? No, label all but adjust)
        # We label all as before
        texts.append(ax.text(row["SUD_HeadFinal"], row["Lex_MDD"], row["Label"], 
                             fontsize=8, color="#C0392B"))
        texts.append(ax.text(row["SUD_HeadFinal"], row["Func_MDD"], row["Label"], 
                             fontsize=8, color="#1D8348"))

    adjust_text(texts, ax=ax,
                force_text=(0.1, 0.25),
                force_points=(0.2, 0.5),
                expand_text=(1.05, 1.2),
                expand_points=(1.05, 1.2),
                lim=500,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.3, lw=0.5))

    # Fit lines
    subset = merged[["SUD_HeadFinal", "Lex_MDD"]].dropna()
    if len(subset) > 2:
        z_lex = np.polyfit(subset["SUD_HeadFinal"], subset["Lex_MDD"], 2)
        p_lex = np.poly1d(z_lex)
        xp = np.linspace(0, 1, 100)
        ax.plot(xp, p_lex(xp), "--", color="#E74C3C", alpha=0.5, label="Lexical quadratic fit")
 
    func_mean = merged["Func_MDD"].mean()
    ax.axhline(y=func_mean, color="#27AE60", linestyle=":", alpha=0.5,
               label=f"Functional mean ({func_mean:.2f})")
 
    ax.set_xlabel("Head-Final Proportion (SUD)", fontsize=11)
    ax.set_ylabel("Mean Dependency Distance (UD)", fontsize=11)
    ax.set_title(f"Functional (stable) vs. Lexical (variable) MDD\nby SUD Head Directionality ({len(merged)} Languages)", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(linestyle="--", alpha=0.3)
    plt.tight_layout()
    # Overwrite the old file or create new? 
    # User asked to "replace" implicitly. I'll overwrite func_lex_scatter.png to keep paper.tex valid without edits
    plt.savefig(os.path.join(OUTPUT_DIR, "func_lex_scatter.png"), dpi=150)
    print("Saved func_lex_scatter.png (using SUD HeadFinal)")
    plt.close()

    # ========== Figure 4: UD vs SUD comparison scatter ==========
    fig, ax = plt.subplots(figsize=(12, 12))
    # Match languages by Language name
    merged_fw = fl_ud.merge(fl_sud, on="Language", suffixes=("_UD", "_SUD"))
    # Shorten names for labels
    merged_fw["Label"] = merged_fw["Language"].str.replace(r"-.*", "", regex=True)

    # Plot points
    ax.scatter(merged_fw["Func_MDD_UD"], merged_fw["Func_MDD_SUD"], s=40, alpha=0.7,
               c="#27AE60", edgecolors="black", linewidths=0.3, label="Functional")
    ax.scatter(merged_fw["Lex_MDD_UD"], merged_fw["Lex_MDD_SUD"], s=40, alpha=0.7,
               c="#E74C3C", edgecolors="black", linewidths=0.3, label="Lexical")

    # Add labels
    texts = []
    for _, row in merged_fw.iterrows():
        # Functional
        texts.append(ax.text(row["Func_MDD_UD"], row["Func_MDD_SUD"], row["Label"], 
                             fontsize=8, color="#1D8348")) # Darker green for text readability
        # Lexical
        texts.append(ax.text(row["Lex_MDD_UD"], row["Lex_MDD_SUD"], row["Label"], 
                             fontsize=8, color="#C0392B")) # Darker red for text readability
    
    adjust_text(texts, ax=ax,
                force_text=(0.1, 0.25),
                force_points=(0.2, 0.5),
                expand_text=(1.05, 1.2),
                expand_points=(1.05, 1.2),
                lim=500,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.3, lw=0.5))

    lims = [0.5, 5.5]
    ax.plot(lims, lims, "--", color="grey", alpha=0.5, label="y = x")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("UD MDD", fontsize=11)
    ax.set_ylabel("SUD MDD", fontsize=11)
    ax.set_title(f"UD vs. SUD: Functional and Lexical MDD\n(matched {len(merged_fw)} languages)", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(linestyle="--", alpha=0.3)
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "ud_vs_sud_scatter.png"), dpi=150)
    print("Saved ud_vs_sud_scatter.png")
    plt.close()

    # ========== Figure 4b: Global MDD Scatter (UD vs SUD) ==========
    # Pivot global results
    pivot_global = ud[["Language", "MDD"]].merge(sud[["Language", "MDD"]], on="Language", suffixes=("_UD", "_SUD")).dropna()
    # Shorten names for labels
    pivot_global["Label"] = pivot_global["Language"].str.replace(r"-.*", "", regex=True)
    
    # Incorporate Family Mapping
    LANG_FAMILIES = {
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
    "Erzya": "Uralic", "Estonian": "Uralic", "Finnish": "Uralic", "Hungarian": "Uralic",
    "Karelian": "Uralic", "Komi_Permyak": "Uralic", "Komi_Zyrian": "Uralic", "Livvi": "Uralic",
    "Moksha": "Uralic", "Nenets": "Uralic", "North_Sami": "Uralic", "Skolt_Sami": "Uralic",
    "Veps": "Uralic",
    "Azerbaijani": "Turkic", "Chuvash": "Turkic", "Kazakh": "Turkic", "Kyrgyz": "Turkic",
    "Old_Turkish": "Turkic", "Ottoman_Turkish": "Turkic", "Tatar": "Turkic", "Turkish": "Turkic",
    "Uyghur": "Turkic", "Uzbek": "Turkic", "Yakut": "Turkic",
    "Akkadian": "Afro-Asiatic", "Amharic": "Afro-Asiatic", "Ancient_Hebrew": "Afro-Asiatic",
    "Arabic": "Afro-Asiatic", "Assyrian": "Afro-Asiatic", "Beja": "Afro-Asiatic",
    "Coptic": "Afro-Asiatic", "Egyptian": "Afro-Asiatic", "Hausa": "Afro-Asiatic",
    "Hebrew": "Afro-Asiatic", "Maltese": "Afro-Asiatic", "South_Levantine_Arabic": "Afro-Asiatic",
    "Zaar": "Afro-Asiatic",
    "Burmese": "Sino-Tibetan", "Cantonese": "Sino-Tibetan", "Chinese": "Sino-Tibetan",
    "Chintang": "Sino-Tibetan", "Classical_Chinese": "Sino-Tibetan", "Naga": "Sino-Tibetan",
    "Shanghainese": "Sino-Tibetan",
    "Cebuano": "Austronesian", "Indonesian": "Austronesian", "Javanese": "Austronesian",
    "Tagalog": "Austronesian",
    "Akuntsu": "Tupian", "Guajajara": "Tupian", "Guarani": "Tupian", "Kaapor": "Tupian",
    "Karo": "Tupian", "Makurap": "Tupian", "Mbya_Guarani": "Tupian", "Munduruku": "Tupian",
    "Nheengatu": "Tupian", "Teko": "Tupian", "Tupinamba": "Tupian",
    "Tamil": "Dravidian", "Telugu": "Dravidian", "Malayalam": "Dravidian",
    "Japanese": "Japonic", "Korean": "Koreanic", "Basque": "Basque",
    "Wolof": "Niger-Congo", "Yoruba": "Niger-Congo", "Tswana": "Niger-Congo",
    "Thai": "Tai-Kadai", "Vietnamese": "Austroasiatic"
    }
    
    pivot_global["Family"] = pivot_global["Language"].str.replace(r"-.*", "", regex=True).map(LANG_FAMILIES).fillna("Other")
    
    # Define Major Families for Coloring
    major_fams = ["Indo-European", "Uralic", "Turkic", "Afro-Asiatic", "Sino-Tibetan", "Austronesian", "Niger-Congo", "Tupian"]
    pivot_global["FamilyGroup"] = pivot_global["Family"].apply(lambda x: x if x in major_fams else "Other")
    
    # Color Map
    fam_colors = {
        "Indo-European": "#E74C3C", # Red
        "Uralic": "#3498DB",        # Blue
        "Turkic": "#2ECC71",        # Green
        "Afro-Asiatic": "#F39C12",  # Orange
        "Sino-Tibetan": "#9B59B6",  # Purple
        "Austronesian": "#1ABC9C",  # Teal
        "Niger-Congo": "#34495E",   # Dark Blue
        "Tupian": "#D35400",        # Dark Orange
        "Other": "#95A5A6"          # Grey
    }

    fig, ax = plt.subplots(figsize=(10, 8))
    
    for fam in major_fams + ["Other"]:
        subset = pivot_global[pivot_global["FamilyGroup"] == fam]
        if len(subset) == 0: continue
        ax.scatter(subset["MDD_UD"], subset["MDD_SUD"], 
                   c=fam_colors.get(fam, "grey"), label=f"{fam} (n={len(subset)})",
                   s=60, alpha=0.8, edgecolors="white", linewidths=0.5)

    # Add labels
    texts = [ax.text(row["MDD_UD"], row["MDD_SUD"], row["Label"], fontsize=8, alpha=0.7) 
             for _, row in pivot_global.iterrows()]
    
    adjust_text(texts, ax=ax, force_text=(0.1, 0.25), lim=500, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5, lw=0.5))
    
    # Diagonal line
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
        np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
    ]
    ax.plot(lims, lims, 'k--', alpha=0.5, zorder=0, label="y=x")
    
    ax.set_aspect('equal')
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("UD Global MDD", fontsize=11)
    ax.set_ylabel("SUD Global MDD", fontsize=11)
    ax.set_title(f"Global MDD Reduction: UD vs SUD by Family (n={len(pivot_global)})", fontsize=13)
    ax.grid(linestyle="--", alpha=0.3)
    ax.legend(title="Language Family", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "ud_vs_sud_global_scatter.png"), dpi=150)
    print("Saved ud_vs_sud_global_scatter.png")
    
    # Update df_rel Lang column too
    df_rel["Lang"] = df_rel["Language"]

    # ========== Figure 5: Per-Relation Scatter (UD vs SUD) ==========
    # Define mapping to comparable categories
    def get_meta_rel(row):
        f, r, c = row["Framework"], row["Relation"], row["Category"]
        # Skip subtype extensions for cleaner grouping if needed, or keep them.
        # Simple mapping based on known equivalence:
        
        # Subjects
        if r.split(":")[0] in ["nsubj", "csubj", "subj"]: return "Subject"
        
        # Objects (Lexical) - comp:obj is object if lexical
        if r.split(":")[0] in ["obj", "ccomp", "xcomp"] and c == "lexical": return "Object"
        if r.startswith("comp:obj") and c == "lexical": return "Object"
        
        # Obliques
        if r.split(":")[0] in ["obl", "iobj", "udep"]: return "Oblique"
        if r.startswith("comp:obl"): return "Oblique"

        # Modifiers
        if r.split(":")[0] in ["amod", "advmod", "nmod", "mod"]: return "Modifier"
        
        # Determiners
        if r.split(":")[0] == "det": return "Determiner"
        
        # Auxiliaries
        if r.split(":")[0] in ["aux"] or r.startswith("comp:aux"): return "Auxiliary"
        
        # Case / Adpositions / Markers (Functional)
        if (r.split(":")[0] in ["case", "mark"]) and c == "functional": return "Adposition/Marker"
        if (r.startswith("comp:obj") or r.startswith("comp:obl")) and c == "functional": return "Adposition/Marker"
        
        # Coordination
        if r.split(":")[0] == "cc": return "Coordinator"
        if r.split(":")[0] == "conj": return "Conjunct"
        
        return None

    df_rel["MetaRel"] = df_rel.apply(get_meta_rel, axis=1)
    df_meta = df_rel.dropna(subset=["MetaRel"])
    
    # Average MDD per MetaRel per Framework across ALL LANGUAGES (treating each language equally)
    # First, mean per language
    lang_grouped = df_meta.groupby(["Framework", "MetaRel", "Category", "Lang"])["MDD"].mean().reset_index()
    # Then mean of language means
    grouped = lang_grouped.groupby(["Framework", "MetaRel", "Category"])
    meta_res = grouped["MDD"].mean().reset_index()

    # Pivot for plotting
    pivot_meta = meta_res.pivot_table(index=["MetaRel", "Category"], columns="Framework", values="MDD").reset_index()
    # Filter only functional and lexical
    pivot_meta = pivot_meta[pivot_meta["Category"].isin(["functional", "lexical"])]
    
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = {"functional": "#27AE60", "lexical": "#E74C3C"}
    
    for cat in pivot_meta["Category"].unique():
        subset = pivot_meta[pivot_meta["Category"] == cat]
        ax.scatter(subset["UD"], subset["SUD"], c=colors[cat], label=cat.capitalize(), s=100, edgecolors="black", alpha=0.8, zorder=3)
        for _, row in subset.iterrows():
            ax.text(row["UD"]+0.1, row["SUD"], row["MetaRel"], fontsize=9, verticalalignment='center')
            
    lims = [0, pivot_meta[["UD", "SUD"]].max().max() + 1.0]
    ax.plot(lims, lims, "--", color="grey", alpha=0.5, zorder=2)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("UD Mean Dependency Distance", fontsize=11)
    ax.set_ylabel("SUD Mean Dependency Distance", fontsize=11)
    ax.set_title("MDD by Relation Type: UD vs. SUD", fontsize=12)
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.3, zorder=1)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "ud_sud_relations_scatter.png"), dpi=150)
    print("Saved ud_sud_relations_scatter.png")
    plt.close()
    # ========== Figure 5: Per-relation heatmap (UD, top 20 languages by data) ==========
    # Expanded list for double-column width (16 relations)
    # Functional: det, case, aux, mark, cc, cop
    # Lexical: nsubj, obj, obl, nmod, amod, advmod, ccomp, xcomp, advcl, conj
    key_rels = ["det", "case", "aux", "mark", "cc", "cop", 
                "nsubj", "obj", "obl", "nmod", "amod", "advmod", 
                "ccomp", "xcomp", "advcl", "conj"]
    ud_rel = df_rel[df_rel["Framework"] == "UD"]
    # Pick top 20 languages by total count
    top_langs = ud_rel.groupby("Language")["Count"].sum().nlargest(20).index
    df_hm = ud_rel[(ud_rel["Language"].isin(top_langs)) & (ud_rel["Relation"].isin(key_rels))].copy()
    df_hm["Lang"] = df_hm["Language"].str.replace(r"-.*", "", regex=True)
    pivot = df_hm.pivot_table(index="Lang", columns="Relation", values="MDD")
    pivot = pivot[[r for r in key_rels if r in pivot.columns]]
    if "nsubj" in pivot.columns:
        pivot = pivot.sort_values("nsubj", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 7))
    # Replace sns.heatmap with matplotlib
    im = ax.imshow(pivot, cmap="YlOrRd")
    
    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticklabels(pivot.index)
    
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            text = ax.text(j, i, f"{pivot.iloc[i, j]:.1f}",
                           ha="center", va="center", color="black", fontsize=8)

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("MDD", rotation=-90, va="bottom")
    ax.set_title("Per-Relation MDD (Top 20 UD Languages)", fontsize=13)
    ax.set_ylabel("")
    ax.set_xlabel("Dependency Relation", fontsize=11)
    ax.text(0.5, -0.02, "← Lexical →", transform=ax.transAxes, ha='left', fontsize=9, color="#E74C3C")
    ax.text(0.92, -0.02, "← Func →", transform=ax.transAxes, ha='right', fontsize=9, color="#27AE60")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "per_relation_heatmap.png"), dpi=150)
    print("Saved per_relation_heatmap.png")
    plt.close()

    # ========== Figure 6: Global MDD vs Random (top 30 UD by size) ==========
    top30 = ud.nlargest(30, "DepCount").sort_values("MDD")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(top30))
    width = 0.35
    
    ax.bar(x - width/2, top30["MDD"], width, label="Observed MDD", color="#3498DB", alpha=0.8)
    ax.bar(x + width/2, top30["RandomMDD"], width, label="Random MDD", color="#95A5A6", alpha=0.6)
    
    ax.set_xticks(x)
    ax.set_xticklabels(top30["Language"], rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Mean Dependency Distance")
    ax.set_title("Global MDD vs Random Baseline (Top 30 UD Languages)", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(top30["Lang"], rotation=45, ha="right", fontsize=8)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "mdd_vs_random.png"), dpi=150)
    print("Saved mdd_vs_random.png")
    plt.close()

    # Print comparison statistics
    print("\n=== UD vs SUD Comparison ===")
    print(f"UD  Functional MDD: {fl_ud['Func_MDD'].mean():.3f} ± {fl_ud['Func_MDD'].std():.3f}")
    print(f"SUD Functional MDD: {fl_sud['Func_MDD'].mean():.3f} ± {fl_sud['Func_MDD'].std():.3f}")
    print(f"UD  Lexical MDD:    {fl_ud['Lex_MDD'].mean():.3f} ± {fl_ud['Lex_MDD'].std():.3f}")
    print(f"SUD Lexical MDD:    {fl_sud['Lex_MDD'].mean():.3f} ± {fl_sud['Lex_MDD'].std():.3f}")
    print(f"UD  Func OptRatio:  {fl_ud['Func_OptRatio'].mean():.3f}")
    print(f"SUD Func OptRatio:  {fl_sud['Func_OptRatio'].mean():.3f}")
    print(f"UD  Lex OptRatio:   {fl_ud['Lex_OptRatio'].mean():.3f}")
    print(f"SUD Lex OptRatio:   {fl_sud['Lex_OptRatio'].mean():.3f}")
    if len(merged_fw) > 0:
        from scipy.stats import pearsonr
        r_func, p_func = pearsonr(merged_fw["Func_MDD_UD"], merged_fw["Func_MDD_SUD"])
        r_lex, p_lex = pearsonr(merged_fw["Lex_MDD_UD"], merged_fw["Lex_MDD_SUD"])
        print(f"\nUD-SUD Correlation (matched languages, n={len(merged_fw)}):")
        print(f"  Functional: r={r_func:.3f}, p={p_func:.2e}")
        print(f"  Lexical:    r={r_lex:.3f}, p={p_lex:.2e}")

    # Combine into Triple Plot (Figure 6)
    import matplotlib.image as mpimg
    try:
        img_a = mpimg.imread(os.path.join(OUTPUT_DIR, "ud_vs_sud_global_scatter.png"))
        img_b = mpimg.imread(os.path.join(OUTPUT_DIR, "ud_sud_relations_scatter.png"))
        from PIL import Image
        # Resize to match height if needed, but for now simple stacking
        # Use matplotlib to show them
        fig = plt.figure(figsize=(18, 6))
        gs = fig.add_gridspec(1, 3)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.imshow(img_a)
        ax1.axis('off')
        ax1.set_title("(a) Global MDD", y=-0.05, fontsize=12)

        ax2 = fig.add_subplot(gs[0, 1])
        ax2.imshow(img_b)
        ax2.axis('off')
        ax2.set_title("(b) Per-Relation MDD", y=-0.05, fontsize=12)

        try:
            img_c = mpimg.imread(os.path.join(OUTPUT_DIR, "ud_vs_sud_scatter.png"))
            ax3 = fig.add_subplot(gs[0, 2])
            ax3.imshow(img_c)
            ax3.axis('off')
            ax3.set_title("(c) Func vs Lex Correlation", y=-0.05, fontsize=12)
        except:
             print("Could not load ud_vs_sud_scatter.png")

        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "ud_vs_sud_triple.png"), dpi=150)
        print("Saved ud_vs_sud_triple.png")
        plt.close()
    except Exception as e:
        print(f"Error creating triple plot: {e}")


    # ========== Figure 7: Family Distribution Boxplot ==========
    # Use fl_ud (UD Functional/Lexical) and map families
    fl_ud = fl_ud.copy()
    fl_ud["Family"] = fl_ud["Language"].str.replace(r"-.*", "", regex=True).map(LANG_FAMILIES).fillna("Other")
    fl_ud["FamilyGroup"] = fl_ud["Family"].apply(lambda x: x if x in major_fams else "Other")
    
    # Melt for plotting
    fl_long = fl_ud.melt(id_vars=["Language", "FamilyGroup", "Lang"], 
                         value_vars=["Func_MDD", "Lex_MDD"], 
                         var_name="Type", value_name="MDD")
    
    # Rename types for legend
    fl_long["Type"] = fl_long["Type"].replace({"Func_MDD": "Functional", "Lex_MDD": "Lexical"})
    
    # Filter to major families only (exclude Other for cleaner plot? Or keep Other?)
    # User asked for "big families". Let's show major ones.
    fl_long_filtered = fl_long[fl_long["FamilyGroup"] != "Other"]
    
    # Sort families by median Lexical MDD
    order = fl_long_filtered[fl_long_filtered["Type"]=="Lexical"].groupby("FamilyGroup")["MDD"].median().sort_values().index
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=fl_long_filtered, x="FamilyGroup", y="MDD", hue="Type", 
                order=order, palette={"Functional": "#27AE60", "Lexical": "#E74C3C"}, ax=ax, linewidth=1)
    
    ax.set_title("Distribution of MDD by Language Family (Major Families)", fontsize=14)
    ax.set_xlabel("Language Family", fontsize=12)
    ax.set_ylabel("Mean Dependency Distance", fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(title="Dependency Type")
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "family_mdd_boxplot.png"), dpi=150)
    print("Saved family_mdd_boxplot.png")

if __name__ == "__main__":
    main()
