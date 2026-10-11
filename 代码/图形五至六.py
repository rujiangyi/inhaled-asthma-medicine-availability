"""Figures 5–6: unequal panels, country-level rank views and preserved denominators."""
import sys
from pathlib import Path
from 绘图公共 import *
from matplotlib.ticker import FuncFormatter, FixedLocator

TABLES = ROOT / '表格'
GROUPS = ['NNN', 'Changed', 'YYY']
GC = {'NNN': NO, 'Changed': GOLD, 'YYY': YES}
RNG = np.random.default_rng(20261005)

def fig5():
    shares = pd.read_csv(TABLES / 'ICS轨迹负担与人口.csv').set_index('trajectory').loc[PATHS].reset_index()
    for r in shares.itertuples():
        z = B[B.trajectory.eq(r.trajectory)]
        assert len(z) == r.country_n
        assert np.isclose(z.daly2021.sum(), r.daly2021)
        assert np.isclose(z.pop2021.sum(), r.pop25_2021)
    rank = B.sort_values(['daly2021', 'iso3'], ascending=[False, True]).reset_index(drop=True).copy()
    rank['country rank'] = np.arange(1, len(rank) + 1)
    total = rank.daly2021.sum()
    cumulative = []
    for p in PATHS:
        col = f'{p} cumulative panel DALY percent'
        rank[col] = rank.daly2021.where(rank.trajectory.eq(p), 0).cumsum() / total * 100
        cumulative.append(np.r_[0, rank[col].to_numpy()])
    rank['cumulative panel DALY percent'] = rank.daly2021.cumsum() / total * 100
    assert np.isclose(sum(x[-1] for x in cumulative), 100)

    fig = plt.figure(figsize=(11.25, 9.2))
    ax = fig.add_axes([.078, .565, .885, .36])
    panel(ax, 'a', 'Where adult asthma DALYs accumulate')
    x = np.r_[0, rank['country rank'].to_numpy()]
    ax.stackplot(x, cumulative, colors=[PC[p] for p in PATHS], step='post',
                 edgecolor='white', linewidth=.18, alpha=.94)
    ax.step(x, np.r_[0, rank['cumulative panel DALY percent']], where='post', color=INK, lw=1.15)
    for count in [10, 25, 50]:
        v = float(rank.loc[count - 1, 'cumulative panel DALY percent'])
        ax.scatter(count, v, s=24, facecolor='white', edgecolor=INK, linewidth=.85, zorder=6)
        ax.annotate(f'Top {count}: {v:.1f}%', (count, v), xytext=(9, 9),
                    textcoords='offset points', fontsize=8.6, color='black',
                    bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .85, 'pad': 1.2})
    ax.set_xlim(0, 168); ax.set_ylim(0, 105)
    ax.set_xticks([0, 25, 50, 75, 100, 125, 150, 168])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel('Countries ranked by 2021 adult asthma DALYs (highest to lowest)')
    ax.set_ylabel('Cumulative share of panel DALYs (%)')
    grid(ax)
    figlegend(fig, [(p, PC[p]) for p in PATHS], y=.474, ncol=8)

    ax = fig.add_axes([.078, .095, .365, .305])
    panel(ax, 'b', 'Three denominators, eight trajectories')
    cols = ['country_percent', 'resident_population_percent_sample', 'daly_percent_sample']
    yy = np.arange(8)
    ax.hlines(yy, shares[cols].min(axis=1), shares[cols].max(axis=1), color='#CCD1D5', lw=1.5)
    for col, label, marker, color in zip(cols, ['Countries', 'Residents aged 25+', 'Asthma DALYs'],
                                         ['o', 's', 'D'], [INK, YES, NO]):
        ax.scatter(shares[col], yy, s=27, marker=marker, color=color,
                   edgecolors='white', linewidths=.4, label=label, zorder=3)
    ax.set_yticks(yy, [f'{p}  {int(n)}' for p, n in zip(PATHS, shares.country_n)], fontsize=8.7)
    ax.invert_yaxis(); ax.set_xlim(0, 67); ax.set_xticks([0, 20, 40, 60])
    ax.set_xlabel('Share within the 168-country panel (%)')
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.205), ncol=3, fontsize=8.2,
              columnspacing=.9, handletextpad=.4, borderaxespad=0)
    grid(ax, 'x')

    ax = fig.add_axes([.555, .095, .408, .305])
    panel(ax, 'c', 'Contributors among 35 NNN countries')
    nn = B[B.trajectory.eq('NNN')].sort_values(['daly2021', 'iso3'], ascending=[False, True]).copy()
    assert len(nn) == 35
    nn['NNN rank'] = np.arange(1, len(nn) + 1)
    nn['NNN DALY share percent'] = nn.daly2021 / nn.daly2021.sum() * 100
    positions = np.arange(len(nn))
    assert nn['NNN DALY share percent'].gt(0).all()
    lower_exponent = int(np.floor(np.log10(nn['NNN DALY share percent'].min()*.8)))
    floor = 10.0**lower_exponent
    ax.vlines(positions, floor, nn['NNN DALY share percent'], color=NO, linewidth=.85, alpha=.48)
    ax.scatter(positions, nn['NNN DALY share percent'], s=23, color=NO,
               edgecolor='white', linewidth=.35, zorder=3)
    ax.set_yscale('log'); ax.set_ylim(floor, 150)
    ticks = [10.0**v for v in range(lower_exponent,3)]
    ax.set_yticks(ticks);ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_:f'{y:g}'))
    ax.set_xlim(-.7, len(nn)-.3)
    ax.set_xticks(positions, nn.iso3, rotation=90, fontsize=7.1)
    ax.set_ylabel('Share of NNN DALYs (%; log scale)')
    ax.set_xlabel('Country')
    india = nn[nn.iso3.eq('IND')].iloc[0]
    for iso,label in [('IND','India'),('PAK','Pakistan')]:
        country = nn[nn.iso3.eq(iso)].iloc[0]
        ax.annotate(f'{label}  {country["NNN DALY share percent"]:.1f}%',
                    (int(country['NNN rank'])-1, country['NNN DALY share percent']),
                    xytext=(12, 6), textcoords='offset points', fontsize=8.7,
                    arrowprops={'arrowstyle': '-', 'color': INK, 'lw': .7})
    grid(ax)
    source('Figure 5 trajectory shares', shares)
    source('Figure 5 country cumulative contributions', rank)
    source('Figure 5 NNN country contributions', nn)
    save(fig, 'Figure 5')
    return {'panel n': len(B), 'panel DALYs': total, 'NNN n': len(nn),
            'NNN India percent': float(india['NNN DALY share percent']),
            'top10 DALY percent': float(rank.loc[9, 'cumulative panel DALY percent']),
            'top25 DALY percent': float(rank.loc[24, 'cumulative panel DALY percent']),
            'top50 DALY percent': float(rank.loc[49, 'cumulative panel DALY percent'])}

