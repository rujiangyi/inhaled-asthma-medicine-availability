"""Figures 3–4: national medicine answers, with preserved analysis denominators.

Figure contract: two asymmetric mixed-modality figures, rendered only in Python.
Figure 3 asks where the 2021 reported ICS gap occurs and how other medicine
answers co-occur. The world map is the primary spatial evidence; the aggregate
bars quantify the full frame; regional tiles retain every country, including
small islands. Each country contributes exactly one tile per medicine.
Figure 4 decomposes the 157 complete three-medicine records into real nested
branches, then bounds interpretation with the 168-country historical cross-tab
and all three observed ICS-No/combination-Yes countries. No network is inferred.
No observation is sampled; Unknown combines non-Yes/No survey answers only.
No uncertainty interval is estimated for these enumerated national records.
Exports: 11.2-inch figures, editable TNR PDF/SVG, 320-dpi PNG and preview,
complete source CSVs, and separate rendered text/collision audits.
"""

from itertools import product
from 绘图公共 import *
from matplotlib.patches import Wedge, Rectangle


STATES = ['Yes', 'No', 'Unknown']
SC = {'Yes': YES, 'No': NO, 'Unknown': UNKNOWN}
MEDICINES = [('bronch2021', 'Bronchodilator'),
             ('ics2021', 'ICS'), ('combo2021', 'Combination')]
FULL = DF.copy()
for field, _ in MEDICINES:
    FULL[field + 'state'] = FULL[field].map(state)
assert len(FULL) == 194 and FULL.iso3.is_unique
assert len(B) == 168


def quiet(ax):
    ax.set_axis_off()
    return ax


def heading(fig, bounds, letter, title):
    ax = fig.add_axes(bounds)
    quiet(ax)
    panel(ax, letter, title)
    return ax


def statuslegend(fig, outside=False):
    entries = [('Yes', YES), ('No', NO), ('Unknown / no response', UNKNOWN)]
    if outside:
        entries.append(('Outside WHO frame', PALE))
    return figlegend(fig, entries, y=.028, ncol=len(entries))


def save34(fig, name):
    # Preserve the requested physical canvas; tight cropping would shrink Fig. 4.
    fig.savefig(MAIN / f'{name}.pdf', dpi=320, bbox_inches=None)
    fig.savefig(MAIN / f'{name}.svg', dpi=320, bbox_inches=None)
    fig.savefig(MAIN / f'{name}.png', dpi=320, bbox_inches=None)
    fig.savefig(PREVIEW / f'{name}.png', dpi=120, bbox_inches=None)
    plt.close(fig)
    print(name, 'saved at 11.2 inches', flush=True)


