#!/usr/bin/env python3
"""
Compute functional covering statistics:
- How often does a functional arc span over (cover) one or more lexical arcs?
- What is the distribution of functional flux contribution?

A functional arc from A to B (span = [min(A,B), max(A,B)]) "covers" a lexical arc
from C to D if min(C,D) >= min(A,B) and max(C,D) <= max(A,B).
"""
import os, glob, re
from collections import defaultdict

UD_DATA_DIR = "data_ud"

UD_FUNCTIONAL_BASES = {'det', 'case', 'aux', 'mark', 'cop', 'cc', 'clf'}
UD_LEXICAL_BASES = {
    'nsubj', 'obj', 'iobj', 'obl', 'nmod', 'amod', 'advmod',
    'advcl', 'acl', 'xcomp', 'ccomp', 'conj', 'appos',
    'nummod', 'compound', 'flat', 'fixed', 'parataxis',
    'csubj', 'vocative', 'dislocated', 'discourse', 'list'
}

def parse_conllu(filepath):
    sentence = []
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                if sentence:
                    yield sentence
                    sentence = []
                continue
            if line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) < 8:
                continue
            tok_id = parts[0]
            if '-' in tok_id or '.' in tok_id:
                continue
            sentence.append((int(tok_id), parts[1], parts[3], int(parts[6]) if parts[6] != '_' else 0, parts[7]))
    if sentence:
        yield sentence

MAX_SENTS = 15000

results = []

for tb_dir in sorted(os.listdir(UD_DATA_DIR)):
    if not tb_dir.startswith('UD_'):
        continue
    lang = re.sub(r'^UD_', '', tb_dir).split('-')[0]
    tb_path = os.path.join(UD_DATA_DIR, tb_dir)

    # Per-language accumulators
    total_func_arcs = 0
    func_covering_lex = 0  # func arcs that cover >= 1 lexical arc
    func_covering_counts = defaultdict(int)  # how many lex arcs each covering func covers
    func_rel_covering = defaultdict(lambda: [0, 0])  # [covering, total] per func rel
    # Per func rel: what lex rels are covered
    func_covers_lex_rel = defaultdict(lambda: defaultdict(int))

    sent_count = 0
    for conllu_file in sorted(glob.glob(os.path.join(tb_path, '*.conllu'))):
        if sent_count >= MAX_SENTS:
            break
        for sent in parse_conllu(conllu_file):
            if sent_count >= MAX_SENTS:
                break
            # Build position map (exclude PUNCT)
            non_punct = [(t[0], t[2]) for t in sent if t[2] != 'PUNCT']
            if len(non_punct) < 2:
                continue
            sent_count += 1
            id_to_pos = {}
            for pos_idx, (tok_id, _) in enumerate(non_punct, 1):
                id_to_pos[tok_id] = pos_idx

            # Collect arcs with their spans
            func_arcs = []
            lex_arcs = []
            for tok_id, form, upos, head, deprel in sent:
                if upos == 'PUNCT' or head == 0:
                    continue
                if tok_id not in id_to_pos or head not in id_to_pos:
                    continue
                base = deprel.split(':')[0]
                dp = id_to_pos[tok_id]
                hp = id_to_pos[head]
                span = (min(dp, hp), max(dp, hp))
                if base in UD_FUNCTIONAL_BASES:
                    func_arcs.append((span, base, deprel))
                elif base in UD_LEXICAL_BASES:
                    lex_arcs.append((span, base, deprel))

            # For each functional arc, check if it covers any lexical arc
            for (fmin, fmax), fbase, frel in func_arcs:
                total_func_arcs += 1
                func_rel_covering[fbase][1] += 1
                if fmax - fmin <= 1:
                    # Length-1 func arc can't cover anything
                    continue
                n_covered = 0
                for (lmin, lmax), lbase, lrel in lex_arcs:
                    if lmin >= fmin and lmax <= fmax and (lmin, lmax) != (fmin, fmax):
                        n_covered += 1
                        func_covers_lex_rel[fbase][lbase] += 1
                if n_covered > 0:
                    func_covering_lex += 1
                    func_rel_covering[fbase][0] += 1
                    func_covering_counts[n_covered] += 1

    if total_func_arcs > 0:
        results.append({
            'lang': lang,
            'total_func': total_func_arcs,
            'covering': func_covering_lex,
            'pct': func_covering_lex / total_func_arcs * 100,
            'rel_covering': dict(func_rel_covering),
            'covers_what': dict(func_covers_lex_rel),
            'count_dist': dict(func_covering_counts),
            'sents': sent_count
        })

