import os
import glob
import random
import pandas as pd
import numpy as np
from conllu import parse_incr
from scipy import stats as sp_stats
from collections import defaultdict

DATA_DIR = "udw2026_paper/data"
OUTPUT_FILE = "udw2026_paper/results.csv"
OUTPUT_RELATION_FILE = "udw2026_paper/results_per_relation.csv"
OUTPUT_FUNLEX_FILE = "udw2026_paper/results_funlex.csv"

N_PERMUTATIONS = 20

# UD-based functional vs. lexical classification
FUNCTIONAL_RELS = {
    'det', 'case', 'aux', 'mark', 'cop', 'cc', 'clf', 'aux:pass',
    'det:poss', 'case:gen', 'case:acc'
}

LEXICAL_RELS = {
    'nsubj', 'obj', 'iobj', 'obl', 'nmod', 'amod', 'advmod',
    'advcl', 'acl', 'xcomp', 'ccomp', 'conj', 'appos',
    'nummod', 'compound', 'flat', 'fixed', 'parataxis',
    'nsubj:pass', 'obl:agent', 'obl:arg', 'acl:relcl',
    'csubj', 'vocative', 'dislocated', 'discourse', 'list',
    'orphan', 'reparandum', 'dep'
}

def classify_relation(deprel):
    """Classify a UD relation as functional, lexical, or other."""
    base = deprel.split(':')[0] if ':' in deprel else deprel
    if deprel in FUNCTIONAL_RELS or base in {'det', 'case', 'aux', 'mark', 'cop', 'cc', 'clf'}:
        return 'functional'
    elif deprel in LEXICAL_RELS or base in {'nsubj', 'obj', 'iobj', 'obl', 'nmod', 'amod', 'advmod',
                                              'advcl', 'acl', 'xcomp', 'ccomp', 'conj', 'appos',
                                              'nummod', 'compound', 'flat', 'fixed', 'parataxis',
                                              'csubj', 'vocative', 'dislocated', 'discourse', 'list',
                                              'orphan', 'reparandum', 'dep'}:
        return 'lexical'
    return 'other'

