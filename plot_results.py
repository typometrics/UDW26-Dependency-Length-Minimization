import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import numpy as np
import os

RESULTS_FILE = "udw2026_paper/results.csv"
RELATION_FILE = "udw2026_paper/results_per_relation.csv"
FUNLEX_FILE = "udw2026_paper/results_funlex.csv"
OUTPUT_DIR = "udw2026_paper/plots"

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    df = pd.read_csv(RESULTS_FILE)
    df = df.sort_values("MDD")
    df = df[df["Language"] != "Russian-GSD"]
    df["Lang"] = df["Language"].str.replace(r"-.*", "", regex=True)

    df_fl = pd.read_csv(FUNLEX_FILE)
    df_fl = df_fl[df_fl["Language"] != "Russian-GSD"]
    df_fl["Lang"] = df_fl["Language"].str.replace(r"-.*", "", regex=True)
    # Sort by Func_MDD for consistent ordering
    df_fl = df_fl.sort_values("Func_MDD")

    df_rel = pd.read_csv(RELATION_FILE)
    df_rel = df_rel[df_rel["Language"] != "Russian-GSD"]
    df_rel["Lang"] = df_rel["Language"].str.replace(r"-.*", "", regex=True)

    # ========== Figure 1: Observed vs Random Baseline ==========
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(df))
    width = 0.35
    ax.bar(x - width/2, df["MDD"], width, yerr=df["MDD_Error"],
           capsize=3, label="Observed MDD", color="#4A90D9", edgecolor="black", linewidth=0.5)
    ax.bar(x + width/2, df["RandomMDD"], width,
           label="Random Baseline MDD", color="#E0E0E0", edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Mean Dependency Distance", fontsize=13)
    ax.set_title("Observed vs. Random Baseline MDD", fontsize=15)
    ax.set_xticks(x)
    ax.set_xticklabels(df["Lang"], rotation=45, ha="right", fontsize=11)
    ax.legend(fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "mdd_vs_random.png"), dpi=150)
    print("Saved mdd_vs_random.png")
    plt.close()

    # ========== Figure 2: Functional vs. Lexical MDD (grouped bar) ==========
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(df_fl))
    width = 0.35
    bars1 = ax.bar(x - width/2, df_fl["Func_MDD"], width,
                   yerr=df_fl["Func_CI"], capsize=3,
                   label="Functional MDD", color="#27AE60", edgecolor="black", linewidth=0.5)
    bars2 = ax.bar(x + width/2, df_fl["Lex_MDD"], width,
                   yerr=df_fl["Lex_CI"], capsize=3,
                   label="Lexical MDD", color="#E74C3C", edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Mean Dependency Distance", fontsize=13)
    ax.set_title("Functional vs. Lexical Dependency Distance", fontsize=15)
    ax.set_xticks(x)
    ax.set_xticklabels(df_fl["Lang"], rotation=45, ha="right", fontsize=11)
    ax.legend(fontsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    # Add horizontal reference line at 2.0
    ax.axhline(y=2.0, color="grey", linestyle=":", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "func_vs_lex_mdd.png"), dpi=150)
    print("Saved func_vs_lex_mdd.png")
    plt.close()

    # ========== Figure 3: Functional vs. Lexical Optimality Ratios ==========
    fig, ax = plt.subplots(figsize=(10, 5))
    df_fl_sorted = df_fl.sort_values("Lex_OptRatio")
    x = np.arange(len(df_fl_sorted))
    width = 0.35
    ax.bar(x - width/2, df_fl_sorted["Func_OptRatio"], width,
           label="Functional Opt. Ratio", color="#27AE60", edgecolor="black", linewidth=0.5)
    ax.bar(x + width/2, df_fl_sorted["Lex_OptRatio"], width,
           label="Lexical Opt. Ratio", color="#E74C3C", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(df_fl_sorted["Lang"], rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Optimality Ratio (Observed / Random)", fontsize=11)
    ax.set_title("Optimization by Dependency Type\n(lower = more optimized)", fontsize=13)
    ax.axhline(y=0.5, color="black", linestyle="--", alpha=0.3, label="50% of random")
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "func_vs_lex_optimality.png"), dpi=150)
    print("Saved func_vs_lex_optimality.png")
    plt.close()

    # ========== Figure 4: Scatter — Lexical MDD vs Head Finality ==========
    fig, ax = plt.subplots(figsize=(8, 6))
    # Merge head-final data
    df_merge = df_fl.merge(df[["Language", "HeadFinal"]], on="Language")
    ax.scatter(df_merge["HeadFinal"], df_merge["Lex_MDD"], s=100,
               c="#E74C3C", edgecolors="black", zorder=3, label="Lexical MDD")
    ax.scatter(df_merge["HeadFinal"], df_merge["Func_MDD"], s=80,
               c="#27AE60", edgecolors="black", zorder=3, marker="s", label="Functional MDD")
    for _, row in df_merge.iterrows():
        ax.annotate(row["Lang"], (row["HeadFinal"], row["Lex_MDD"]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)
    # Fit for lexical only
    z = np.polyfit(df_merge["HeadFinal"], df_merge["Lex_MDD"], 2)
    p = np.poly1d(z)
    xp = np.linspace(df_merge["HeadFinal"].min() - 0.05, df_merge["HeadFinal"].max() + 0.05, 100)
    ax.plot(xp, p(xp), "--", color="#E74C3C", alpha=0.5, label="Lexical quadratic fit")
    # Flat reference for functional
    func_mean = df_merge["Func_MDD"].mean()
    ax.axhline(y=func_mean, color="#27AE60", linestyle=":", alpha=0.5,
               label=f"Functional mean ({func_mean:.2f})")
    ax.set_xlabel("Head-Final Proportion", fontsize=13)
    ax.set_ylabel("Mean Dependency Distance", fontsize=13)
    ax.set_title("Functional (stable) vs. Lexical (variable) MDD by Head Directionality", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "func_lex_scatter.png"), dpi=150)
    print("Saved func_lex_scatter.png")
    plt.close()

    # ========== Figure 5: Per-relation heatmap ==========
    key_rels = ["nsubj", "obj", "obl", "nmod", "amod", "advmod", "det", "case"]
    df_hm = df_rel[df_rel["Relation"].isin(key_rels)].copy()
    pivot = df_hm.pivot_table(index="Lang", columns="Relation", values="MDD")
    pivot = pivot[[r for r in key_rels if r in pivot.columns]]
    pivot = pivot.sort_values("nsubj", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 8))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd", linewidths=0.5, ax=ax,
                cbar_kws={"label": "MDD"})
    ax.set_title("Per-Relation MDD Across Languages", fontsize=15)
    ax.set_ylabel("")
    ax.set_xlabel("Dependency Relation", fontsize=13)
    # Add functional/lexical labels
    ax.text(0.5, -0.02, "← Lexical →", transform=ax.transAxes, ha='left', fontsize=9, color="#E74C3C")
    ax.text(0.92, -0.02, "← Func →", transform=ax.transAxes, ha='right', fontsize=9, color="#27AE60")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "per_relation_heatmap.png"), dpi=150)
    print("Saved per_relation_heatmap.png")
    plt.close()

if __name__ == "__main__":
    main()
