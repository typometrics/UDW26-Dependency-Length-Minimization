#!/usr/bin/env python3
"""
Analyze ALL UD and SUD treebanks for functional vs. lexical dependency length minimization.

- Concatenates all .conllu files per treebank (train+dev+test)
- Filters treebanks by minimum sentence count
- Computes MDD, random baselines, and functional/lexical split
- Outputs results to CSV
"""
import os
import glob
import random
import pandas as pd
import numpy as np
from conllu import parse_incr
from scipy import stats as sp_stats
from collections import defaultdict
import sys
import re

# --- Configuration ---
UD_DATA_DIR = "data_ud"
SUD_DATA_DIR = "data_sud_full/sud-treebanks-v2.17"
OUTPUT_DIR = "."

MIN_SENTENCES = 500  # Minimum sentences to include a treebank
N_PERMUTATIONS = 20

# UD-based functional vs. lexical classification
UD_FUNCTIONAL_BASES = {'det', 'case', 'aux', 'mark', 'cop', 'cc', 'clf'}
UD_LEXICAL_BASES = {
    'nsubj', 'obj', 'iobj', 'obl', 'nmod', 'amod', 'advmod',
    'advcl', 'acl', 'xcomp', 'ccomp', 'conj', 'appos',
    'nummod', 'compound', 'flat', 'fixed', 'parataxis',
    'csubj', 'vocative', 'dislocated', 'discourse', 'list'
}

# SUD classification:
# In SUD, functional words (aux, cop, case, mark) become heads, so their
# dependents carry comp:aux*, comp:pred, comp:obj (head=ADP), comp:obl (head=SCONJ).
# We classify based on relation label + head UPOS to disambiguate.
SUD_FUNCTIONAL_RELS = {'det', 'cc', 'clf'}  # Same direction as UD
# comp:aux* and comp:pred are functional (SUD equivalents of UD aux/cop)
SUD_FUNCTIONAL_COMP_PREFIXES = {'comp:aux', 'comp:pred'}
# comp:obj/comp:obl where head is ADP/SCONJ → functional (SUD equiv of UD case/mark)
SUD_FUNCTIONAL_HEAD_POS = {'ADP', 'SCONJ'}

SUD_LEXICAL_BASES = {
    'subj', 'mod', 'udep', 'conj', 'appos', 'vocative',
    'dislocated', 'discourse', 'parataxis',
    'flat', 'fixed', 'compound', 'nummod'
}

def classify_relation_ud(deprel):
    """Classify a UD dependency relation as functional, lexical, or other."""
    base = deprel.split(':')[0] if ':' in deprel else deprel
    if base in UD_FUNCTIONAL_BASES:
        return 'functional'
    elif base in UD_LEXICAL_BASES:
        return 'lexical'
    return 'other'

def classify_relation_sud(deprel, head_upos=None):
    """Classify a SUD dependency relation as functional, lexical, or other.
    
    In SUD, function words (aux, cop, case, mark) are promoted to heads.
    Their dependents appear under comp:aux*, comp:pred, comp:obj, comp:obl.
    We use the head's UPOS to disambiguate comp:obj/comp:obl.
    """
    # Split on @ first (SUD uses @ for deep features), then check base
    rel_core = deprel.split('@')[0]  # e.g., comp:aux@tense -> comp:aux
    base = rel_core.split(':')[0]    # e.g., comp:aux -> comp
    
    # Simple functional relations (same direction as UD)
    if base in SUD_FUNCTIONAL_RELS:
        return 'functional'
    
    # comp:aux* and comp:pred are functional (SUD equiv of UD aux/cop)
    for prefix in SUD_FUNCTIONAL_COMP_PREFIXES:
        if rel_core.startswith(prefix):
            return 'functional'
    
    # comp:obj/comp:obl where head is ADP or SCONJ → functional (SUD equiv of case/mark)
    if base == 'comp' and head_upos in SUD_FUNCTIONAL_HEAD_POS:
        return 'functional'
    
    # Lexical relations
    if base in SUD_LEXICAL_BASES:
        return 'lexical'
    
    # Remaining comp relations (comp:obj with VERB head, comp:obl with VERB head, etc.)
    if base == 'comp':
        return 'lexical'
    
    return 'other'

def find_conllu_files(data_dir, prefix):
    """Find all .conllu files and aggregate them by LANGUAGE."""
    lang_files = defaultdict(list)
    
    if not os.path.exists(data_dir):
        print(f"  Data directory {data_dir} not found")
        return lang_files
    
    for tb_dir in sorted(os.listdir(data_dir)):
        if not tb_dir.startswith(prefix):
            continue
        tb_path = os.path.join(data_dir, tb_dir)
        if not os.path.isdir(tb_path):
            continue
        
        # Extract language name: UD_French-GSD -> French
        # SUD_French-GSD -> French
        clean_name = re.sub(r'^(UD|SUD)_', '', tb_dir)
        lang_name = clean_name.split('-')[0]
        
        conllu_files = glob.glob(os.path.join(tb_path, "*.conllu"))
        if conllu_files:
            lang_files[lang_name].extend(sorted(conllu_files))
    
    return lang_files

