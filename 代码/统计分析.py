"""Exploratory country-level analysis; frozen plan is in 核验/探索性分析方案.md."""
from pathlib import Path
import hashlib
import itertools
import json
import math
import sys
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import scipy
from scipy.optimize import linprog
from scipy.stats import binomtest, norm
import statsmodels
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / '输入数据'
TABLES = ROOT / '表格'
AUDIT = ROOT / '核验'
for directory in (TABLES, AUDIT):
    directory.mkdir(exist_ok=True)
YEARS = [2017, 2019, 2021]
ALL_YEARS = [2013, 2015, 2017, 2019, 2021]
VALID = ['Yes', 'No']
TRAJECTORIES = [''.join(x) for x in itertools.product('NY', repeat=3)]
MEDICINES = {'ics': '吸入激素', 'bronch': '支气管扩张剂', 'combo': '复方吸入剂'}
ENV = {'EN.ATM.PM25.MC.M3': 'pm25', 'NY.GDP.PCAP.PP.KD': 'gdp',
       'SH.XPD.OOPC.CH.ZS': 'oop', 'SH.XPD.CHEX.PP.CD': 'health'}
TABLE_DESCRIPTIONS = {}


def save_table(name, frame, description):
    destination = TABLES / f'{name}.csv'
    temporary = TABLES / f'{name}.临时.csv'
    frame.to_csv(temporary, index=False, encoding='utf-8-sig')
    temporary.replace(destination)
    TABLE_DESCRIPTIONS[destination.name] = {'rows': len(frame), 'columns': list(frame.columns), 'description': description}


