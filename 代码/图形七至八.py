"""Figures 7-8: fixed-model comparisons and burden-concentration sensitivity.

The figure contract is common-sample model comparison, followed by transparent
perturbations of the reported NNN burden share. No models are fitted here.
All points represent actual frozen outputs or exact deterministic recalculation.
"""
import sys
from pathlib import Path
from 绘图公共 import *
from matplotlib.ticker import FixedLocator, FuncFormatter, PercentFormatter
from matplotlib.patches import Rectangle

PRIMARY = pd.read_csv(ROOT/'表格/四项预设模型.csv')
MODELS = pd.read_csv(ROOT/'表格/模型敏感性结果.csv')
DIAGNOSTICS = pd.read_csv(ROOT/'表格/模型诊断与分母.csv').set_index('model_id')
OUTCOMES = [('ics2021','ICS'),('combo2021','Combination inhaler')]
FONTS = {'family':'Times New Roman','color':'black'}
plt.rcParams.update({'font.family':'Times New Roman','pdf.fonttype':42,'svg.fonttype':'none'})


def export(fig,name):
    """Explicit vector/raster exports; other style settings remain shared."""
    fig.savefig(MAIN/(name+'.pdf'))
    fig.savefig(MAIN/(name+'.svg'))
    fig.savefig(MAIN/(name+'.png'),dpi=320)
    fig.savefig(PREVIEW/(name+'.png'),dpi=320)
    plt.close(fig)
    print(name,'saved',flush=True)


def modelrow(frame, model, variable):
    selection = frame[frame.model_id.eq(model)&frame.variable.eq(variable)]
    assert len(selection)==1, (model,variable,len(selection))
    row=selection.iloc[0]
    assert 0 < row.ci95_lower <= row.odds_ratio <= row.ci95_upper
    return row


def oddsaxis(ax, xlabel=True):
    ax.set_xscale('log')
    ax.set_xlim(.125,2)
    ax.xaxis.set_major_locator(FixedLocator([.2,.5,1,2]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v:g}'))
    ax.minorticks_off()
    ax.axvline(1,color='#90969A',lw=.8,ls=(0,(3,3)),zorder=0)
    ax.tick_params(axis='y',length=0)
    ax.spines['left'].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='x',color='#EEF0F2',lw=.6)
    if xlabel: ax.set_xlabel('Odds ratio',fontsize=10)


def pointci(ax, row, y, marker='o', filled=True, color=NO):
    ax.plot([row.ci95_lower,row.ci95_upper],[y,y],color=color,lw=1.35,zorder=2)
    ax.scatter([row.odds_ratio],[y],s=35,marker=marker,
               facecolor=color if filled else 'white',edgecolor=color,lw=1.2,zorder=3)


