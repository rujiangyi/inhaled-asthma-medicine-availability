"""Independent numerical checks of saved tables using alternate statistics APIs."""
from pathlib import Path
import importlib.util
import json
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd

import statsmodels.api as sm
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / '表格'
country = pd.read_csv(T / '国家分析表.csv')
paired = pd.read_csv(T / '配对药物变化.csv')
estimates = pd.read_csv(T / '四项预设模型.csv')
diagnostics = pd.read_csv(T / '模型诊断与分母.csv')
checks = {}
assert len(country) == 194 and country.iso3.is_unique
assert country.balanced168.sum() == 168
assert len(country.columns) == 18
checks['country_table_unique_194_and_18_fields'] = True
max_p_error = 0.0
for medicine, group in paired.groupby('medicine'):
    pvalues = []
    for _, row in group.iterrows():
        p = mcnemar([[row.yes_yes, row.yes_no], [row.no_yes, row.no_no]], exact=True).pvalue
        pvalues.append(p)
        max_p_error = max(max_p_error, abs(p - row.p_exact_mcnemar))
        assert row.yes_yes + row.yes_no + row.no_yes + row.no_no == row.paired_n
        assert abs(100 * (row.no_yes - row.yes_no) / row.paired_n - row.change_percentage_points) < 1e-12
    adjusted = multipletests(pvalues, method='holm')[1]
    assert np.allclose(adjusted, group.p_holm_within_medicine_three_comparisons, rtol=0, atol=1e-12)
assert max_p_error < 1e-12
checks['mcnemar_alternate_API_max_absolute_error'] = max_p_error
checks['holm_statsmodels_agreement'] = True

model_checks = []
for _, metadata in diagnostics.loc[diagnostics.family == 'four_prespecified'].iterrows():
    countries = metadata.included_iso3.split(';')
    d = country.loc[country.iso3.isin(countries)].copy()
    economic = metadata.economic_predictor
    y = d[metadata.outcome].eq('No').astype(float)
    X = sm.add_constant(pd.DataFrame({'economic': np.log2(d[economic]), 'pm25': d.pm25 / 10, 'oop': d.oop / 10}))
    # Different likelihood-fitting implementation; HC0 scaled by the explicit HC1 correction.
    model = sm.Logit(y, X).fit(disp=False, cov_type='HC0', maxiter=200, tol=1e-12)
    expected_se = np.asarray(model.bse) * np.sqrt(len(d) / (len(d) - X.shape[1]))
    saved = estimates.loc[estimates.model_id == metadata.model_id]
    errors = []
    for index, variable in enumerate([economic, 'pm25', 'oop'], start=1):
        row = saved.loc[saved.variable == variable].iloc[0]
        coefficient_error = abs(model.params.iloc[index] - row.log_odds_coefficient)
        se_error = abs(expected_se[index] - row.robust_se)
        assert coefficient_error < 1e-8 and se_error < 1e-8
        errors.append({'variable': variable, 'coefficient_error': coefficient_error, 'HC1_SE_error': se_error})
    model_checks.append({'model_id': metadata.model_id, 'n': len(d), 'events': int(y.sum()), 'differences': errors})
checks['four_models_independent_Logit_HC0_scaled_to_HC1'] = model_checks

trajectory = pd.read_csv(T / 'ICS轨迹负担与人口.csv')
assert trajectory.country_n.sum() == 168
assert np.isclose(trajectory.daly_percent_sample.sum(), 100)
assert np.isclose(trajectory.resident_population_percent_sample.sum(), 100)
assert np.isclose(trajectory.daly2021.sum(), country.loc[country.balanced168, 'daly2021'].sum())
assert np.isclose(trajectory.pop25_2021.sum(), country.loc[country.balanced168, 'pop2021'].sum())
combo = pd.read_csv(T / 'ICS轨迹与复方交叉.csv')
assert combo.country_n.sum() == 168
assert combo.loc[combo.combo2021 != 'Unknown', 'country_n'].sum() == 144
triple = pd.read_csv(T / '2021三药状态.csv')
assert triple.country_n.sum() == 157
checks['trajectory_burden_population_and_drug_denominators'] = True
bounds = pd.read_csv(T / '缺失极端边界.csv')
assert (bounds.lower_country_n <= bounds.upper_country_n).all()
assert (bounds.upper_country_n <= bounds.denominator).all()
checks['missing_bounds_ordered_within_denominator'] = True

spec = importlib.util.spec_from_file_location('analysis_for_audit', ROOT / '代码' / '统计分析.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
separation_cases = [
    ('complete', [[1, -2], [1, -1], [1, 1], [1, 2]], [0, 0, 1, 1], True),
    ('quasi', [[1, -1], [1, 0], [1, 0], [1, 1]], [0, 0, 1, 1], True),
    ('overlap', [[1, -1], [1, 0], [1, 1], [1, -1], [1, 0], [1, 1]], [0, 1, 0, 1, 0, 1], False),
]
for name, X, y, expected in separation_cases:
    observed, diagnostic = module.separation_check(np.asarray(X), np.asarray(y))
    assert observed == expected, (name, observed, diagnostic)
checks['complete_quasi_and_nonseparation_examples'] = True
result = {'verified_utc': datetime.now(timezone.utc).isoformat(), 'status': 'passed', 'checks': checks,
          'scope': 'Independent computation checks; does not validate source truth or causal assumptions.'}
(ROOT / '核验' / '统计独立复核.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': 'passed', 'mcnemar_max_error': max_p_error,
                  'max_model_coefficient_error': max(x['coefficient_error'] for m in model_checks for x in m['differences']),
                  'max_model_se_error': max(x['HC1_SE_error'] for m in model_checks for x in m['differences'])}, indent=2))