def analyze_treebank(filepath):
    print(f"Analyzing {filepath}...")

    dependency_lengths = []
    sentence_lengths = []
    head_final_count = 0
    total_dependencies = 0

    # Per-relation tracking
    relation_lengths = defaultdict(list)

    # Functional vs. lexical tracking
    func_lengths = []
    lex_lengths = []

    # For random baseline (global, functional, lexical)
    observed_total = 0
    random_totals = [0] * N_PERMUTATIONS
    func_observed_total = 0
    func_random_totals = [0] * N_PERMUTATIONS
    lex_observed_total = 0
    lex_random_totals = [0] * N_PERMUTATIONS
    sentence_count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for sentence in parse_incr(f):
            relevant_tokens = []
            for t in sentence:
                if not isinstance(t['id'], int):
                    continue
                if t['upos'] == 'PUNCT':
                    continue
                relevant_tokens.append(t)

            sent_len = len(relevant_tokens)
            if sent_len < 2:
                continue

            sentence_lengths.append(sent_len)
            sentence_count += 1

            id_to_pos = {}
            for pos_idx, t in enumerate(relevant_tokens, 1):
                id_to_pos[t['id']] = pos_idx

            sent_deps = []  # (dep_pos, head_pos, deprel, category)
            for t in relevant_tokens:
                head_id = t['head']
                dep_id = t['id']
                deprel = t['deprel']

                if head_id == 0 or head_id is None:
                    continue
                if head_id not in id_to_pos:
                    continue

                dep_pos = id_to_pos[dep_id]
                head_pos = id_to_pos[head_id]
                distance = abs(head_pos - dep_pos)
                category = classify_relation(deprel)

                dependency_lengths.append(distance)
                relation_lengths[deprel].append(distance)
                total_dependencies += 1
                observed_total += distance

                if category == 'functional':
                    func_lengths.append(distance)
                    func_observed_total += distance
                elif category == 'lexical':
                    lex_lengths.append(distance)
                    lex_observed_total += distance

                if head_pos > dep_pos:
                    head_final_count += 1

                sent_deps.append((dep_pos, head_pos, deprel, category))

            # Random baseline
            positions = list(range(1, sent_len + 1))
            for perm_i in range(N_PERMUTATIONS):
                shuffled = positions[:]
                random.shuffle(shuffled)
                pos_map = dict(zip(positions, shuffled))

                rand_total = 0
                func_rand_total = 0
                lex_rand_total = 0
                for dep_pos, head_pos, _, cat in sent_deps:
                    d = abs(pos_map[dep_pos] - pos_map[head_pos])
                    rand_total += d
                    if cat == 'functional':
                        func_rand_total += d
                    elif cat == 'lexical':
                        lex_rand_total += d

                random_totals[perm_i] += rand_total
                func_random_totals[perm_i] += func_rand_total
                lex_random_totals[perm_i] += lex_rand_total

    if total_dependencies == 0:
        return None, None, None

    # Global metrics
    mdd = np.mean(dependency_lengths)
    sem = sp_stats.sem(dependency_lengths)
    ci = sem * 1.96
    avg_sent_len = np.mean(sentence_lengths)
    norm_mdd = mdd / avg_sent_len
    head_final_prop = head_final_count / total_dependencies
    random_mdd = np.mean([rt / total_dependencies for rt in random_totals])
    optimality_ratio = mdd / random_mdd

    lang_name = os.path.basename(filepath).replace(".conllu", "")

    result = {
        "Language": lang_name,
        "MDD": round(mdd, 3),
        "MDD_Error": round(ci, 3),
        "NormMDD": round(norm_mdd, 3),
        "HeadFinal": round(head_final_prop, 3),
        "AvgSentenceLength": round(avg_sent_len, 1),
        "DependencyCount": total_dependencies,
        "TokenCount": sum(sentence_lengths),
        "RandomMDD": round(random_mdd, 3),
        "OptimalityRatio": round(optimality_ratio, 3)
    }

    # Functional vs. Lexical metrics
    funlex_result = {"Language": lang_name}
    if func_lengths:
        func_mdd = np.mean(func_lengths)
        func_random_mdd = np.mean([rt / len(func_lengths) for rt in func_random_totals])
        funlex_result["Func_MDD"] = round(func_mdd, 3)
        funlex_result["Func_CI"] = round(sp_stats.sem(func_lengths) * 1.96, 3)
        funlex_result["Func_Count"] = len(func_lengths)
        funlex_result["Func_RandomMDD"] = round(func_random_mdd, 3)
        funlex_result["Func_OptRatio"] = round(func_mdd / func_random_mdd, 3) if func_random_mdd > 0 else None
    if lex_lengths:
        lex_mdd = np.mean(lex_lengths)
        lex_random_mdd = np.mean([rt / len(lex_lengths) for rt in lex_random_totals])
        funlex_result["Lex_MDD"] = round(lex_mdd, 3)
        funlex_result["Lex_CI"] = round(sp_stats.sem(lex_lengths) * 1.96, 3)
        funlex_result["Lex_Count"] = len(lex_lengths)
        funlex_result["Lex_RandomMDD"] = round(lex_random_mdd, 3)
        funlex_result["Lex_OptRatio"] = round(lex_mdd / lex_random_mdd, 3) if lex_random_mdd > 0 else None

    # Per-relation results
    rel_results = []
    for rel, lengths in sorted(relation_lengths.items()):
        if len(lengths) >= 50:
            rel_results.append({
                "Language": lang_name,
                "Relation": rel,
                "Category": classify_relation(rel),
                "MDD": round(np.mean(lengths), 3),
                "Count": len(lengths)
            })

    return result, rel_results, funlex_result

def main():
    random.seed(42)

    results = []
    all_rel_results = []
    funlex_results = []

    conllu_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.conllu")))

    if not conllu_files:
        print("No .conllu files found in data directory.")
        return

    for filepath in conllu_files:
        result, rel_results, funlex = analyze_treebank(filepath)
        if result:
            results.append(result)
        if rel_results:
            all_rel_results.extend(rel_results)
        if funlex:
            funlex_results.append(funlex)

    df = pd.DataFrame(results)
    df = df.sort_values("MDD")
    print("\n=== Main Results ===")
    print(df.to_string(index=False))
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to {OUTPUT_FILE}")

    df_rel = pd.DataFrame(all_rel_results)
    df_rel.to_csv(OUTPUT_RELATION_FILE, index=False)
    print(f"Saved per-relation results to {OUTPUT_RELATION_FILE}")

    df_fl = pd.DataFrame(funlex_results)
    df_fl = df_fl.sort_values("Language")
    print("\n=== Functional vs. Lexical MDD ===")
    cols = ["Language", "Func_MDD", "Func_CI", "Func_OptRatio", "Func_Count",
            "Lex_MDD", "Lex_CI", "Lex_OptRatio", "Lex_Count"]
    print(df_fl[[c for c in cols if c in df_fl.columns]].to_string(index=False))
    df_fl.to_csv(OUTPUT_FUNLEX_FILE, index=False)
    print(f"Saved to {OUTPUT_FUNLEX_FILE}")

if __name__ == "__main__":
    main()
