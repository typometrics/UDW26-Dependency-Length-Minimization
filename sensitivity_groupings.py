#!/usr/bin/env python3
"""
Sensitivity analysis: recompute functional vs. lexical MDD
under alternative relation groupings, using existing per-relation data.

Scenarios:
  A (current)      - original groupings from the paper
  B (-conj)        - exclude conj from lexical
  C (core syntax)  - only core syntactic relations (excl conj, parataxis, discourse, flat, fixed, etc.)
  D (strictest)    - minimal func (no mark, cc) and minimal lex (no advmod, compound)
"""
import csv
import math
from collections import defaultdict

# --- Scenario definitions ---
# Each scenario maps base relations to 'functional', 'lexical', or implicitly 'excluded'

FUNCTIONAL_A = {'det', 'case', 'aux', 'mark', 'cop', 'cc', 'clf'}
LEXICAL_A = {
    'nsubj', 'obj', 'iobj', 'obl', 'nmod', 'amod', 'advmod',
    'advcl', 'acl', 'xcomp', 'ccomp', 'conj', 'appos',
    'nummod', 'compound', 'flat', 'fixed', 'parataxis',
    'csubj', 'vocative', 'dislocated', 'discourse', 'list'
}

FUNCTIONAL_B = FUNCTIONAL_A
LEXICAL_B = LEXICAL_A - {'conj'}

FUNCTIONAL_C = FUNCTIONAL_A
LEXICAL_C = {
    'nsubj', 'obj', 'iobj', 'obl', 'nmod', 'amod', 'advmod',
    'advcl', 'acl', 'xcomp', 'ccomp', 'csubj', 'nummod'
}

FUNCTIONAL_D = {'det', 'case', 'aux', 'cop', 'clf'}
LEXICAL_D = {
    'nsubj', 'obj', 'iobj', 'obl', 'nmod', 'amod',
    'advcl', 'acl', 'xcomp', 'ccomp', 'csubj'
}

SCENARIOS = {
    'A (current)':    (FUNCTIONAL_A, LEXICAL_A),
    'B (-conj)':      (FUNCTIONAL_B, LEXICAL_B),
    'C (core syntax)':(FUNCTIONAL_C, LEXICAL_C),
    'D (strictest)':  (FUNCTIONAL_D, LEXICAL_D),
}

def classify(deprel, func_set, lex_set):
    """Classify a relation by its base (before ':')."""
    base = deprel.split(':')[0] if ':' in deprel else deprel
    # Also strip SUD @ features
    base = base.split('@')[0]
    if base in func_set:
        return 'functional'
    elif base in lex_set:
        return 'lexical'
    return None

def mean(vals):
    return sum(vals) / len(vals) if vals else 0

def stdev(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))

def wilcoxon_sign(x, y):
    """Simple sign test (proportion of pairs where x < y). 
    For the real Wilcoxon we'd need scipy, but for reporting
    we compute how many languages have func < lex."""
    n = len(x)
    n_less = sum(1 for a, b in zip(x, y) if a < b)
    n_equal = sum(1 for a, b in zip(x, y) if a == b)
    n_greater = sum(1 for a, b in zip(x, y) if a > b)
    return n_less, n_equal, n_greater

def cohens_d(x, y):
    """Paired Cohen's d."""
    diffs = [a - b for a, b in zip(x, y)]
    m = mean(diffs)
    s = stdev(diffs)
    return m / s if s > 0 else float('inf')


def main():
    # Read per-relation data: Language -> Framework -> Relation -> (MDD, Count)
    data = defaultdict(lambda: defaultdict(dict))

    with open('results_all_relations.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = row['Language']
            fw = row['Framework']
            rel = row['Relation']
            mdd = float(row['MDD'])
            count = int(row['Count'])
            data[(lang, fw)][rel] = (mdd, count)

    for scenario_name, (func_set, lex_set) in SCENARIOS.items():
        print(f"\n{'='*70}")
        print(f"  Scenario: {scenario_name}")
        print(f"  Functional: {sorted(func_set)}")
        print(f"  Lexical:    {sorted(lex_set)}")
        print(f"{'='*70}")

        for fw in ['UD', 'SUD']:
            func_mdds = []
            lex_mdds = []
            lang_names = []

            for (lang, framework), rels in sorted(data.items()):
                if framework != fw:
                    continue

                # Weighted average MDD for functional and lexical
                func_sum, func_count = 0, 0
                lex_sum, lex_count = 0, 0

                for rel, (mdd, count) in rels.items():
                    cat = classify(rel, func_set, lex_set)
                    if cat == 'functional':
                        func_sum += mdd * count
                        func_count += count
                    elif cat == 'lexical':
                        lex_sum += mdd * count
                        lex_count += count

                if func_count > 0 and lex_count > 0:
                    func_mdds.append(func_sum / func_count)
                    lex_mdds.append(lex_sum / lex_count)
                    lang_names.append(lang)

            if not func_mdds:
                print(f"  {fw}: No data")
                continue

            n = len(func_mdds)
            f_mean = mean(func_mdds)
            f_std = stdev(func_mdds)
            l_mean = mean(lex_mdds)
            l_std = stdev(lex_mdds)
            gap = l_mean - f_mean
            d = cohens_d(lex_mdds, func_mdds)
            n_less, n_eq, n_greater = wilcoxon_sign(func_mdds, lex_mdds)

            print(f"\n  {fw} ({n} languages):")
            print(f"    Functional MDD: {f_mean:.2f} ± {f_std:.2f}")
            print(f"    Lexical MDD:    {l_mean:.2f} ± {l_std:.2f}")
            print(f"    Gap (lex-func): {gap:.2f}")
            print(f"    Cohen's d:      {d:.2f}")
            print(f"    func < lex in {n_less}/{n} languages ({n_less/n*100:.1f}%)")
            if n_greater > 0:
                exceptions = [lang_names[i] for i in range(n) if func_mdds[i] >= lex_mdds[i]]
                print(f"    Exceptions (func >= lex): {exceptions}")


if __name__ == '__main__':
    main()
