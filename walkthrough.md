# Walkthrough: Full UD + SUD 2.17 Extension

## What Was Done

Extended the functional vs. lexical DLM analysis from a treebank-based approach to a **language-based approach**, analyzing **102 UD languages** and **102 SUD languages**. We concatenated all available treebanks for each language to ensure robust, typologically valid results.

### 1. Data Download
- **UD 2.17**: Downloaded from LINDAT (~2GB tgz), extracted 339 treebank directories
- **SUD 2.17**: Downloaded from `grew.fr/download/sud-treebanks-v2.17.tgz` (~518MB), extracted 338 treebank directories

### 2. SUD Classifier Fix
The initial SUD functional/lexical classification was incorrect because SUD reverses head direction for function words. In SUD:
- `aux` → `comp:aux@*` (auxiliary becomes head)
- `cop` → `comp:pred` (copula becomes head)
- `case` → `comp:obj` with ADP head (adposition becomes head)
- `mark` → `comp:obl` with SCONJ head (complementizer becomes head)

Fixed by using the **head's UPOS tag** to disambiguate `comp:obj/obl`. Variance dropped from 1.22 to **0.34**, matching UD.

### 3. Key Results

| | Languages | Func MDD | Lex MDD | Func Ratio | Lex Ratio |
|---|:---:|:---:|:---:|:---:|:---:|
| **UD** | 102 | 1.73 ± 0.33 | 2.92 ± 0.62 | 0.27 | 0.44 |
| **SUD** | 102 | 1.67 ± 0.31 | 2.51 ± 0.46 | 0.26 | 0.39 |

UD–SUD correlation across matched languages: **r = 0.93** (functional), **r = 0.92** (lexical)

![Global MDD Reduction](/Users/kimgerdes/.gemini/antigravity/brain/907f1f7d-2ac1-4cff-8c62-3974b7a3843b/ud_vs_sud_global_scatter.png)
*Figure: Global MDD reduction in SUD vs UD. Nearly all languages fall below the diagonal.*

### 4. Files Modified/Created
- [analyze_all.py](file:///Users/kimgerdes/Documents/programming/paper%20test/udw2026_paper/analyze_all.py) — fixed SUD classifier
- [plot_all.py](file:///Users/kimgerdes/Documents/programming/paper%20test/udw2026_paper/plot_all.py) — new plotting script
- [paper.tex](file:///Users/kimgerdes/Documents/programming/paper%20test/udw2026_paper/paper.tex) — rewritten for 403-treebank results
- 6 new plots in `plots/` directory
- 3 CSV result files: `results_all.csv`, `results_all_funlex.csv`, `results_all_relations.csv`

### 5. Verification
- Paper compiles to 4 pages with xelatex, no errors or overfull boxes
- All citations resolved
- All 6 figures render correctly

### 6. Per-Relation UD vs. SUD Analysis
To rigorously test robustness, we added a fine-grained comparison of MDD for equivalent relation types across frameworks (e.g., UD `nsubj` vs. SUD `subj`, UD `case` vs. SUD `comp:obj`).

- **Method**: Mapped relations to meta-categories (Subject, Object, Oblique, Modifier, Functional Head-Dep) and computed mean MDD across all languages (treating each language equally).
- **Result**: Confirmed that functional relations are universally short in both frameworks, even when head direction is reversed (e.g., Adpositions).
- **Visualization**: Added `ud_sud_relations_scatter.png` (Figure 6) to the paper.

![Per-Relation Scatter](/Users/kimgerdes/.gemini/antigravity/brain/907f1f7d-2ac1-4cff-8c62-3974b7a3843b/ud_sud_relations_scatter.png)

## Round 2 Revisions

Based on the second round of reviews, we addressed the three most urgent criticisms:

### 1. Formal Significance Testing (Mathematician #1)
Added a paragraph to Section 4.2 reporting paired Wilcoxon tests ($p < 10^{-18}$) and Cohen's $d$ (> 2.0), confirming the functional-lexical gap is statistically significant.

![Significance Test Paragraph](/Users/kimgerdes/.gemini/antigravity/brain/907f1f7d-2ac1-4cff-8c62-3974b7a3843b/significance_test_paragraph_1771107672284.png)

### 2. SUD Relation Mapping (UD Specialist #2)
Replaced the brief SUD description with a detailed table (Table 2) showing the exact mapping from UD to SUD relations and the criteria for classifying `comp:obj` / `comp:obl` as functional vs. lexical.

![SUD Mapping Table](/Users/kimgerdes/.gemini/antigravity/brain/907f1f7d-2ac1-4cff-8c62-3974b7a3843b/sud_mapping_table_1771107672759.png)

### 3. Sensitivity Analysis (Syntactician #1)
Added a new subsection **4.7 Sensitivity Analysis** to the Results, demonstrating that the main findings hold even when `advmod` is reclassified as functional or excluded entirely.

![Sensitivity Analysis Section](/Users/kimgerdes/.gemini/antigravity/brain/907f1f7d-2ac1-4cff-8c62-3974b7a3843b/sensitivity_analysis_section_1771107673175.png)

### 4. Figure 1 Update
Replaced the example sentence in Figure 1 with the Che Guevara quote ("Let me say that the true revolutionary is guided by a great feeling of love"), confirming it fits horizontally within the page margins.

![Figure 1 Update](/Users/kimgerdes/.gemini/antigravity/brain/907f1f7d-2ac1-4cff-8c62-3974b7a3843b/figure1_check_1771108427226.png)