def fig3():
    fig = plt.figure(figsize=(11.2, 7.9))
    ax = fig.add_axes([.037, .444, .732, .496])
    panel(ax, 'a', 'Reported ICS availability, 2021')
    world(ax, dict(zip(FULL.iso3, FULL.ics2021state)), SC)

    # National aggregates: identical 194-country denominator for all three bars.
    ax = fig.add_axes([.798, .495, .177, .442])
    panel(ax, 'b', 'National answers')
    counts = []
    for j, (field, label) in enumerate(MEDICINES):
        y = 3.48 - 1.23 * j
        ax.text(0, y + .29, label, ha='left', va='bottom', fontsize=10.5)
        left = 0
        for s in STATES:
            n = int(FULL[field + 'state'].eq(s).sum())
            ax.barh(y, n, left=left, height=.25, color=SC[s],
                    edgecolor='white', linewidth=.6)
            left += n
            counts.append({'medicine': field, 'state': s, 'countries': n,
                           'denominator': len(FULL), 'percent': n / len(FULL) * 100})
        for xpos, s in zip([29, 96, 164], STATES):
            n = int(FULL[field + 'state'].eq(s).sum())
            ax.text(xpos, y - .25, str(n), ha='center', va='top',
                    fontsize=11, color=SC[s] if s != 'Unknown' else '#62676F')
    ax.text(97, -.37, '194 country records', ha='center', fontsize=10)
    ax.set(xlim=(0, 194), ylim=(-.5, 4.28))
    quiet(ax)

    heading(fig, [.045, .409, .92, .006], 'c', 'Country-level medicine profiles by WHO region')
    # Equal cell width across all regions; alphabetical ISO order inside each
    # reported ICS, bronchodilator, combination pattern. No countries excluded.
    tiledata = []
    regional = []
    maxn = int(FULL.groupby('region').size().max())
    ordermap = {'No': 0, 'Yes': 1, 'Unknown': 2}
    positions = [(.112, .318), (.610, .318), (.112, .215),
                 (.610, .215), (.112, .112), (.610, .112)]
    for reg, (x, y) in zip(REGIONS, positions):
        d = FULL.loc[FULL.region.eq(reg)].copy()
        d['sortkey'] = d[['ics2021state', 'bronch2021state', 'combo2021state']].apply(
            lambda z: tuple(ordermap[q] for q in z), axis=1)
        d = d.sort_values(['sortkey', 'iso3']).reset_index(drop=True)
        ax = fig.add_axes([x, y, .361, .060])
        for j, row in d.iterrows():
            for i, (field, label) in enumerate(MEDICINES):
                s = row[field + 'state']
                ax.add_patch(Rectangle((j, i), .91, .83, facecolor=SC[s],
                                       edgecolor='none'))
                tiledata.append({'region': reg, 'region_name': RL[reg],
                                 'column': j + 1, 'iso3': row.iso3,
                                 'country': row.country, 'medicine': field,
                                 'raw_answer': row[field], 'display_state': s})
        ax.set(xlim=(0, maxn), ylim=(3, 0))
        for i, label in enumerate(['Bronch.', 'ICS', 'Combo']):
            ax.text(-1.35, i + .415, label, ha='right', va='center',
                    fontsize=9, clip_on=False)
        ax.text(0, -.43, f'{RL[reg]}  ·  {len(d)} countries',
                fontsize=10.3, ha='left', va='bottom', clip_on=False)
        quiet(ax)
        for field, label in MEDICINES:
            for s in STATES:
                n = int(d[field + 'state'].eq(s).sum())
                regional.append({'medicine': field, 'region': reg, 'state': s,
                                 'n': n, 'denominator': len(d),
                                 'percentage': n / len(d) * 100})
    fig.text(.973, .417, 'One column = one country', ha='right', va='bottom', fontsize=9.3)
    statuslegend(fig, outside=True)
    source('Figure 3 medicine geography', FULL[['iso3', 'country', 'region',
           'bronch2021', 'ics2021', 'combo2021', 'bronch2021state',
           'ics2021state', 'combo2021state']])
    source('Figure 3 national answers', pd.DataFrame(counts))
    source('Figure 3 country tiles', pd.DataFrame(tiledata))
    source('Figure 3 regional distributions', pd.DataFrame(regional))
    assert len(tiledata) == 194 * 3
    assert pd.DataFrame(counts).groupby('medicine').countries.sum().eq(194).all()
    save34(fig, 'Figure 3')


def nestedbranches(frame):
    """Angles are country counts / 157; child angles partition each parent."""
    records = []
    fields = [x[0] for x in MEDICINES]
    for depth in range(1, 4):
        consumed = 0
        for prefix in product(['Yes', 'No'], repeat=depth):
            mask = np.logical_and.reduce([frame[f].eq(v).to_numpy()
                                          for f, v in zip(fields, prefix)])
            n = int(mask.sum())
            start = 90 - consumed / len(frame) * 360
            end = start - n / len(frame) * 360
            records.append({'depth': depth, 'medicine': fields[depth - 1],
                            'branch': ' / '.join(prefix), 'state': prefix[-1],
                            'countries': n, 'denominator': len(frame),
                            'percent': n / len(frame) * 100,
                            'angle_start': start, 'angle_end': end})
            consumed += n
        assert consumed == len(frame)
    return pd.DataFrame(records)