def figure7():
    # Validate the fixed-country comparisons with identities, not n alone.
    same=[]
    for outcome,label in OUTCOMES:
        g=f'{outcome}_gdp_same_sample'; h=f'{outcome}_health_same_sample'
        assert DIAGNOSTICS.loc[g,'included_iso3']==DIAGNOSTICS.loc[h,'included_iso3']
        assert int(DIAGNOSTICS.loc[g,'complete_n']) in [172,150]
        for model in [g,h]:
            assert DIAGNOSTICS.loc[model,'status']=='fitted'
            same.extend(MODELS[MODELS.model_id.eq(model)].to_dict('records'))
    same=pd.DataFrame(same)
    source('Figure 7 common-country model estimates',same)

    fig=plt.figure(figsize=(11.2,7.6))
    outer=fig.add_gridspec(2,1,left=.035,right=.975,top=.91,bottom=.11,
                          height_ratios=[1.45,1],hspace=.48)
    top=outer[0].subgridspec(1,5,width_ratios=[2.15,1.35,1.7,1.35,1.7],wspace=.11)
    labels=fig.add_subplot(top[0,0]); labels.set_axis_off()
    panel(labels,'a','Common-country comparisons')
    positions=[0,.82,2.0,2.82,4.0,4.82]
    predictorlabels=['GDP per capita','Health expenditure','PM2.5 · GDP model','PM2.5 · health model',
                     'OOP share · GDP model','OOP share · health model']
    labels.set_xlim(0,1);labels.set_ylim(5.45,-.50)
    for y,label in zip(positions,predictorlabels):
        labels.text(0,y,label,va='center',fontsize=10)
    labels.text(0,1.30,'Economic indicators: per doubling',fontsize=8.5,color='black')
    labels.text(0,3.30,'PM2.5: per 10 µg/m³',fontsize=8.5,color='black')
    labels.text(0,5.30,'OOP: per 10 percentage points',fontsize=8.5,color='black')

    for j,(outcome,label) in enumerate(OUTCOMES):
        ax=fig.add_subplot(top[0,1+j*2]); numbers=fig.add_subplot(top[0,2+j*2])
        n=int(DIAGNOSTICS.loc[f'{outcome}_gdp_same_sample','complete_n'])
        ax.set_title(f'{label}\nn = {n}',fontsize=11,pad=10)
        numbers.set_title('OR (95% CI)',fontsize=10,pad=10)
        ax.set_ylim(5.45,-.50);numbers.set_ylim(5.45,-.50);numbers.set_xlim(0,1)
        numbers.set_axis_off();ax.set_yticks([]);oddsaxis(ax)
        specifications=[('gdp','gdp'),('health','health'),('gdp','pm25'),('health','pm25'),('gdp','oop'),('health','oop')]
        for y,(economic,variable) in zip(positions,specifications):
            row=modelrow(MODELS,f'{outcome}_{economic}_same_sample',variable)
            marker='o' if economic=='gdp' else 's'
            pointci(ax,row,y,marker=marker,filled=economic=='gdp')
            numbers.text(.03,y,f'{row.odds_ratio:.3f} ({row.ci95_lower:.3f}–{row.ci95_upper:.3f})',
                         fontsize=9.4,va='center')
        for hline in [1.55,3.55]:
            ax.axhline(hline,color='#E5E5E5',lw=.7)
            numbers.axhline(hline,color='#E5E5E5',lw=.7)

    lower=outer[1].subgridspec(1,4,width_ratios=[1.9,2,2,2],wspace=.26)
    rowlabels=fig.add_subplot(lower[0,0]);rowlabels.axis('off')
    panel(rowlabels,'b','Health model: added-country check')
    rowlabels.set_ylim(-.55,3.55);rowlabels.set_xlim(0,1)
    yy=[2.9,2.25,.75,.1]
    for y,label in zip(yy,['ICS · common, 172','ICS · available, 178','Combination · common, 150','Combination · available, 154']):
        rowlabels.text(0,y,label,fontsize=9.5,va='center')
    checks=[]
    for j,(variable,label) in enumerate([('health','Health expenditure'),('pm25','PM2.5'),('oop','OOP share')]):
        ax=fig.add_subplot(lower[0,j+1]);ax.set_title(label,fontsize=10.5,pad=10)
        ax.set_ylim(-.55,3.55);ax.set_yticks([]);oddsaxis(ax)
        for k,(outcome,_) in enumerate(OUTCOMES):
            for offset,(frame,suffix,filled) in enumerate([(MODELS,'_health_same_sample',True),(PRIMARY,'_health',False)]):
                row=modelrow(frame,outcome+suffix,variable)
                pointci(ax,row,yy[k*2+offset],filled=filled)
                checks.append({'display outcome':outcome,'sample display':'common' if filled else 'all available',**row.to_dict()})
        ax.axhline(1.55,color='#E5E5E5',lw=.7)
    source('Figure 7 health-model sample check',pd.DataFrame(checks))
    selectedids=list(same.model_id.unique())+[f'{o}_health' for o,_ in OUTCOMES]
    source('Figure 7 model denominators',DIAGNOSTICS.loc[selectedids].reset_index())
    fig.text(.5,.025,'Outcome: reported No. Point estimates and robust 95% CIs; the reference line is OR = 1.',
             ha='center',fontsize=9.5,color='black')
    export(fig,'Figure 7')


def shares(frame):
    group=frame[frame.trajectory.eq('NNN')]
    return {'retained countries':len(frame),'NNN countries':len(group),
            'NNN DALYs':group.daly2021.sum(),'denominator DALYs':frame.daly2021.sum(),
            'DALY share':100*group.daly2021.sum()/frame.daly2021.sum(),
            'NNN population':group.pop2021.sum(),'denominator population':frame.pop2021.sum(),
            'population share':100*group.pop2021.sum()/frame.pop2021.sum()}


