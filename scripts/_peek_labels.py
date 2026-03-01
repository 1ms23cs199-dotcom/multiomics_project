import gzip, re

BASE = 'C:/Users/trish/multiomics_project/data/raw/genomic/'

for fname, label_key in [
    ('GSE37250_series_matrix.txt.gz', 'disease state'),
    ('GSE19435_series_matrix.txt.gz', 'illness'),
    ('GSE83456_series_matrix.txt.gz', 'disease state'),
]:
    print(f'\n=== {fname} — unique [{label_key}] values ===')
    with gzip.open(BASE + fname, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if '!Sample_characteristics_ch1' in line and label_key + ':' in line.lower():
                vals = re.findall(label_key + r': ([^\"]+)', line, re.IGNORECASE)
                unique = sorted(set(v.strip() for v in vals))
                for u in unique:
                    print(f'  {u}')
                break
            if '!series_matrix_table_begin' in line:
                break