# Aggregate by language (multiple treebanks -> same lang)
from collections import Counter
lang_agg = defaultdict(lambda: {'total_func': 0, 'covering': 0, 'rel_covering': defaultdict(lambda: [0,0]),
                                  'covers_what': defaultdict(lambda: defaultdict(int)), 'count_dist': Counter()})
for r in results:
    la = lang_agg[r['lang']]
    la['total_func'] += r['total_func']
    la['covering'] += r['covering']
    for rel, (cov, tot) in r['rel_covering'].items():
        la['rel_covering'][rel][0] += cov
        la['rel_covering'][rel][1] += tot
    for frel, lcounts in r['covers_what'].items():
        for lrel, cnt in lcounts.items():
            la['covers_what'][frel][lrel] += cnt
    la['count_dist'].update(r['count_dist'])

# Print summary across all languages
print("=" * 80)
print("FUNCTIONAL COVERING STATISTICS (UD treebanks)")
print("=" * 80)

total_f = sum(la['total_func'] for la in lang_agg.values())
total_cov = sum(la['covering'] for la in lang_agg.values())
print(f"\nOverall: {total_cov:,} / {total_f:,} functional arcs cover ≥1 lexical arc ({total_cov/total_f*100:.1f}%)")

# Per functional relation
print(f"\n{'Relation':<10} {'Covering':>10} {'Total':>10} {'%':>7}")
print("-" * 40)
global_rel = defaultdict(lambda: [0, 0])
for la in lang_agg.values():
    for rel, (c, t) in la['rel_covering'].items():
        global_rel[rel][0] += c
        global_rel[rel][1] += t
for rel in sorted(global_rel, key=lambda r: global_rel[r][0]/max(global_rel[r][1],1), reverse=True):
    c, t = global_rel[rel]
    print(f"{rel:<10} {c:>10,} {t:>10,} {c/t*100:>6.1f}%")

# What lex rels do func rels cover?
print(f"\n{'Func rel':<10} covers {'Lex rel':<12} {'Count':>8}")
print("-" * 45)
global_covers = defaultdict(lambda: defaultdict(int))
for la in lang_agg.values():
    for frel, lcounts in la['covers_what'].items():
        for lrel, cnt in lcounts.items():
            global_covers[frel][lrel] += cnt
for frel in sorted(global_covers):
    for lrel, cnt in sorted(global_covers[frel].items(), key=lambda x: -x[1])[:5]:
        print(f"{frel:<10} covers {lrel:<12} {cnt:>8,}")

# Languages with highest covering %
print(f"\n=== Languages with highest % functional arcs covering lexical ===")
print(f"{'Language':<25} {'Covering':>10} {'Total':>10} {'%':>7}")
print("-" * 55)
lang_list = [(lang, la['covering'], la['total_func']) for lang, la in lang_agg.items() if la['total_func'] >= 5000]
lang_list.sort(key=lambda x: x[1]/x[2], reverse=True)
for lang, cov, tot in lang_list[:25]:
    print(f"{lang:<25} {cov:>10,} {tot:>10,} {cov/tot*100:>6.1f}%")

# Languages with lowest covering %
print(f"\n=== Languages with lowest % functional arcs covering lexical ===")
lang_list.sort(key=lambda x: x[1]/x[2])
for lang, cov, tot in lang_list[:10]:
    print(f"{lang:<25} {cov:>10,} {tot:>10,} {cov/tot*100:>6.1f}%")

# Distribution of how many lex arcs a covering func arc covers
print(f"\n=== Distribution: how many lex arcs each covering func arc spans ===")
global_dist = Counter()
for la in lang_agg.values():
    global_dist.update(la['count_dist'])
for n in sorted(global_dist):
    print(f"  covers {n} lex arc(s): {global_dist[n]:>10,} ({global_dist[n]/total_cov*100:.1f}%)")