def sensitivity_data():
    base=shares(B)
    ordered=B.sort_values(['daly2021','iso3'],ascending=[False,True])
    individual=pd.DataFrame([{'omitted ISO3':r.iso3,'omitted country':r.country,
                             'omitted trajectory':r.trajectory,'omitted DALYs':r.daly2021,
                             **shares(B[B.iso3.ne(r.iso3)])} for r in ordered.itertuples()])
    cumulative=pd.DataFrame([{'omitted count':k,'omitted ISO3':';'.join(ordered.iloc[:k].iso3),
                             'last omitted':ordered.iloc[k-1].iso3 if k else 'None',
                             **shares(ordered.iloc[k:])} for k in range(11)])
    regions=pd.DataFrame([{'omitted region':region,'region label':RL[region],
                          **shares(B[B.region.ne(region)])} for region in REGIONS])
    assert len(individual)==168
    assert np.isclose(base['DALY share'],45.69449572821605)
    india=individual[individual['omitted ISO3'].eq('IND')].iloc[0]
    assert np.isclose(india['DALY share'],20.81861913539574)
    assert np.isclose(cumulative.iloc[1]['DALY share'],india['DALY share'])
    previous=pd.read_csv(ROOT/'表格/敏感性轨迹负担.csv')
    previous=previous[previous.trajectory.eq('NNN')].set_index('sample')
    for _,row in regions.iterrows():
        assert np.isclose(row['DALY share'],previous.loc['without_'+row['omitted region'],'daly_percent_sample'])
    # Rank is an observed statistic used to create an empirical distribution, not jitter.
    ecdf=individual.sort_values(['DALY share','omitted ISO3']).copy()
    ecdf['empirical cumulative percent']=np.arange(1,len(ecdf)+1)/len(ecdf)*100
    source('Figure 8 original panel',pd.DataFrame([base]))
    source('Figure 8 individual-country omissions',ecdf)
    source('Figure 8 cumulative large-country omissions',cumulative)
    source('Figure 8 regional omissions',regions)
    return base,individual,cumulative,regions,ecdf


def figure8():
    base,individual,cumulative,regions,ecdf=sensitivity_data()
    india=individual[individual['omitted ISO3'].eq('IND')].iloc[0]
    fig=plt.figure(figsize=(11.2,8.0))
    gs=fig.add_gridspec(2,1,left=.075,right=.965,top=.935,bottom=.12,
                        height_ratios=[1.26,1],hspace=.46)
    top=gs[0].subgridspec(1,2,width_ratios=[1.95,1],wspace=.35)
    ax=fig.add_subplot(top[0,0]);panel(ax,'a','Cumulative removal of large contributors')
    for variable,color,marker,label in [('DALY share',NO,'o','Asthma DALYs'),('population share',YES,'s','Resident population 25+')]:
        ax.plot(cumulative['omitted count'],cumulative[variable],color=color,lw=1.8,marker=marker,ms=4.2,label=label,zorder=3)
    ax.set_xticks(range(11),[f'{int(r["omitted count"])}\n{r["last omitted"]}' for _,r in cumulative.iterrows()],fontsize=8.8)
    ax.set_xlim(-.35,10.35);ax.set_ylim(0,56);ax.set_yticks([0,10,20,30,40,50])
    ax.set_ylabel('NNN share of the retained sample (%)')
    ax.set_xlabel('Countries removed, in order of original DALYs',fontsize=10,labelpad=8)
    grid(ax)
    ax.text(3.0,43.5,'India is removed first',fontsize=10,color='black',va='bottom')
    ax.plot([1,2.85],[india['DALY share'],43.5],color='#737373',lw=.8)
    for variable,offset in [('DALY share',2.5),('population share',-4.7)]:
        row=cumulative.iloc[-1]
        ax.text(9.5,row[variable]+offset,f'{row[variable]:.1f}%',fontsize=10,color='black',ha='center')

    ax=fig.add_subplot(top[0,1]);panel(ax,'b','India changes the magnitude')
    values=[base['DALY share'],india['DALY share']]
    ax.bar([0,1],values,width=.48,color=[NO,'#BF879A'],edgecolor='none')
    for x,y in enumerate(values):ax.text(x,y+1.6,f'{y:.1f}%',ha='center',fontsize=11,color='black')
    ax.set_xticks([0,1],['All countries\nn = 168','Without India\nn = 167'],fontsize=10)
    ax.set_ylim(0,62);ax.set_xlim(-.6,1.6);ax.set_yticks([0,20,40,60]);ax.set_ylabel('NNN DALY share (%)',fontsize=10)
    ax.text(.5,.95,f'{india["DALY share"]-base["DALY share"]:+.1f} percentage points',transform=ax.transAxes,
            ha='center',va='top',fontsize=11,color='black')

    bottom=gs[1].subgridspec(1,2,width_ratios=[1.12,1.18],wspace=.48)
    ax=fig.add_subplot(bottom[0,0]);panel(ax,'c','All 168 single-country omissions')
    ax.step(ecdf['DALY share'],ecdf['empirical cumulative percent'],where='post',color='#AAADB1',lw=1,zorder=1)
    ax.scatter(ecdf['DALY share'],ecdf['empirical cumulative percent'],color=NO,s=10,alpha=.75,zorder=2)
    one=ecdf[ecdf['omitted ISO3'].eq('IND')].iloc[0]
    ax.scatter([one['DALY share']],[one['empirical cumulative percent']],color=NO,s=48,zorder=3)
    ax.axvline(base['DALY share'],color='#72777C',lw=.85,ls=(0,(3,3)))
    ax.text(25,33,'India',fontsize=10,color='black',va='bottom')
    ax.plot([one['DALY share'],24.5],[one['empirical cumulative percent'],32.5],color='#737373',lw=.7)
    ax.set_xlim(15,55);ax.set_ylim(-3,104);ax.set_yticks([0,25,50,75,100]);ax.set_ylabel('Country omissions accumulated (%)',fontsize=10)
    ax.set_xlabel('NNN DALY share after one omission (%)',fontsize=10);grid(ax)
    ax.text(.03,.85,'One point = one omitted country',transform=ax.transAxes,fontsize=9,va='top')

    ax=fig.add_subplot(bottom[0,1]);panel(ax,'d','Regional exclusions')
    for j,row in regions.iterrows():
        ax.plot([row['population share'],row['DALY share']],[j,j],color='#D8DBDE',lw=2,zorder=1)
        ax.scatter(row['DALY share'],j,color=NO,s=34,marker='o',zorder=3)
        ax.scatter(row['population share'],j,color=YES,s=32,marker='s',zorder=3)
        ax.text(row['population share']-1.5,j,f'{row["population share"]:.1f}',ha='right',va='center',fontsize=9.2)
        ax.text(row['DALY share']+1.5,j,f'{row["DALY share"]:.1f}',ha='left',va='center',fontsize=9.2)
    ax.set_yticks(range(6),[f'{r["omitted region"]}  (n={r["retained countries"]})' for _,r in regions.iterrows()],fontsize=9.5)
    ax.set_ylim(5.5,-.65);ax.set_xlim(0,65);ax.set_xticks([0,20,40,60]);ax.set_xlabel('NNN share of the retained sample (%)',fontsize=10)
    for tick in ax.get_yticklabels():
        if tick.get_text().startswith('SEAR'):tick.set_fontweight('bold')
    fig.legend(handles=[Line2D([],[],color=NO,marker='o',label='Asthma DALYs'),
                        Line2D([],[],color=YES,marker='s',label='Resident population aged 25+')],
               loc='lower center',bbox_to_anchor=(.5,.038),ncol=2,fontsize=10)
    export(fig,'Figure 8')