def distribution(ax, frame, variable, title, log=False):
    ax.set_title(title, loc='left', fontsize=9.5, pad=4)
    arrays = [frame.loc[frame['trajectory group'].eq(g), variable].dropna().to_numpy() for g in GROUPS]
    bp = ax.boxplot(arrays, positions=np.arange(3), vert=False, widths=.44,
                    patch_artist=True, showfliers=False, manage_ticks=False,
                    medianprops={'color':'black','linewidth':1},
                    whiskerprops={'color':'#68727A','linewidth':.65},
                    capprops={'color':'#68727A','linewidth':.65}, boxprops={'linewidth':.75})
    for i,(g, values, box) in enumerate(zip(GROUPS, arrays, bp['boxes'])):
        box.set_facecolor(colors.to_rgba(GC[g], .17)); box.set_edgecolor(GC[g])
        ax.scatter(values, i+RNG.uniform(-.13,.13,len(values)), s=7, c=GC[g],
                   alpha=.55, edgecolors='none', zorder=3)
    ax.set_yticks(range(3), [f'{g} ({len(v)})' for g,v in zip(GROUPS,arrays)], fontsize=7.8)
    ax.set_ylim(2.55, -.55)
    if log:
        ax.set_xscale('log'); ax.set_xlim(20,15000); ax.set_xticks([100,1000,10000])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x:,.0f}'))
    else:
        ax.set_xlim(0,120 if variable=='pm25' else 100)
        ax.set_xticks([0,50,100])
    ax.tick_params(axis='x', labelsize=8, length=2)
    grid(ax,'x')
    return [{'variable':variable,'group':g,'n':len(v),'median':float(np.median(v)),
             'q25':float(np.quantile(v,.25)),'q75':float(np.quantile(v,.75))}
            for g,v in zip(GROUPS,arrays)]

