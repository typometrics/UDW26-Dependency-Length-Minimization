import csv
import math

def mean(data):
    return sum(data) / len(data)

def variance(data):
    n = len(data)
    if n < 2: return 0
    m = mean(data)
    return sum((x - m) ** 2 for x in data) / (n - 1)

def covariance(x, y):
    n = len(x)
    if n < 2: return 0
    mx = mean(x)
    my = mean(y)
    return sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (n - 1)

def pearson_r(x, y):
    cov = covariance(x, y)
    sx = math.sqrt(variance(x))
    sy = math.sqrt(variance(y))
    if sx == 0 or sy == 0: return 0
    return cov / (sx * sy)

def t_cdf(t, df):
    # Approximation I don't want to implement.
    # I'll just print t and df and check if p is extremely small (which it should be).
    # If t > 6, p < 1e-6.
    import math
    x = df / (df + t**2)
    return 1 # Placeholder, will rely on t-value magnitude. 
    # Actually, let's just output t. If t > 10, p is practically 0.

def pitman_morgan(f, l):
    s = [a + b for a, b in zip(f, l)]
    d = [a - b for a, b in zip(f, l)]
    r = pearson_r(s, d)
    n = len(f)
    t = r * math.sqrt((n - 2) / (1 - r**2))
    return t, n-2

data_ud = {'f': [], 'l': []}
data_sud = {'f': [], 'l': []}

with open('results_all_funlex.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        lang = row['Language']
        framework = row['Framework']
        # Skip duplicates or aggregations if any? No, file looks flat per lang/framework.
        try:
            f_mdd = float(row['Func_MDD'])
            l_mdd = float(row['Lex_MDD'])
        except ValueError:
            continue
            
        if framework == 'UD':
            data_ud['f'].append(f_mdd)
            data_ud['l'].append(l_mdd)
        elif framework == 'SUD':
            data_sud['f'].append(f_mdd)
            data_sud['l'].append(l_mdd)

# Stats for UD
f_ud = data_ud['f']
l_ud = data_ud['l']
print(f"UD Samples: {len(f_ud)}")
print(f"Func Var: {variance(f_ud):.4f}")
print(f"Lex Var: {variance(l_ud):.4f}")
t_ud, df_ud = pitman_morgan(f_ud, l_ud)
print(f"Pitman-Morgan t: {t_ud:.4f}")

# Stats for SUD
f_sud = data_sud['f']
l_sud = data_sud['l']
print(f"\nSUD Samples: {len(f_sud)}")
print(f"Func Var: {variance(f_sud):.4f}")
print(f"Lex Var: {variance(l_sud):.4f}")
t_sud, df_sud = pitman_morgan(f_sud, l_sud)
print(f"Pitman-Morgan t: {t_sud:.4f}")