def sanitize(value):
    if isinstance(value, dict):
        return {str(k): sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize(x) for x in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def save_json(path, value):
    path.write_text(json.dumps(sanitize(value), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def read_data():
    w = pd.read_csv(INPUT / '呼吸国家轮次.csv').rename(columns={
        'Year': 'year', 'Country code': 'iso3', 'Country': 'country', 'WHO region code': 'region'})
    g = pd.read_csv(INPUT / '成人哮喘数据.csv').rename(columns={'ISO3': 'iso3', 'geography review': 'geo_review'})
    e = pd.read_csv(INPUT / '呼吸环境社会数据.csv').rename(columns={'Country code': 'iso3', 'Year': 'year', **ENV})
    p = pd.read_csv(INPUT / '成人哮喘人口.csv')
    assert not w.duplicated(['iso3', 'year']).any()
    assert not g.duplicated(['iso3', 'year', 'metric']).any()
    assert not e.duplicated(['iso3', 'year']).any()
    assert not p.duplicated(['iso3', 'year']).any()
    assert set(g['age']) == {'25+ years'} and set(g['measure']) == {'DALYs'}
    assert set(g['metric']) == {'Number', 'Rate per 100000'}
    assert set(g['cause']) == {'Asthma'}
    assert g.iso3.nunique() == 204 and w.iso3.nunique() == 194
    wide = g.pivot(index=['iso3', 'year'], columns='metric', values='value').rename(
        columns={'Number': 'daly', 'Rate per 100000': 'rate'}).reset_index()
    geo = g[['iso3', 'geo_review']].drop_duplicates()
    assert not geo.duplicated('iso3').any()
    wide = wide.merge(geo, on='iso3', validate='many_to_one').merge(
        p[['iso3', 'year', 'pop25']], on=['iso3', 'year'], validate='one_to_one')
    relative = np.abs((wide['daly'] / wide['pop25'] * 1e5 - wide['rate']) / wide['rate'])
    assert relative.max() < 1e-8
    pair_sets = {y: set(w.loc[(w.year == y) & w['吸入激素'].isin(VALID) & w['支气管扩张剂'].isin(VALID), 'iso3']) for y in ALL_YEARS}
    ics_sets = {y: set(w.loc[(w.year == y) & w['吸入激素'].isin(VALID), 'iso3']) for y in ALL_YEARS}
    balanced = set.intersection(*(pair_sets[y] for y in YEARS))
    five = set.intersection(*(pair_sets[y] for y in ALL_YEARS))
    ics_only = set.intersection(*(ics_sets[y] for y in YEARS))
    assert len(balanced) == 168 and len(five) == 141 and len(ics_only) == 170
    base = w.loc[w.year == 2021, ['iso3', 'country', 'region']].copy()
    for key, original in MEDICINES.items():
        use_years = YEARS if key == 'ics' else [2021]
        for year in use_years:
            piece = w.loc[w.year == year, ['iso3', original]].rename(columns={original: f'{key}{year}'})
            base = base.merge(piece, on='iso3', validate='one_to_one')
    base['balanced168'] = base.iso3.isin(balanced)
    base['trajectory'] = base.apply(lambda r: ''.join('Y' if r[f'ics{y}'] == 'Yes' else 'N' for y in YEARS)
                                    if all(r[f'ics{y}'] in VALID for y in YEARS) else 'Unknown', axis=1)
    base = base.merge(wide.loc[wide.year == 2021, ['iso3', 'daly', 'rate', 'pop25', 'geo_review']].rename(
        columns={'daly': 'daly2021', 'rate': 'rate2021', 'pop25': 'pop2021'}), on='iso3', how='left', validate='one_to_one')
    base = base.merge(e.loc[e.year == 2021, ['iso3', *ENV.values()]], on='iso3', how='left', validate='one_to_one')
    columns = ['iso3', 'country', 'region', 'balanced168', 'ics2017', 'ics2019', 'ics2021',
               'bronch2021', 'combo2021', 'trajectory', 'daly2021', 'rate2021', 'pm25', 'gdp', 'oop', 'health', 'geo_review', 'pop2021']
    base = base[columns].sort_values('iso3').reset_index(drop=True)
    assert len(base) == 194 and base.daly2021.notna().all() and base.pop2021.notna().all()
    triple = set(base.loc[base.ics2021.isin(VALID) & base.bronch2021.isin(VALID) & base.combo2021.isin(VALID), 'iso3'])
    geo_clean = set(base.loc[base.balanced168 & (base.geo_review != 'review_required'), 'iso3'])
    assert len(triple) == 157 and len(geo_clean) == 149
    assert sum(base.balanced168 & base.combo2021.isin(VALID)) == 144
    assert base.loc[base.balanced168, 'trajectory'].value_counts().to_dict() == {
        'YYY': 99, 'NNN': 35, 'NNY': 11, 'NYY': 10, 'YNY': 5, 'YYN': 4, 'NYN': 2, 'YNN': 2}
    save_table('国家分析表', base, 'One row per WHO country/territory in 2021; 25+ DALY rate is crude per 100000; original unknown medicine answers retained; population is residents, not treated patients.')
    cohorts = {'balanced168': balanced, 'fivewave141': five, 'icsonly170': ics_only,
               'geoclean149': geo_clean, 'cross2021': pair_sets[2021], 'triple2021': triple}
    return w, wide, e, p, base, cohorts, pair_sets, float(relative.max())


def percentage(numerator, denominator):
    return 100 * numerator / denominator if denominator else np.nan


def quantiles(values):
    values = pd.Series(values).dropna()
    if values.empty:
        return {'n': 0, 'mean': np.nan, 'median': np.nan, 'q25': np.nan, 'q75': np.nan, 'min': np.nan, 'max': np.nan}
    return {'n': len(values), 'mean': values.mean(), 'median': values.median(),
            'q25': values.quantile(.25), 'q75': values.quantile(.75), 'min': values.min(), 'max': values.max()}


def medicine_counts(w, cohorts, pair_sets):
    records = []
    for year in ALL_YEARS:
        wave = w.loc[w.year == year]
        selections = {'all_available_single_item': set(wave.iso3), 'all_available_paired_items': pair_sets[year],
                      'fixed168': cohorts['balanced168'], 'fixed141_five_waves': cohorts['fivewave141']}
        for sample, countries in selections.items():
            chosen = wave.loc[wave.iso3.isin(countries)]
            for medicine, original in MEDICINES.items():
                if medicine == 'combo' and year != 2021:
                    continue
                n_yes = int(chosen[original].eq('Yes').sum())
                n_no = int(chosen[original].eq('No').sum())
                records.append({'sample': sample, 'year': year, 'medicine': medicine, 'eligible_n': len(chosen),
                                'valid_n': n_yes + n_no, 'yes_n': n_yes, 'no_n': n_no,
                                'unknown_n': len(chosen) - n_yes - n_no,
                                'yes_percent_valid': percentage(n_yes, n_yes + n_no),
                                'yes_percent_eligible': percentage(n_yes, len(chosen))})
    result = pd.DataFrame(records)
    save_table('药物逐轮计数', result, 'All-available single-item and paired-item denominators versus fixed168 and five-wave141; unknowns excluded from valid denominator only.')
    raw = w.groupby(['year', 'WHO region', '吸入激素', '支气管扩张剂'], dropna=False).size().rename('n').reset_index()
    save_table('逐轮原始答复', raw, 'Raw response categories by wave and WHO region; preserves missing-response labels.')
    return result


def holm(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty(len(values))
    adjusted[order] = np.minimum(1, np.maximum.accumulate(values[order] * (len(values) - np.arange(len(values)))))
    return adjusted


def paired_comparisons(w, countries, sample, medicines=('ics', 'bronch')):
    """Two distinct Holm families: 3 year comparisons for ICS, 3 for bronchodilator.

    Family membership is fixed independently of significance. We do not combine
    the medicines into a six-test family or select a comparison after seeing p.
    Country counts and percentage-point changes remain the primary summaries.
    """
    rows = []
    for medicine in medicines:
        frame = w.loc[w.iso3.isin(countries) & w.year.isin(YEARS)].pivot(index='iso3', columns='year', values=MEDICINES[medicine])
        first = len(rows)
        for before, after in [(2017, 2019), (2019, 2021), (2017, 2021)]:
            paired = frame.loc[frame[before].isin(VALID) & frame[after].isin(VALID)]
            yy = int(((paired[before] == 'Yes') & (paired[after] == 'Yes')).sum())
            yn = int(((paired[before] == 'Yes') & (paired[after] == 'No')).sum())
            ny = int(((paired[before] == 'No') & (paired[after] == 'Yes')).sum())
            nn = int(((paired[before] == 'No') & (paired[after] == 'No')).sum())
            discordant = yn + ny
            p = binomtest(ny, discordant, p=.5, alternative='two-sided').pvalue if discordant else 1.0
            rows.append({'sample': sample, 'medicine': medicine, 'before': before, 'after': after, 'paired_n': len(paired),
                         'yes_yes': yy, 'yes_no': yn, 'no_yes': ny, 'no_no': nn,
                         'before_yes_n': yy + yn, 'after_yes_n': yy + ny,
                         'change_percentage_points': percentage(ny - yn, len(paired)),
                         'discordant_n': discordant, 'p_exact_mcnemar': p})
        adjusted = holm([r['p_exact_mcnemar'] for r in rows[first:]])
        for row, adjusted_p in zip(rows[first:], adjusted):
            row['p_holm_within_medicine_three_comparisons'] = adjusted_p
    return pd.DataFrame(rows)


def linked_data(w, g, e, p, cohorts):
    chosen = w.loc[w.year.isin(YEARS), ['iso3', 'country', 'region', 'year', *MEDICINES.values()]].copy()
    chosen = chosen.rename(columns={v: k for k, v in MEDICINES.items()})
    chosen['balanced168'] = chosen.iso3.isin(cohorts['balanced168'])
    chosen = chosen.merge(g, on=['iso3', 'year'], how='left', validate='one_to_one')
    chosen = chosen.merge(e[['iso3', 'year', *ENV.values()]], on=['iso3', 'year'], how='left', validate='one_to_one')
    assert len(chosen) == 194 * 3 and chosen['daly'].notna().all()
    save_table('三轮国家联合表', chosen, '194 WHO countries/territories at each of 2017/2019/2021; exact-year linked 25+ DALYs, crude rate, population and environmental/social indicators.')
    return chosen


def burden_summary(base, g, countries, sample):
    chosen = base.loc[base.iso3.isin(countries)]
    global2021 = g.loc[g.year == 2021]
    global_daly = global2021.daly.sum()
    global_pop = global2021.pop25.sum()
    sample_daly, sample_pop = chosen.daly2021.sum(), chosen.pop2021.sum()
    rows = []
    for trajectory in TRAJECTORIES:
        subset = chosen.loc[chosen.trajectory == trajectory]
        stats = quantiles(subset.rate2021)
        rows.append({'sample': sample, 'trajectory': trajectory, 'country_n': len(subset),
                     'country_percent': percentage(len(subset), len(chosen)), 'daly2021': subset.daly2021.sum(),
                     'daly_percent_sample': percentage(subset.daly2021.sum(), sample_daly),
                     'daly_percent_global204': percentage(subset.daly2021.sum(), global_daly),
                     'pop25_2021': subset.pop2021.sum(), 'resident_population_percent_sample': percentage(subset.pop2021.sum(), sample_pop),
                     'resident_population_percent_global204': percentage(subset.pop2021.sum(), global_pop),
                     'country_crude_rate_median': stats['median'], 'country_crude_rate_q25': stats['q25'],
                     'country_crude_rate_q75': stats['q75'],
                     'pooled_crude_rate_per100000': subset.daly2021.sum() / subset.pop2021.sum() * 1e5 if subset.pop2021.sum() else np.nan,
                     'global204_daly_denominator': global_daly, 'sample_daly_denominator': sample_daly,
                     'global204_pop25_denominator': global_pop, 'sample_pop25_denominator': sample_pop})
    return pd.DataFrame(rows)


def trajectory_tables(base, g, cohorts):
    result = burden_summary(base, g, cohorts['balanced168'], 'balanced168')
    save_table('ICS轨迹负担与人口', result, 'Eight ICS trajectories; point-estimate DALY totals and resident population shares within fixed168 and global204; no summed GBD uncertainty intervals.')
    chosen = base.loc[base.balanced168].copy()
    records = []
    for region in sorted(base.region.unique()):
        subset = chosen.loc[chosen.region == region]
        for trajectory in TRAJECTORIES:
            group = subset.loc[subset.trajectory == trajectory]
            records.append({'region': region, 'trajectory': trajectory, 'country_n': len(group),
                            'region_n': len(subset), 'percent_within_region': percentage(len(group), len(subset)),
                            'daly2021': group.daly2021.sum(), 'pop25_2021': group.pop2021.sum()})
    save_table('ICS轨迹地区分布', pd.DataFrame(records), 'All eight trajectories crossed with six WHO regions; denominator is fixed168 within region.')
    chosen['combo_group'] = chosen.combo2021.where(chosen.combo2021.isin(VALID), 'Unknown')
    records = []
    for trajectory in TRAJECTORIES:
        subset = chosen.loc[chosen.trajectory == trajectory]
        for combo in ['Yes', 'No', 'Unknown']:
            group = subset.loc[subset.combo_group == combo]
            records.append({'trajectory': trajectory, 'combo2021': combo, 'country_n': len(group),
                            'trajectory_n': len(subset), 'percent_within_trajectory': percentage(len(group), len(subset)),
                            'daly2021': group.daly2021.sum(), 'pop25_2021': group.pop2021.sum(),
                            'raw_unknown_answers': '; '.join(sorted(group.combo2021.unique())) if combo == 'Unknown' else ''})
    save_table('ICS轨迹与复方交叉', pd.DataFrame(records), 'Fixed168 denominator; 144 with valid 2021 combo responses; Unknown retained as a third category.')
    records = []
    for bronch, ics, combo in itertools.product(VALID, repeat=3):
        group = base.loc[(base.bronch2021 == bronch) & (base.ics2021 == ics) & (base.combo2021 == combo)]
        records.append({'bronch2021': bronch, 'ics2021': ics, 'combo2021': combo, 'country_n': len(group),
                        'denominator': len(cohorts['triple2021']), 'percent': percentage(len(group), len(cohorts['triple2021'])),
                        'iso3': ';'.join(sorted(group.iso3)), 'daly2021': group.daly2021.sum(), 'pop25_2021': group.pop2021.sum()})
    save_table('2021三药状态', pd.DataFrame(records), 'Eight exact Yes/No combinations within 157 triple-valid countries; this is supply reporting, not patient treatment.')
    return result


def coverage_table(w, g, cohorts, pair_sets):
    rows = []
    for year in YEARS:
        global_year = g.loc[g.year == year]
        samples = {'global204': set(global_year.iso3), 'WHO194': set(w.iso3),
                   'wave_pair_valid': pair_sets[year], **cohorts}
        for name, countries in samples.items():
            subset = global_year.loc[global_year.iso3.isin(countries)]
            rows.append({'sample': name, 'year': year, 'country_n': len(subset),
                         'daly_total': subset.daly.sum(), 'global204_daly': global_year.daly.sum(),
                         'daly_percent_global204': percentage(subset.daly.sum(), global_year.daly.sum()),
                         'pop25_total': subset.pop25.sum(), 'global204_pop25': global_year.pop25.sum(),
                         'resident_population_percent_global204': percentage(subset.pop25.sum(), global_year.pop25.sum())})
    result = pd.DataFrame(rows)
    save_table('样本全球覆盖', result, 'Disease-burden and resident population coverage against all 204 input GBD countries/territories at each year; no national flags interpreted as patient access.')
    return result


def environment_descriptions(base, cohorts):
    rows = []
    for sample, countries in [('cross2021', cohorts['cross2021']), ('balanced168', cohorts['balanced168']), ('triple2021', cohorts['triple2021'])]:
        subset = base.loc[base.iso3.isin(countries)]
        for grouping in ['all', 'ics2021', 'combo2021', 'trajectory', 'region']:
            groups = [('All', subset)] if grouping == 'all' else subset.groupby(grouping, dropna=False)
            for group, frame in groups:
                for variable in ENV.values():
                    summary = quantiles(frame[variable])
                    rows.append({'sample': sample, 'grouping': grouping, 'group': group, 'variable': variable,
                                 'eligible_n': len(frame), 'missing_n': int(frame[variable].isna().sum()), **summary})
    save_table('2021环境社会分布', pd.DataFrame(rows), 'Country-unweighted mean, median, IQR and range; exact 2021 values; no p-value screening.')


def missing_bounds(w, base, g):
    rows = []
    for year in ALL_YEARS:
        chosen = w.loc[w.year == year]
        for medicine, original in MEDICINES.items():
            if medicine == 'combo' and year != 2021:
                continue
            yes = int(chosen[original].eq('Yes').sum())
            no = int(chosen[original].eq('No').sum())
            unknown = len(chosen) - yes - no
            rows.append({'bound_type': 'wave_general_availability', 'year': year, 'medicine_or_trajectory': medicine,
                         'denominator': len(chosen), 'observed_yes_n': yes, 'observed_no_n': no, 'unknown_n': unknown,
                         'lower_country_n': yes, 'upper_country_n': yes + unknown,
                         'lower_percent': percentage(yes, len(chosen)), 'upper_percent': percentage(yes + unknown, len(chosen))})
    for trajectory in TRAJECTORIES:
        target = ['Yes' if x == 'Y' else 'No' for x in trajectory]
        observed = np.ones(len(base), dtype=bool)
        compatible = np.ones(len(base), dtype=bool)
        for year, answer in zip(YEARS, target):
            current = base[f'ics{year}']
            observed &= current.eq(answer)
            compatible &= current.eq(answer) | ~current.isin(VALID)
        rows.append({'bound_type': 'trajectory_extreme_compatibility', 'year': 2021, 'medicine_or_trajectory': trajectory,
                     'denominator': len(base), 'lower_country_n': int(observed.sum()), 'upper_country_n': int(compatible.sum()),
                     'lower_percent': percentage(observed.sum(), len(base)), 'upper_percent': percentage(compatible.sum(), len(base)),
                     'lower_daly2021': base.loc[observed, 'daly2021'].sum(),
                     'upper_daly2021': base.loc[compatible, 'daly2021'].sum(),
                     'lower_pop25_2021': base.loc[observed, 'pop2021'].sum(),
                     'upper_pop25_2021': base.loc[compatible, 'pop2021'].sum()})
    for trajectory in ['All', *TRAJECTORIES]:
        chosen = base.loc[base.balanced168 & ((base.trajectory == trajectory) if trajectory != 'All' else True)]
        yes = int(chosen.combo2021.eq('Yes').sum())
        no = int(chosen.combo2021.eq('No').sum())
        unknown = len(chosen) - yes - no
        rows.append({'bound_type': 'combo_unknown_all_no_or_yes', 'year': 2021, 'medicine_or_trajectory': trajectory,
                     'denominator': len(chosen), 'observed_yes_n': yes, 'observed_no_n': no, 'unknown_n': unknown,
                     'lower_country_n': yes, 'upper_country_n': yes + unknown,
                     'lower_percent': percentage(yes, len(chosen)), 'upper_percent': percentage(yes + unknown, len(chosen))})
    result = pd.DataFrame(rows)
    save_table('缺失极端边界', result, 'Worst/best assignments are mathematical bounds, not imputations or confidence intervals; trajectory upper bounds are marginal and cannot be simultaneously summed.')
    return result


def separation_check(X, y):
    signed = np.asarray(X) * (2 * np.asarray(y) - 1)[:, None]
    check = linprog(-signed.sum(axis=0), A_ub=-signed, b_ub=np.zeros(len(y)),
                    bounds=[(-1, 1)] * signed.shape[1], method='highs')
    if not check.success:
        return True, f'separation check failed: {check.message}'
    gain = float(-check.fun)
    return gain > 1e-6, f'bounded separation LP objective={gain:.10g}'


def fit_model(base, countries, outcome, economic, model_id, family, restriction=None):
    eligible = base.loc[base.iso3.isin(countries)].copy()
    if restriction is not None:
        eligible = eligible.loc[restriction(eligible)].copy()
    predictors = [economic, 'pm25', 'oop']
    valid = eligible[outcome].isin(VALID) & eligible[predictors].notna().all(axis=1) & eligible[economic].gt(0)
    used = eligible.loc[valid].copy()
    missing = eligible.loc[~valid]
    role = ('primary_explanatory' if economic == 'gdp' else 'health_expenditure_replacement_sensitivity') if family == 'four_prespecified' else 'sensitivity_refit'
    info = {'model_id': model_id, 'family': family, 'model_role': role, 'outcome': outcome, 'event_definition': 'No=1',
            'economic_predictor': economic, 'eligible_n': len(eligible), 'complete_n': len(used),
            'events_no': int(used[outcome].eq('No').sum()), 'nonevents_yes': int(used[outcome].eq('Yes').sum()),
            'excluded_missing_n': len(missing), 'excluded_missing_iso3': ';'.join(sorted(missing.iso3)),
            'included_iso3': ';'.join(sorted(used.iso3)), 'covariance': 'HC1 independent-country sandwich, n/(n-p)',
            'status': 'not_fitted', 'stop_reason': '', 'separation_check': '', 'converged': False}
    missing_rows = []
    for _, row in missing.iterrows():
        reasons = [x for x in predictors if pd.isna(row[x]) or (x == economic and row[x] <= 0)]
        if row[outcome] not in VALID:
            reasons.append(outcome)
        missing_rows.append({'model_id': model_id, 'iso3': row.iso3, 'missing_or_invalid': ';'.join(reasons)})
    if min(info['events_no'], info['nonevents_yes']) < 30:
        info['stop_reason'] = 'fewer than 30 events or 30 nonevents for three prespecified slopes'
        return info, [], missing_rows
    X = np.column_stack([np.ones(len(used)), np.log2(used[economic]), used.pm25 / 10, used.oop / 10])
    y = used[outcome].eq('No').astype(float).to_numpy()
    if np.linalg.matrix_rank(X) < X.shape[1]:
        info['stop_reason'] = 'rank-deficient design'
        return info, [], missing_rows
    separated, separation_note = separation_check(X, y)
    info['separation_check'] = separation_note
    if separated:
        info['stop_reason'] = 'complete/quasi separation or unsuccessful separation diagnostic'
        return info, [], missing_rows
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            fit = sm.GLM(y, X, family=sm.families.Binomial()).fit(maxiter=200, tol=1e-10)
        info['warnings'] = '; '.join(str(x.message) for x in caught)
        if not fit.converged or any('separation' in str(x.message).lower() for x in caught):
            info['stop_reason'] = 'nonconvergence or separation warning'
            return info, [], missing_rows
        probability = fit.predict(X)
        weights = probability * (1 - probability)
        information = X.T @ (weights[:, None] * X)
        inverse = np.linalg.inv(information)
        score = X * (y - probability)[:, None]
        covariance = inverse @ (score.T @ score) @ inverse * len(y) / (len(y) - X.shape[1])
        se = np.sqrt(np.diag(covariance))
        if not np.isfinite(covariance).all() or not np.all(np.diag(covariance) > 0):
            info['stop_reason'] = 'nonfinite or nonpositive robust covariance'
            return info, [], missing_rows
        info.update(status='fitted', converged=True, iterations=fit.fit_history.get('iteration'),
                    log_likelihood=fit.llf, design_condition_number=np.linalg.cond(X),
                    information_condition_number=np.linalg.cond(information),
                    fitted_probability_min=probability.min(), fitted_probability_max=probability.max(),
                    robust_covariance_min_eigenvalue=np.linalg.eigvalsh(covariance).min())
        output = []
        for index, (variable, unit) in enumerate([(economic, 'per doubling (log2)'), ('pm25', 'per 10 micrograms/m3'), ('oop', 'per 10 percentage points')], start=1):
            coefficient = float(fit.params[index])
            lower = coefficient - norm.ppf(.975) * se[index]
            upper = coefficient + norm.ppf(.975) * se[index]
            output.append({'model_id': model_id, 'family': family, 'model_role': role, 'outcome': outcome, 'variable': variable, 'unit': unit,
                           'eligible_n': len(eligible), 'complete_n': len(used), 'events_no': info['events_no'],
                           'nonevents_yes': info['nonevents_yes'], 'log_odds_coefficient': coefficient,
                           'robust_se': se[index], 'odds_ratio': np.exp(coefficient), 'ci95_lower': np.exp(lower),
                           'ci95_upper': np.exp(upper), 'p_wald_exploratory': 2 * norm.sf(abs(coefficient / se[index])),
                           'covariance': info['covariance']})
        return info, output, missing_rows
    except (ValueError, np.linalg.LinAlgError, OverflowError) as error:
        info['stop_reason'] = f'{type(error).__name__}: {error}'
        return info, [], missing_rows


def model_tables(base, cohorts):
    """GDP specification is primary; health replaces it only as frozen sensitivity.

    No outcome p-value, including PM2.5's p-value, changes the predictor set,
    transformations, inclusion criteria, stopping rules, or reported models.
    """
    diagnostics, coefficients, missing_rows = [], [], []
    specs = []
    for outcome, cohort in [('ics2021', 'cross2021'), ('combo2021', 'triple2021')]:
        for economic in ['gdp', 'health']:
            specs.append((cohorts[cohort], outcome, economic, f'{outcome}_{economic}', 'four_prespecified', None))
        common = set(base.loc[base.iso3.isin(cohorts[cohort]) & base[['gdp', 'health', 'pm25', 'oop']].notna().all(axis=1)
                             & base.gdp.gt(0) & base.health.gt(0), 'iso3'])
        for economic in ['gdp', 'health']:
            specs.append((common, outcome, economic, f'{outcome}_{economic}_same_sample', 'economic_same_sample', None))
        for region in sorted(base.region.unique()):
            specs.append((cohorts[cohort], outcome, 'gdp', f'{outcome}_without_{region}', 'leave_one_region_out',
                          lambda frame, r=region: frame.region != r))
        specs.append((cohorts[cohort], outcome, 'gdp', f'{outcome}_geo_clean', 'exclude_map_review',
                      lambda frame: frame.geo_review != 'review_required'))
        for sensitivity in ['balanced168', 'fivewave141', 'icsonly170']:
            specs.append((cohorts[cohort] & cohorts[sensitivity], outcome, 'gdp', f'{outcome}_{sensitivity}', 'cohort_sensitivity', None))
    for countries, outcome, economic, name, family, restriction in specs:
        info, estimates, missing = fit_model(base, countries, outcome, economic, name, family, restriction)
        diagnostics.append(info)
        coefficients.extend(estimates)
        missing_rows.extend(missing)
    diagnostics = pd.DataFrame(diagnostics)
    coefficients = pd.DataFrame(coefficients)
    save_table('模型诊断与分母', diagnostics, 'All four prespecified fits plus explicitly labelled sensitivity refits; stopping rules and exact included/excluded country lists retained.')
    save_table('四项预设模型', coefficients.loc[coefficients.family == 'four_prespecified'], 'Two outcomes x GDP or health expenditure replacement; HC1 robust OR and Wald CI; no p-value selection, no causal interpretation.')
    save_table('模型敏感性结果', coefficients.loc[coefficients.family != 'four_prespecified'], 'Prespecified sensitivity refits, not independent discovery tests; small-event or separated models may be stopped.')
    save_table('模型缺失国家', pd.DataFrame(missing_rows), 'Country-specific incomplete-case reasons, one row per model-country exclusion.')
    return diagnostics, coefficients


def sensitivity_tables(w, base, g, cohorts):
    selections = {name: cohorts[name] for name in ['balanced168', 'fivewave141', 'icsonly170', 'geoclean149']}
    for region in sorted(base.region.unique()):
        selections[f'without_{region}'] = cohorts['balanced168'] - set(base.loc[base.region == region, 'iso3'])
    count_rows, burden_frames, paired_frames = [], [], []
    for name, countries in selections.items():
        chosen = base.loc[base.iso3.isin(countries)]
        burden_frames.append(burden_summary(base, g, countries, name))
        paired_frames.append(paired_comparisons(w, countries, name, ('ics',) if name == 'icsonly170' else ('ics', 'bronch')))
        for year in YEARS:
            wave = w.loc[(w.year == year) & w.iso3.isin(countries)]
            for medicine, original in MEDICINES.items():
                if medicine == 'combo' and year != 2021:
                    continue
                yes = int(wave[original].eq('Yes').sum())
                no = int(wave[original].eq('No').sum())
                count_rows.append({'sample': name, 'year': year, 'medicine': medicine, 'eligible_n': len(wave),
                                   'yes_n': yes, 'no_n': no, 'unknown_n': len(wave) - yes - no,
                                   'yes_percent_valid': percentage(yes, yes + no)})
    save_table('敏感性药物计数', pd.DataFrame(count_rows), 'Fixed five-wave141, ICS-only170, spatial-review-excluded149 and leave-one-region-out descriptions.')
    save_table('敏感性轨迹负担', pd.concat(burden_frames, ignore_index=True), 'Trajectory DALY/resident-population shares and country rate summaries re-estimated within each sensitivity cohort.')
    save_table('敏感性配对变化', pd.concat(paired_frames, ignore_index=True), 'Paired exact McNemar and per-medicine Holm in sensitivity cohorts; descriptive robustness, not p-value screening.')


def main():
    started = datetime.now(timezone.utc).isoformat()
    w, g, e, p, base, cohorts, pair_sets, population_error = read_data()
    counts = medicine_counts(w, cohorts, pair_sets)
    paired = paired_comparisons(w, cohorts['balanced168'], 'balanced168')
    save_table('配对药物变化', paired, 'Fixed168 paired 2017/2019/2021 exact McNemar, three comparisons per medicine Holm adjusted; percentage-point differences primary.')
    linked_data(w, g, e, p, cohorts)
    burden = trajectory_tables(base, g, cohorts)
    coverage = coverage_table(w, g, cohorts, pair_sets)
    environment_descriptions(base, cohorts)
    missing_bounds(w, base, g)
    sensitivity_tables(w, base, g, cohorts)
    diagnostics, coefficients = model_tables(base, cohorts)
    global2021 = g.loc[g.year == 2021]
    primary = base.loc[base.balanced168]
    main_counts = counts.loc[(counts['sample'] == 'fixed168') & counts.year.isin(YEARS)]
    summary = {
        'analysis_type': 'Exploratory analysis frozen after viewing coverage and trajectory counts; not preregistered.',
        'analysis_date_utc': started, 'age': '25+ years', 'rate_type': 'Crude DALY rate per 100000 people aged 25+; not age-standardised.',
        'cohorts': {name: len(countries) for name, countries in cohorts.items()},
        'all_available_pair_valid': {str(y): len(pair_sets[y]) for y in ALL_YEARS},
        'WHO_countries': 194, 'GBD_countries_territories': 204,
        'balanced_trajectory_counts': primary.trajectory.value_counts().sort_index().to_dict(),
        'balanced_combo_counts': {'Yes': int(primary.combo2021.eq('Yes').sum()), 'No': int(primary.combo2021.eq('No').sum()),
                                  'Unknown': int((~primary.combo2021.isin(VALID)).sum())},
        'ICS_No_combo_Yes_global2021': base.loc[base.ics2021.eq('No') & base.combo2021.eq('Yes'), ['iso3', 'country']].to_dict('records'),
        'global204_daly2021': global2021.daly.sum(), 'global204_pop25_2021': global2021.pop25.sum(),
        'balanced168_daly2021': primary.daly2021.sum(), 'balanced168_pop25_2021': primary.pop2021.sum(),
        'fixed168_counts': main_counts.to_dict('records'), 'paired_results': paired.to_dict('records'),
        'trajectory_burden': burden.to_dict('records'),
        'core_model_diagnostics': diagnostics.loc[diagnostics.family == 'four_prespecified'].to_dict('records'),
        'core_model_results': coefficients.loc[coefficients.family == 'four_prespecified'].to_dict('records'),
        'model_stops': diagnostics.loc[diagnostics.status != 'fitted', ['model_id', 'complete_n', 'events_no', 'nonevents_yes', 'stop_reason']].to_dict('records'),
        'table_descriptions': TABLE_DESCRIPTIONS,
        'interpretation_limits': [
            'Country availability threshold is not patient access, affordability, use or treatment quality.',
            'No general-availability response does not mean complete absence of the medicine.',
            'Reported ICS availability trajectories do not establish absence of all anti-inflammatory therapy; the original questionnaire does not support a single-agent restriction.',
            'Population shares describe residents of countries reporting a status; not undertreated individual proportions.',
            'GBD joint uncertainty intervals were not generated by summing endpoints.',
            'Regression robust intervals do not include survey-report measurement error, GBD uncertainty or spatial dependence.',
            'Original map-review flags do not imply a failed country identity match.',
            'The GBD 2023 release label is supported by the provider namespace, archived export citations and official location hierarchy. The original export citation lists 2024; the dataset publication year has not been independently confirmed. The GBD 2023 methods articles were published in 2025, which does not establish that the dataset date is incorrect. The original citation is preserved; the results tool is cited as undated with its access date.',
        ],
    }
    save_json(TABLES / '核心结果.json', summary)
    input_files = ['呼吸国家轮次.csv', '成人哮喘数据.csv', '成人哮喘人口.csv', '呼吸环境社会数据.csv']
    hashes = {name: hashlib.sha256((INPUT / name).read_bytes()).hexdigest() for name in input_files}
    audit = {'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(), 'input_sha256': hashes,
             'software': {'python': sys.version, 'numpy': np.__version__, 'pandas': pd.__version__,
                          'scipy': scipy.__version__, 'statsmodels': statsmodels.__version__},
             'assertions_passed': ['unique input keys', '194 WHO entities', '204 GBD entities', '25+ age only',
                                   '168 balanced', '141 five-wave', '170 ICS-only', '149 geo-exclusion', '181 cross-section',
                                   '157 triple-valid', '144 combo valid within168', 'eight trajectory counts',
                                   'complete DALY and population match', 'DALY number-rate-population consistency'],
             'max_daly_rate_population_relative_error': population_error,
             'all_tables': TABLE_DESCRIPTIONS, 'fitted_model_n': int(diagnostics.status.eq('fitted').sum()),
             'stopped_model_n': int(diagnostics.status.ne('fitted').sum()),
             'no_joint_GBD_UI': True, 'no_environment_imputation': True, 'no_causal_claim': True}
    save_json(AUDIT / '统计执行核验.json', audit)
    print(json.dumps(sanitize({'country_table_rows': len(base), 'tables': len(TABLE_DESCRIPTIONS),
                              'core_models': summary['core_model_diagnostics'], 'paired': summary['paired_results']}), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