def fig6():
    frame = B.copy()
    frame['trajectory group'] = frame.trajectory.where(frame.trajectory.isin(['NNN','YYY']),'Changed')
    variables = ['pm25','gdp','oop','health']
    complete = frame.dropna(subset=variables+['pop2021']).sort_values(['gdp','iso3']).copy()
    assert len(complete)==160
    scatter = frame.dropna(subset=['pm25','gdp','pop2021']).copy()
    assert set(scatter.iso3) == set(complete.iso3)
    scatter['bubble area points2'] = 10+4*np.sqrt(scatter.pop2021/1e6)
    complete['GDP ascending country rank'] = np.arange(1,len(complete)+1)
    for var in variables:
        complete[var+' percentile'] = complete[var].rank(method='average',pct=True)*100
    assert complete.gdp.is_monotonic_increasing
    frame['included in scatter'] = frame.iso3.isin(scatter.iso3)
    frame['included in percentile matrix'] = frame.iso3.isin(complete.iso3)
    frame['missing contextual variables'] = frame[variables].isna().apply(
        lambda r: '; '.join(r.index[r].tolist()), axis=1)
    fig=plt.figure(figsize=(11.25,9.2))
    ax=fig.add_axes([.077,.41,.56,.515])
    panel(ax,'a','Air pollution and economic resources')
    for status,color in [('No',NO),('Yes',YES)]:
        z=scatter[scatter.ics2021.eq(status)].sort_values('pop2021',ascending=False)
        ax.scatter(z.gdp,z.pm25,s=z['bubble area points2'],c=color,alpha=.66,
                   linewidths=.4,edgecolors='white',zorder=3)
    ax.set_xscale('log');ax.set_xlim(650,200000);ax.set_ylim(0,120)
    ax.set_xticks([1000,10000,100000]);ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x:,.0f}'))
    ax.set_xlabel('GDP per capita (PPP international $; log scale)')
    ax.set_ylabel('PM$_{2.5}$ (µg/m³)');grid(ax)
    ax.text(.02,.035,f'n = {len(scatter)} countries',transform=ax.transAxes,fontsize=9)
    legend_ax=fig.add_axes([.077,.329,.86,.042]);legend_ax.set_axis_off()
    legend_ax.set_xlim(0,1);legend_ax.set_ylim(0,1)
    legend_ax.text(0,.5,'2021 ICS',va='center',fontsize=9)
    for x,lab,col in [(.115,'No',NO),(.205,'Yes',YES)]:
        legend_ax.scatter(x,.5,s=28,c=col,edgecolors='white',linewidths=.4)
        legend_ax.text(x+.014,.5,lab,va='center',fontsize=8.7)
    legend_ax.plot([.30,.30],[.18,.82],color='#CDD1D5',lw=.7)
    legend_ax.text(.325,.5,'Residents aged 25+',va='center',fontsize=9)
    for x,v,lab in [(.555,10,'10 million'),(.70,100,'100 million'),(.87,1000,'1 billion')]:
        legend_ax.scatter(x,.5,s=10+4*np.sqrt(v),c='#A1A8AF',edgecolors='white',linewidths=.4)
        legend_ax.text(x+.018,.5,lab,va='center',fontsize=8.2)
    head=fig.add_axes([.76,.41,.21,.515]);head.set_axis_off()
    panel(head,'b','Context by ICS trajectory')
    summary=[]
    specs=[('pm25','PM$_{2.5}$ (µg/m³)',False,.77),
           ('oop','Out-of-pocket expenditure (%)',False,.592),
           ('health','Health spending (PPP $; log)',True,.414)]
    for var,title,log,y in specs:
        ax=fig.add_axes([.77,y,.20,.12])
        summary.extend(distribution(ax,frame,var,title,log))
    ax=fig.add_axes([.077,.145,.86,.145])
    panel(ax,'c','Four contextual indicators aligned across the same 160 countries')
    arr=complete[[v+' percentile' for v in variables]].to_numpy().T
    cmap=colors.LinearSegmentedColormap.from_list('column percentiles',['#F1F3F4','#9EB5BD','#365F70'])
    im=ax.imshow(arr,aspect='auto',interpolation='nearest',vmin=0,vmax=100,cmap=cmap,
                 extent=[.5,160.5,3.5,-.5])
    ax.set_yticks(range(4),['PM$_{2.5}$','GDP','Out-of-pocket','Health spending'],fontsize=9)
    ax.set_xticks([]);ax.tick_params(length=0)
    ax.set_yticks(np.arange(-.5,4,1),minor=True);ax.grid(which='minor',axis='y',color='white',lw=1.4)
    for spine in ax.spines.values():spine.set_visible(False)
    status=fig.add_axes([.077,.112,.86,.018])
    yn=complete.ics2021.map({'No':0,'Yes':1}).to_numpy()[None,:]
    assert not pd.isna(yn).any()
    status.imshow(yn,aspect='auto',interpolation='nearest',vmin=0,vmax=1,
                  cmap=colors.ListedColormap([NO,YES]),extent=[.5,160.5,.5,-.5])
    status.set_yticks([0],['ICS'],fontsize=9);status.set_xticks([1,40,80,120,160]);status.tick_params(length=2,labelsize=8)
    status.set_xlabel('Countries ordered by GDP per capita (lowest to highest)',fontsize=10,labelpad=5)
    for spine in status.spines.values():spine.set_visible(False)
    cax=fig.add_axes([.954,.145,.011,.145]);cb=fig.colorbar(im,cax=cax,ticks=[0,50,100])
    cb.ax.tick_params(labelsize=8,length=2);cb.outline.set_visible(False)
    cb.ax.set_title('Rank\npercentile',fontsize=8,pad=6)
    source('Figure 6 countries and context',frame[['iso3','country','region','trajectory','trajectory group','ics2021','pop2021']+variables+['included in scatter','included in percentile matrix','missing contextual variables']])
    source('Figure 6 scatter source',scatter[['iso3','country','ics2021','pop2021','pm25','gdp','bubble area points2']])
    source('Figure 6 distribution summaries',pd.DataFrame(summary))
    source('Figure 6 aligned country percentiles',complete[['iso3','country','trajectory','ics2021','GDP ascending country rank']+variables+[v+' percentile' for v in variables]])
    save(fig,'Figure 6')
    return {'scatter n':len(scatter),'matrix n':len(complete),'distribution summaries':summary}