MAX_SENTENCES_PER_LANG = 15000  # Cap sentences per language for performance

def analyze_treebank(name, files, is_sud=False):
    """Analyze a single language (aggregating files)."""
    dependency_lengths = []
    sentence_lengths = []
    head_final_count = 0
    total_dependencies = 0
    
    relation_lengths = defaultdict(list)
    func_lengths = []
    lex_lengths = []
    pron_lex_lengths = []
    nonpron_lex_lengths = []
    
    observed_total = 0
    random_totals = [0] * N_PERMUTATIONS
    func_observed_total = 0
    func_random_totals = [0] * N_PERMUTATIONS
    lex_observed_total = 0
    lex_random_totals = [0] * N_PERMUTATIONS
    sentence_count = 0
    
    for filepath in files:
        if sentence_count >= MAX_SENTENCES_PER_LANG:
            print(f"    [Limit Reached] Skipping remaining files for {name} (>{MAX_SENTENCES_PER_LANG} sents)")
            break
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for sentence in parse_incr(f):
                    if sentence_count >= MAX_SENTENCES_PER_LANG:
                        break
                    
                    
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
                    id_to_upos = {}
                    for pos_idx, t in enumerate(relevant_tokens, 1):
                        id_to_pos[t['id']] = pos_idx
                        id_to_upos[t['id']] = t.get('upos', '_')
                    
                    sent_deps = []
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
                        
                        # Classify using the appropriate framework
                        if is_sud:
                            head_upos = id_to_upos.get(head_id, '_')
                            category = classify_relation_sud(deprel, head_upos)
                        else:
                            category = classify_relation_ud(deprel)
                        
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
                            # Track PRON vs non-PRON lexical deps
                            dep_upos = id_to_upos.get(dep_id, '_')
                            if dep_upos == 'PRON':
                                pron_lex_lengths.append(distance)
                            else:
                                nonpron_lex_lengths.append(distance)
                        
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
        except Exception as e:
            print(f"    Error parsing {filepath}: {e}")
            continue
    
    if total_dependencies == 0 or sentence_count < MIN_SENTENCES:
        return None, None, None
    
    # Global metrics
    mdd = np.mean(dependency_lengths)
    sem = sp_stats.sem(dependency_lengths)
    ci = sem * 1.96
    avg_sent_len = np.mean(sentence_lengths)
    head_final_prop = head_final_count / total_dependencies
    random_mdd = np.mean([rt / total_dependencies for rt in random_totals])
    optimality_ratio = mdd / random_mdd if random_mdd > 0 else None
    
    # Use name as Language (since we pass language name)
    clean_name = name
    
    result = {
        "Treebank": name,  # Kept for compatibility, now Language name
        "Language": clean_name,
        "Framework": "SUD" if is_sud else "UD",
        "MDD": round(mdd, 3),
        "MDD_CI": round(ci, 3),
        "HeadFinal": round(head_final_prop, 3),
        "AvgSentLen": round(avg_sent_len, 1),
        "DepCount": total_dependencies,
        "SentCount": sentence_count,
        "RandomMDD": round(random_mdd, 3),
        "OptRatio": round(optimality_ratio, 3) if optimality_ratio else None
    }
    
    # Functional vs. lexical
    funlex = {"Treebank": name, "Language": clean_name, "Framework": "SUD" if is_sud else "UD"}
    if func_lengths:
        func_mdd = np.mean(func_lengths)
        func_random_mdd = np.mean([rt / len(func_lengths) for rt in func_random_totals])
        funlex["Func_MDD"] = round(func_mdd, 3)
        funlex["Func_CI"] = round(sp_stats.sem(func_lengths) * 1.96, 3)
        funlex["Func_Count"] = len(func_lengths)
        funlex["Func_RandomMDD"] = round(func_random_mdd, 3)
        funlex["Func_OptRatio"] = round(func_mdd / func_random_mdd, 3) if func_random_mdd > 0 else None
    if lex_lengths:
        lex_mdd = np.mean(lex_lengths)
        lex_random_mdd = np.mean([rt / len(lex_lengths) for rt in lex_random_totals])
        funlex["Lex_MDD"] = round(lex_mdd, 3)
        funlex["Lex_CI"] = round(sp_stats.sem(lex_lengths) * 1.96, 3)
        funlex["Lex_Count"] = len(lex_lengths)
        funlex["Lex_RandomMDD"] = round(lex_random_mdd, 3)
        funlex["Lex_OptRatio"] = round(lex_mdd / lex_random_mdd, 3) if lex_random_mdd > 0 else None
    if pron_lex_lengths:
        funlex["Pron_Lex_MDD"] = round(np.mean(pron_lex_lengths), 3)
        funlex["Pron_Lex_Count"] = len(pron_lex_lengths)
    if nonpron_lex_lengths:
        funlex["NonPron_Lex_MDD"] = round(np.mean(nonpron_lex_lengths), 3)
        funlex["NonPron_Lex_Count"] = len(nonpron_lex_lengths)
    
    # Per-relation
    rel_results = []
    for rel, lengths in sorted(relation_lengths.items()):
        if len(lengths) >= 50:
            rel_results.append({
                "Treebank": name,
                "Language": clean_name,
                "Framework": "SUD" if is_sud else "UD",
                "Relation": rel,
                "Category": classify_relation_ud(rel) if not is_sud else classify_relation_sud(rel),
                "MDD": round(np.mean(lengths), 3),
                "Count": len(lengths)
            })
    
    return result, rel_results, funlex

