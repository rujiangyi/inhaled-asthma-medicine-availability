"""Format four compact English tables from existing CSVs without rerunning analyses."""
from pathlib import Path
import csv
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '表格'
REPORT = ROOT / '报告'
REPORT.mkdir(exist_ok=True)
SOURCES = {}


def read_csv(name):
    path = SOURCE / name
    SOURCES[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def number(value):
    return float(value)


def integer(value):
    return int(float(value))


def select(rows, **criteria):
    selected = [r for r in rows if all(str(r[k]) == str(v) for k, v in criteria.items())]
    assert len(selected) == 1, (criteria, len(selected))
    return selected[0]


def p_value(value):
    return f'{float(value):.4g}'


def or_ci(row):
    return f"{number(row['odds_ratio']):.2f} ({number(row['ci95_lower']):.2f}–{number(row['ci95_upper']):.2f})"


counts = read_csv('药物逐轮计数.csv')
coverage = read_csv('样本全球覆盖.csv')
paired = read_csv('配对药物变化.csv')
trajectories = read_csv('ICS轨迹负担与人口.csv')
models = read_csv('四项预设模型.csv')
cross = read_csv('ICS轨迹与复方交叉.csv')
countries = read_csv('国家分析表.csv')
tables = []

rows = []
def add_count(label, numerator, denominator):
    rows.append([label, f'{numerator:,} / {denominator:,}', f'{100 * numerator / denominator:.1f}'])

add_count('WHO country records, 2021', len(countries), len(countries))
for year in [2017, 2019, 2021]:
    match = select(counts, sample='all_available_paired_items', year=year, medicine='ics')
    add_count(f'Two basic medicine answers valid, {year}', integer(match['valid_n']), len(countries))
add_count('Fixed three-wave panel', 168, len(countries))
add_count('All three medicine answers valid, 2021', sum(all(r[k] in ['Yes', 'No'] for k in ['ics2021', 'bronch2021', 'combo2021']) for r in countries), len(countries))
combo_known = sum(integer(r['country_n']) for r in cross if r['combo2021'] != 'Unknown')
add_count('Known combination-inhaler answer within panel, 2021', combo_known, 168)
for medicine, label in [('ics', 'Reported ICS Yes'), ('bronch', 'Bronchodilator Yes')]:
    for year in [2017, 2019, 2021]:
        match = select(counts, sample='fixed168', year=year, medicine=medicine)
        add_count(f'{label}, {year} (fixed panel)', integer(match['yes_n']), integer(match['eligible_n']))
combo_groups = {answer: sum(integer(r['country_n']) for r in cross if r['combo2021'] == answer) for answer in ['Yes', 'No', 'Unknown']}
rows.append(['Combination inhaler Yes / No / Unknown, 2021 (panel)',
             f"{combo_groups['Yes']} / {combo_groups['No']} / {combo_groups['Unknown']} (N=168)",
             ' / '.join(f'{100 * combo_groups[x] / 168:.1f}' for x in ['Yes', 'No', 'Unknown'])])
panel_coverage = select(coverage, sample='balanced168', year=2021)
tables.append({
    'id': 'Table 1', 'title': 'Analysis samples and main availability counts',
    'headers': ['Sample or reported status', 'n / denominator', '%'], 'rows': rows,
    'notes': [
        'Valid means an explicit Yes or No. Unknown answers remain separate. Samples overlap; they are not a nested flow. Basic items are reported ICS and bronchodilator inhalers.',
        f"The 168-country panel covers {number(panel_coverage['resident_population_percent_global204']):.2f}% of the population aged ≥25 years and {number(panel_coverage['daly_percent_global204']):.2f}% of asthma DALYs in the 204-country/territory GBD input frame in 2021.",
    ], 'sources': ['药物逐轮计数.csv', '样本全球覆盖.csv', 'ICS轨迹与复方交叉.csv', '国家分析表.csv']})

rows = []
for medicine, label in [('ics', 'Reported ICS'), ('bronch', 'Bronchodilator')]:
    for before, after in [(2017, 2019), (2019, 2021), (2017, 2021)]:
        row = select(paired, medicine=medicine, before=before, after=after)
        rows.append([label, f'{before}–{after}', str(integer(row['no_yes'])), str(integer(row['yes_no'])),
                     f"{number(row['change_percentage_points']):+.2f}", p_value(row['p_exact_mcnemar']),
                     p_value(row['p_holm_within_medicine_three_comparisons'])])
tables.append({
    'id': 'Table 2', 'title': 'Paired changes in reported availability in the fixed panel',
    'headers': ['Medicine', 'Years', 'No→Yes', 'Yes→No', 'Change, pp', 'Exact p', 'Holm p'], 'rows': rows,
    'notes': ['Every comparison uses the same 168 countries. Change is later minus earlier Yes prevalence in percentage points (pp). Two-sided exact McNemar p values are supplementary; Holm adjustment forms a separate family of three year comparisons for each medicine.'],
    'sources': ['配对药物变化.csv']})

rows = []
for row in trajectories:
    rows.append([row['trajectory'], f"{integer(row['country_n'])} ({number(row['country_percent']):.1f}%)",
                 f"{number(row['resident_population_percent_sample']):.2f}", f"{number(row['daly_percent_sample']):.2f}",
                 f"{number(row['resident_population_percent_global204']):.2f}", f"{number(row['daly_percent_global204']):.2f}"])
tables.append({
    'id': 'Table 3', 'title': 'Reported ICS sequences and shares of resident population and asthma DALYs',
    'headers': ['ICS sequence', 'Countries, n (%)', 'Population share: panel, %', 'DALY share: panel, %',
                'Population share: global, %', 'DALY share: global, %'], 'rows': rows,
    'notes': [
        'Y=Yes and N=No in 2017, 2019 and 2021. Panel denominators are 168 countries; global denominators are 204 GBD countries/territories.',
        'Population and DALYs are for 2021, ages ≥25. Population shares describe residents of reporting countries, not untreated people. DALY shares use point estimates without joint uncertainty intervals.',
    ], 'sources': ['ICS轨迹负担与人口.csv']})

rows = []
for outcome, outcome_label in [('ics2021', 'Reported ICS No'), ('combo2021', 'Combination inhaler No')]:
    for economic, label in [('gdp', 'GDP: primary'), ('health', 'Health spending: sensitivity')]:
        name = f'{outcome}_{economic}'
        econ = select(models, model_id=name, variable=economic)
        pm25 = select(models, model_id=name, variable='pm25')
        oop = select(models, model_id=name, variable='oop')
        rows.append([f'{outcome_label}; {label}', f"{integer(econ['complete_n'])} / {integer(econ['events_no'])}",
                     or_ci(econ), or_ci(pm25), or_ci(oop)])
tables.append({
    'id': 'Table 4', 'title': 'Prespecified exploratory logistic models: odds ratios (95% confidence intervals)',
    'headers': ['Outcome and specification', 'Complete n / No events', 'Economic measure, per doubling',
                'PM2.5, per 10 µg/m³', 'Out-of-pocket share, per 10 pp'], 'rows': rows,
    'notes': [
        'No=1. Eligible n=181 for reported ICS and 157 for budesonide–formoterol; complete-case n varies. Economic measures are log2: GDP per capita in constant 2021 PPP dollars; health spending per capita in current PPP dollars. Out-of-pocket share uses current health expenditure as denominator.',
        'Health spending replaces GDP only in sensitivity models. HC1 robust 95% Wald intervals are shown. Models passed the prespecified checks; no p-value selection or causal interpretation was used.',
    ], 'sources': ['四项预设模型.csv']})

assert len(tables) == 4
assert len(tables[1]['rows']) == 6 and len(tables[2]['rows']) == 8 and len(tables[3]['rows']) == 4
for table in tables:
    assert all(len(row) == len(table['headers']) for row in table['rows'])
    assert not any('|' in str(cell) for row in table['rows'] for cell in row)

intro = ('These tables summarize an exploratory country-level analysis planned after initial inspection of coverage and sequence counts; it was not preregistered. '
         'Reported ICS follows the questionnaire category without a formulation restriction. Yes denotes general availability at the ≥50% public-primary-care pharmacy threshold; No denotes failure to reach that threshold.')
provenance = 'The GBD 2023 release label is supported by the provider namespace, archived export citations and official location hierarchy. The original export citation lists 2024; the dataset publication year has not been independently confirmed. The GBD 2023 methods articles were published in 2025, which does not establish that the dataset date is incorrect. The original citation is preserved; the results tool is cited as undated with its access date. Numerical inputs were unchanged.'
markdown = ['# Statistical tables', '', intro, '']
for table in tables:
    markdown += [f"## {table['id']}. {table['title']}", '', '| ' + ' | '.join(table['headers']) + ' |',
                 '| ' + ' | '.join(['---'] * len(table['headers'])) + ' |']
    markdown += ['| ' + ' | '.join(row) + ' |' for row in table['rows']]
    markdown += ['', 'Notes: ' + ' '.join(table['notes']), '']
markdown += ['Data provenance: ' + provenance, '']
(REPORT / 'Statistical tables.md').write_text('\n'.join(markdown), encoding='utf-8')
artifact = {'schema_version': 1, 'title': 'Statistical tables', 'generated_utc': datetime.now(timezone.utc).isoformat(),
            'intro': intro, 'tables': tables, 'data_provenance': provenance, 'source_csv_sha256': SOURCES,
            'formatting': {'percent_digits': 2, 'country_percent_digits': 1, 'odds_ratio_digits': 2,
                           'p_significant_digits': 4},
            'no_new_statistical_analysis': True, 'no_joint_GBD_uncertainty_interval': True}
(REPORT / 'Statistical tables.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding='utf-8')
assert all(hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == value for name, value in SOURCES.items())
print(json.dumps({'tables': len(tables), 'rows': [len(t['rows']) for t in tables], 'source_csv_unchanged': True,
                  'markdown': str(REPORT / 'Statistical tables.md'), 'json': str(REPORT / 'Statistical tables.json')}, ensure_ascii=False))