def write_documents():
    caps='''# Figures 7–8 captions

**Figure 7. Economic indicators, air pollution, and reported inhaler availability.** (a) GDP and health-expenditure specifications compared within identical country sets for each outcome: 172 countries for ICS and 150 for combination inhalers. Circles identify GDP models and open squares identify health-expenditure models. Displayed values are odds ratios and robust 95% confidence intervals for a reported No answer, with the numerical estimates shown alongside. (b) Existing health-expenditure models using the common countries (filled circles) or all available countries (open circles; 178 and 154, respectively). The shared logarithmic axes retain intervals crossing OR=1. GDP and health expenditure are alternatives, not simultaneous predictors. Country-level associations do not establish effects on treatment or health. Model definitions, units, eligible populations, and exclusions appear in Models and sensitivity figure methods.

**Figure 8. Large-country dependence of persistent-No burden concentration.** NNN denotes ICS No in all three surveys, 2017–2021. (a) DALY and resident-population shares after cumulatively excluding the ten largest contributors to original-panel DALYs, in their fixed initial order. (b) Removing India changes the NNN DALY share from 45.69% to 20.82%. (c) Exact empirical distribution of all 168 single-country omissions; each point represents one recalculated result, not a confidence limit or bootstrap replicate. The dashed line marks the original share. (d) Shares after excluding each WHO region, with retained sample sizes. South-East Asia exclusion reduces the DALY share to 21.58%. Every numerator and denominator is recalculated. Estimates cover ages 25 and older, using GBD 2023 data for calendar year 2021; uncertainty intervals are not inferred without draws.
'''
    methods='''# Models and sensitivity figure methods

Figure 7 reads frozen coefficients, confidence limits, and model diagnostics from 四项预设模型.csv, 模型敏感性结果.csv, and 模型诊断与分母.csv. The plotting script does not fit or select any model. The top comparisons use existing models with suffixes gdp same sample and health same sample; included ISO3 strings are checked for exact identity within each outcome, not merely equality of sample sizes. The common samples contain 172 countries for ICS and 150 for the budesonide–formoterol combination inhaler. The GDP coefficient is expressed per doubling of GDP per capita; the health-expenditure coefficient is per doubling of health expenditure per capita. PM2.5 is per 10 µg/m³ and out-of-pocket expenditure share is per 10 percentage points. GDP and health expenditure are alternative economic covariates. Full variable, model, and denominator records accompany the figures as source CSV files.

The outcome is a national reported No answer (No=1, Yes=0). The ICS eligibility frame requires valid answers for ICS and bronchodilator inhalers in 2021; the combination eligibility frame requires valid answers for all three medicines. Unknown answers are excluded from these outcome analyses, not recoded as No. General availability refers to the WHO survey threshold; No does not establish zero supply or lack of every anti-inflammatory treatment. These are ecological, exploratory associations and are not estimates of patient-level treatment effects. The figure retains both estimates with confidence intervals crossing OR=1 and those not crossing it. It does not encode significance stars or reinterpret an interval crossing one as proof of no association.

Displayed confidence intervals are taken directly from the saved logistic-regression results using the HC1 independent-country sandwich covariance estimator, with factor n/(n−p). Reference lines at OR=1 mark the null odds ratio. Panel 7b compares the common-country health specifications with the previously fitted all-available health specifications (178 ICS countries and 154 combination-inhaler countries). Filled and open symbols identify sample definitions, not statistical significance. No confidence interval is constructed for the difference between models. All original country exclusions and convergence records are preserved in the source tables.

Figure 8 uses the existing 168-country balanced panel with explicit Yes/No answers for both ICS and bronchodilator in each of 2017, 2019, and 2021. NNN comprises the 35 countries reporting ICS No in all three surveys. The baseline shares are the sum of 2021 asthma DALYs or population among those countries divided by the corresponding total across the selected panel. The GBD release is GBD 2023; the displayed observation year is 2021 and both burden and population refer to ages 25 years and older. Population means residents, not diagnosed patients or medicine users. National medication answers are not restricted to adults.

For every single-country omission, the omitted country is removed from the denominator and, where applicable, the NNN numerator. All 168 countries are omitted individually. The empirical cumulative distribution plots the sorted resulting DALY shares against ranks 1/168 through 168/168; rank is an observed statistic, and no jitter, synthetic data, bootstrap, or sampled subset is used. These results are exact sensitivity point estimates conditional on the frozen inputs, not uncertainty intervals. The original-panel share is shown as a reference only. The regional omission results are checked for numerical agreement with the frozen sensitivity table.

For cumulative exclusions, countries are ranked once by their original-panel 2021 DALY total, using ISO3 only to break ties. The same initial ranking is used for removals of zero through ten countries: IND, IDN, USA, PAK, BGD, PHL, BRA, NGA, MMR, and RUS. Countries are not reselected to maximize or minimize the displayed share. Each point recalculates the numerator and denominator. The first removal, India, reduces the NNN DALY share from 45.6945% to 20.8186% and the resident-population share from 36.2061% to 16.4776%. The cumulative sequence is not monotonic because omitted countries have different ICS trajectories.

Regional exclusions remove all original-panel members of each WHO region. Retained n is displayed. AFR, AMR, EMR, EUR, SEAR, and WPR denote Africa, the Americas, the Eastern Mediterranean, Europe, South-East Asia, and the Western Pacific. Excluding South-East Asia reduces the NNN DALY share to 21.5836%, showing that the magnitude depends substantially on regional composition. Connections between DALY and population markers simply join two statistics; they are not confidence intervals. No GBD uncertainty bounds are constructed by summing marginal limits because joint draws are unavailable. Map-scope and alternative-panel checks remain in supplementary Figure S3.

Reproduction uses 代码/图形七至八.py and the unchanged shared plotting module 代码/绘图公共.py. Exports include editable PDF/SVG, PNG, previews, source CSVs, and figure-specific QA outputs. All observations plotted in the sensitivity panels are actual country calculations; the statistical pipeline and model estimates are unchanged.
'''
    directory=ROOT/'报告';directory.mkdir(exist_ok=True,parents=True)
    (directory/'Figures 7–8 captions.md').write_text(caps,encoding='utf-8')
    (directory/'Models and sensitivity figure methods.md').write_text(methods,encoding='utf-8')


if __name__=='__main__':
    figure7()
    figure8()
    write_documents()