def main(args):
    random.seed(42)
    
    print("=" * 70)
    print(f"Analyzing all UD and SUD LANGUAGES (aggregating treebanks, min {MIN_SENTENCES} sents)")
    print(f"Shard {args.shard_id + 1}/{args.num_shards}")
    print("=" * 70)
    
    all_results = []
    all_rel_results = []
    all_funlex = []
    
    # --- UD languages ---
    print(f"\nScanning UD treebanks and grouping by language in {UD_DATA_DIR}...")
    ud_langs_full = find_conllu_files(UD_DATA_DIR, "UD_")
    ud_keys = sorted(ud_langs_full.keys())
    # Filter for shard
    my_ud_keys = [k for i, k in enumerate(ud_keys) if i % args.num_shards == args.shard_id]
    ud_langs = {k: ud_langs_full[k] for k in my_ud_keys}
    
    print(f"Found {len(ud_langs_full)} UD languages total. Processing {len(ud_langs)} in this shard.")
    
    for i, (lang_name, files) in enumerate(sorted(ud_langs.items())):
        sys.stdout.write(f"\r  [{i+1}/{len(ud_langs)}] {lang_name:<40}")
        sys.stdout.flush()
        # Pass lang_name as the 'name'
        result, rels, funlex = analyze_treebank(lang_name, files, is_sud=False)
        if result:
            all_results.append(result)
            if rels:
                all_rel_results.extend(rels)
            if funlex:
                all_funlex.append(funlex)
    
    ud_count = len([r for r in all_results if r["Framework"] == "UD"])
    print(f"\n  UD: {ud_count} languages passed the {MIN_SENTENCES}-sentence threshold")
    
    # --- SUD languages ---
    print(f"\nScanning SUD treebanks and grouping by language in {SUD_DATA_DIR}...")
    sud_langs_full = find_conllu_files(SUD_DATA_DIR, "SUD_")
    sud_keys = sorted(sud_langs_full.keys())
    # Filter for shard
    my_sud_keys = [k for i, k in enumerate(sud_keys) if i % args.num_shards == args.shard_id]
    sud_langs = {k: sud_langs_full[k] for k in my_sud_keys}
    
    print(f"Found {len(sud_langs_full)} SUD languages total. Processing {len(sud_langs)} in this shard.")
    
    for i, (lang_name, files) in enumerate(sorted(sud_langs.items())):
        sys.stdout.write(f"\r  [{i+1}/{len(sud_langs)}] {lang_name:<40}")
        sys.stdout.flush()
        result, rels, funlex = analyze_treebank(lang_name, files, is_sud=True)
        if result:
            all_results.append(result)
            if rels:
                all_rel_results.extend(rels)
            if funlex:
                all_funlex.append(funlex)
    
    sud_count = len([r for r in all_results if r["Framework"] == "SUD"])
    print(f"\n  SUD: {sud_count} languages passed the {MIN_SENTENCES}-sentence threshold")
    
    # --- Save results ---
    suffix = ""
    if args.num_shards > 1:
        suffix = f"_{args.shard_id}"
    
    df = pd.DataFrame(all_results)
    if not df.empty:
        df = df.sort_values(["Framework", "MDD"])
    out_main = os.path.join(OUTPUT_DIR, f"results_all{suffix}.csv")
    df.to_csv(out_main, index=False)
    print(f"\nSaved main results to {out_main} ({len(df)} languages)")
    
    df_rel = pd.DataFrame(all_rel_results)
    out_rel = os.path.join(OUTPUT_DIR, f"results_all_relations{suffix}.csv")
    df_rel.to_csv(out_rel, index=False)
    print(f"Saved per-relation results to {out_rel}")
    
    df_fl = pd.DataFrame(all_funlex)
    out_fl = os.path.join(OUTPUT_DIR, f"results_all_funlex{suffix}.csv")
    df_fl.to_csv(out_fl, index=False)
    print(f"Saved functional/lexical results to {out_fl}")
    
    # --- Print summary ---
    print(f"\n{'=' * 70}")
    print(f"SUMMARY (Shard {args.shard_id}/{args.num_shards}): {len(df)} qualifying languages")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard_id", type=int, default=0)
    parser.add_argument("--num_shards", type=int, default=1)
    args = parser.parse_args()
    main(args)