if __name__=='__main__':
    five,six=fig5(),fig6()
    captions='''# Figures 5–6 captions

**Figure 5. Concentration of adult asthma burden across ICS trajectories.**
(a) Cumulative asthma disability-adjusted life years (DALYs) across 168 countries ordered from highest to lowest burden; coloured layers track the eight ICS-response trajectories. (b) Trajectory shares use separate country, population and DALY denominators within that panel. Row labels include country counts. (c) Contributions within the 35 NNN countries, with actual percentages shown on a logarithmic vertical axis. Sequences indicate responses in 2017, 2019 and 2021: N, No; Y, Yes. Burden and population refer to 2021 and ages 25+. These are DALYs among residents, not estimates of untreated or treatment-attributable burden.

**Figure 6. Environmental and health-system context of ICS availability.**
(a) Ambient PM2.5 versus GDP per capita in 160 countries; colour denotes 2021 ICS responses and compressed bubble areas indicate populations aged 25+. (b) Country distributions by ICS trajectory, with available counts; Changed combines six nonconstant response sequences without implying improvement. Boxes indicate medians and interquartile ranges. (c) Four indicators aligned across the same 160 complete-data countries, ordered by GDP; colour denotes within-indicator percentile across countries, not a risk score. The separate status strip records ICS responses. Contextual data are from 2021; GDP and health-spending axes are logarithmic. These descriptive country-level comparisons do not identify causal effects.
'''
    (ROOT/'报告/Figures 5–6 captions.md').write_text(captions,encoding='utf-8')
    (ROOT/'核验/图形五至六核验.json').write_text(json.dumps({'Figure 5':five,'Figure 6':six},ensure_ascii=False,indent=2),encoding='utf-8')