def fig4():
    fig = plt.figure(figsize=(11.2, 8.0))
    fields = [x[0] for x in MEDICINES]
    full = FULL.loc[FULL[fields].isin(VALID).all(axis=1)].copy()
    assert len(full) == 157
    full['pattern'] = full[fields].replace({'Yes': 'Y', 'No': 'N'}).agg(''.join, axis=1)
    patternorder = ['YYY', 'YYN', 'YNY', 'YNN', 'NYY', 'NYN', 'NNY', 'NNN']
    counts = full.pattern.value_counts().reindex(patternorder, fill_value=0)
    assert counts.tolist() == [77, 32, 3, 13, 1, 0, 0, 31]
    branches = nestedbranches(full)

    ax = fig.add_axes([.051, .470, .398, .476])
    panel(ax, 'a', 'Three-medicine taxonomy')
    radii = {1: (.33, .57), 2: (.59, .83), 3: (.85, 1.09)}
    for row in branches.itertuples():
        if row.countries == 0:
            continue
        low, high = radii[row.depth]
        ax.add_patch(Wedge((0, 0), high, row.angle_end, row.angle_start,
                           width=high - low, facecolor=SC[row.state],
                           edgecolor='white', linewidth=1.05))
        # Tiny branches remain exact in the adjacent table; no overlapping labels.
        if row.countries >= (11 if row.depth < 3 else 10):
            angle = np.deg2rad((row.angle_start + row.angle_end) / 2)
            r = (low + high) / 2
            label = f'{row.state}\n{row.countries}' if row.depth < 3 else str(row.countries)
            ax.text(r * np.cos(angle), r * np.sin(angle), label,
                    ha='center', va='center', fontsize=9.6, color='white')
    ax.text(0, .02, '157', ha='center', va='center', fontsize=20)
    ax.text(0, -.14, 'countries', ha='center', va='center', fontsize=10)
    ax.set(xlim=(-1.15, 1.15), ylim=(-1.15, 1.15), aspect='equal')
    quiet(ax)
    fig.text(.251, .447, 'Inner → outer: bronchodilator → ICS → combination',
             ha='center', va='top', fontsize=9.5)

    ax = fig.add_axes([.518, .499, .445, .439])
    panel(ax, 'b', 'Exact answer combinations')
    xs = [.25, 1.35, 2.45]
    for x, label in zip(xs, ['Bronch.', 'ICS', 'Combo']):
        ax.text(x, 8.15, label, ha='center', va='bottom', fontsize=10)
    ax.text(4.65, 8.15, 'Countries', ha='center', va='bottom', fontsize=10)
    ax.text(6.57, 8.15, 'n', ha='center', va='bottom', fontsize=10)
    ax.text(7.43, 8.15, '%', ha='center', va='bottom', fontsize=10)
    ax.hlines(7.91, -.17, 7.8, color='#C5C8CC', linewidth=.7)
    patterns = []
    for j, (p, n) in enumerate(counts.items()):
        y = 7.32 - j
        if p == 'YNY':
            ax.add_patch(Rectangle((-.18, y - .40), 8.01, .80,
                                   facecolor='#F7F0E5', edgecolor='none', zorder=0))
        for x, letter in zip(xs, p):
            s = 'Yes' if letter == 'Y' else 'No'
            ax.scatter([x], [y], s=225, color=SC[s], edgecolor='none', zorder=2)
            ax.text(x, y, letter, ha='center', va='center', color='white', fontsize=8.7)
        ax.barh(y, n / 80 * 2.6, left=3.24, height=.44,
                color=YES if p[-1] == 'Y' else NO)
        ax.text(6.57, y, str(int(n)), ha='center', va='center', fontsize=11)
        ax.text(7.43, y, f'{n / len(full) * 100:.1f}', ha='center', va='center', fontsize=10)
        patterns.append({'pattern': p, 'bronchodilator': p[0], 'ICS': p[1],
                         'combination': p[2], 'countries': int(n),
                         'denominator': len(full), 'percent': n / len(full) * 100})
    ax.set(xlim=(-.18, 7.83), ylim=(-.34, 8.57))
    quiet(ax)

    heading(fig, [.066, .386, .42, .008], 'c', 'Historical ICS sequence × combination')
    hist = B.assign(combo=B.combo2021.map(state))
    tab = pd.crosstab(hist.trajectory, hist.combo).reindex(index=PATHS, columns=STATES, fill_value=0)
    assert int(tab.to_numpy().sum()) == 168
    assert int(tab[['Yes', 'No']].to_numpy().sum()) == 144
    ax = fig.add_axes([.124, .103, .286, .249])
    heat(ax, tab.values, PATHS, STATES, vmax=int(tab.to_numpy().max()))
    ax.tick_params(axis='y', labelsize=10, pad=6)
    ax.tick_params(axis='x', labelsize=10, pad=5)
    for j, n in enumerate(tab.sum(axis=1)):
        ax.text(2.77, j, f'{int(n)}', ha='center', va='center', fontsize=10)
    ax.text(2.77, -.90, 'n', ha='center', va='center', fontsize=10, clip_on=False)
    ax.text(-.61, -.90, 'ICS path', ha='right', va='center', fontsize=9.5, clip_on=False)
    ax.text(.94, -.90, 'Combination answer (2021)', ha='center', va='center', fontsize=9.5, clip_on=False)
    ax.set_xlim(-.5, 3.10)
    fig.text(.254, .068, '168 countries; 144 known combination answers',
             ha='center', va='center', fontsize=9.3)

    heading(fig, [.549, .386, .416, .008], 'd', 'ICS No with combination Yes')
    selected = full.loc[full.ics2021.eq('No') & full.combo2021.eq('Yes')].sort_values('iso3')
    assert set(selected.iso3) == {'DZA', 'KNA', 'UZB'}
    ax = fig.add_axes([.551, .153, .417, .185])
    examplexs = [4.60, 6.0, 7.4]
    for x, label in zip(examplexs, ['Bronch.', 'ICS', 'Combo']):
        ax.text(x, 3.09, label, ha='center', va='bottom', fontsize=9.5)
    names = {'DZA': 'Algeria (DZA)', 'KNA': 'Saint Kitts and Nevis (KNA)', 'UZB': 'Uzbekistan (UZB)'}
    for i, row in enumerate(selected.itertuples()):
        y = 2.5 - i
        ax.text(.06, y, names[row.iso3], ha='left', va='center', fontsize=9.9)
        for x, (field, _) in zip(examplexs, MEDICINES):
            s = getattr(row, field)
            ax.add_patch(Rectangle((x - .39, y - .28), .78, .56,
                                   facecolor=SC[s], edgecolor='none'))
            ax.text(x, y, 'Y' if s == 'Yes' else 'N', ha='center',
                    va='center', fontsize=9.2, color='white')
    ax.set(xlim=(0, 8), ylim=(-.05, 3.37))
    quiet(ax)
    fig.text(.758, .114, 'Three observed country profiles', ha='center', fontsize=9.5)
    statuslegend(fig)

    source('Figure 4 complete medicine patterns', full[['iso3', 'country', 'region'] + fields + ['pattern']])
    source('Figure 4 taxonomy branches', branches)
    source('Figure 4 answer combinations', pd.DataFrame(patterns))
    source('Figure 4 history by combination', tab.reset_index())
    source('Figure 4 observed country profiles', selected[['iso3', 'country', 'region'] + fields + ['trajectory']])
    save34(fig, 'Figure 4')


if __name__ == '__main__':
    fig3()
    fig4()
