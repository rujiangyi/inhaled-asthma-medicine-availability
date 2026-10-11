"""Independent audit and supplementary figures S1-S3.

Run with the bundled Python runtime. This file does not mutate analytical inputs,
the primary statistical pipeline, the common plotting module, or main figures.
"""
from pathlib import Path
import csv
import json
import math
from collections import Counter

AUDITROOT = Path(__file__).resolve().parents[1]


def readrows(relative):
    with (AUDITROOT / relative).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def independent_audit():
    """Reconstruct countries from raw answers, using only Python's stdlib."""
    raw = readrows('输入数据/呼吸国家轮次.csv')
    lookup = {(r['Country code'], int(r['Year'])): r for r in raw}
    assert len(lookup) == len(raw) == 970
    countries = sorted({r['Country code'] for r in raw})
    years = (2017, 2019, 2021)
    valid = {'Yes', 'No'}
    keep = [c for c in countries if all(lookup[c, y][m] in valid
            for y in years for m in ('吸入激素', '支气管扩张剂'))]
    trajectories = {c: ''.join(lookup[c, y]['吸入激素'][0] for y in years) for c in keep}
    nnn = sorted(c for c in keep if trajectories[c] == 'NNN')
    g = readrows('输入数据/成人哮喘数据.csv')
    assert {r['age'] for r in g} == {'25+ years'}
    assert {r['cause'] for r in g} == {'Asthma'} and {r['measure'] for r in g} == {'DALYs'}
    d = {r['ISO3']: float(r['value']) for r in g
         if r['year'] == '2021' and r['metric'] == 'Number'}
    poprows = readrows('输入数据/成人哮喘人口.csv')
    assert {r['age'] for r in poprows} == {'25+ years'} and {r['sex id'] for r in poprows} == {'3'}
    p = {r['iso3']: float(r['pop25']) for r in poprows if r['year'] == '2021'}
    assert len(d) == len(p) == 204 and set(keep) <= d.keys() and set(keep) <= p.keys()
    sums = {
        'NNN DALYs': math.fsum(d[c] for c in nnn),
        'Panel DALYs': math.fsum(d[c] for c in keep),
        'Global 204 DALYs': math.fsum(d.values()),
        'NNN population 25+': math.fsum(p[c] for c in nnn),
        'Panel population 25+': math.fsum(p[c] for c in keep),
        'Global 204 population 25+': math.fsum(p.values()),
    }
    shares = {
        'NNN DALY share within 168 (%)': 100*sums['NNN DALYs']/sums['Panel DALYs'],
        'NNN DALY share within global 204 (%)': 100*sums['NNN DALYs']/sums['Global 204 DALYs'],
        'NNN population share within 168 (%)': 100*sums['NNN population 25+']/sums['Panel population 25+'],
        'NNN population share within global 204 (%)': 100*sums['NNN population 25+']/sums['Global 204 population 25+'],
    }
    paired = Counter((lookup[c, 2017]['吸入激素'], lookup[c, 2021]['吸入激素']) for c in keep)
    before = sum(lookup[c, 2017]['吸入激素'] == 'Yes' for c in keep)
    after = sum(lookup[c, 2021]['吸入激素'] == 'Yes' for c in keep)
    change = 100*(after-before)/len(keep)
    reference = next(r for r in readrows('表格/ICS轨迹负担与人口.csv') if r['trajectory'] == 'NNN')
    comparisons = {
        'country_n': len(nnn),
        'daly2021': sums['NNN DALYs'],
        'daly_percent_sample': shares['NNN DALY share within 168 (%)'],
        'daly_percent_global204': shares['NNN DALY share within global 204 (%)'],
        'pop25_2021': sums['NNN population 25+'],
        'resident_population_percent_sample': shares['NNN population share within 168 (%)'],
        'resident_population_percent_global204': shares['NNN population share within global 204 (%)'],
    }
    for key, value in comparisons.items():
        assert math.isclose(value, float(reference[key]), rel_tol=1e-12, abs_tol=1e-8), key
    officialpair = next(r for r in readrows('表格/配对药物变化.csv')
                        if r['medicine']=='ics' and r['before']=='2017' and r['after']=='2021')
    assert math.isclose(change, float(officialpair['change_percentage_points']), abs_tol=1e-12)
    assert len(keep)==168 and len(nnn)==35
    assert paired == {('Yes','Yes'):104, ('Yes','No'):6, ('No','Yes'):21, ('No','No'):37}
    text = ['# 独立统计核验', '',
            '核验日期：2026-10-05。核验代码：`代码/补充图.py` 的 `independent_audit()`。', '',
            '使用 Python 标准库 csv、Counter 与 math.fsum 从原始输入重新构造样本、轨迹和加总值；未导入主统计脚本，也未以其分析表中的样本标记筛选国家。随后与已经生成的结果表逐项比较。', '',
            '输入：`输入数据/呼吸国家轮次.csv`、`输入数据/成人哮喘数据.csv`、`输入数据/成人哮喘人口.csv`。WHO 原始输入为194国×5轮=970行，国家—年份唯一。2021 GBD DALY Number 与25岁及以上人口各204个国家/地区，168国均可匹配。', '',
            '样本规则：2017、2019、2021每轮ICS与支气管扩张剂两项均为明确Yes/No；独立得到168国。ICS三轮为No/No/No得到35国。', '',
            '| 独立复算指标 | 数值 |', '|---|---:|']
    text += [f'| {k} | {v:,.9f} |' for k,v in {**sums, **shares}.items()]
    text += ['', '2017→2021配对ICS答复：Yes→Yes 104国、Yes→No 6国、No→Yes 21国、No→No 37国。Yes由110/168（65.476190%）变为125/168（74.404762%），净变化为15/168×100 = **+8.928571个百分点**。端点No→No的37国不等同于三轮持续No的35国；另外2国属于NYN。', '',
             '8种三轮轨迹：'+ '；'.join(f'{k}={v}' for k,v in sorted(Counter(trajectories.values()).items()))+'。', '',
             '**核验通过：**所核查的7个NNN统计量与既有结果表一致（相对容差1×10⁻¹²，绝对容差1×10⁻⁸）；配对变化也一致。', '',
             '35国ISO3：'+', '.join(nnn)+'。', '',
             '解释边界：NNN表示国家所报ICS一般可得性三轮均为No；No不代表零供应。原题未限定ICS必须为单方，也不能据此判断患者未获抗炎治疗。DALY为25岁及以上哮喘疾病负担，人口为25岁及以上居民人口，均不是接受某药物的患者数量。样本内份额与全球204国/地区份额使用不同分母，不应混称。未取得GBD draws，以上加总份额未构造不确定区间。', '']
    out = AUDITROOT / '核验/独立统计核验.md'
    out.parent.mkdir(exist_ok=True, parents=True)
    out.write_text('\n'.join(text), encoding='utf-8')
    print('Independent audit: PASS; NNN DALYs 45.694496%, population 36.206115%; paired +8.928571 pp.', flush=True)


independent_audit()

# Common module resolves the local matplotlib dependency when required.
from 绘图公共 import *
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter

YEARS5 = [2013, 2015, 2017, 2019, 2021]
BURGUNDY = '#842742'
ROSE = '#BF7D95'
SOFT = '#EDD6DF'
LIGHT = '#F8EFF2'
GRAY = '#D7D9DD'
MISSING = '#B06A83'
BINARY = colors.ListedColormap([YES, NO])
LIGHTMAP = colors.LinearSegmentedColormap.from_list('supplement burgundy', [LIGHT, '#D7A3B5'])

icswide = PANEL.pivot(index='Country code', columns='Year', values='吸入激素')
bronchwide = PANEL.pivot(index='Country code', columns='Year', values='支气管扩张剂')
fiveids = sorted(set(icswide[icswide[YEARS5].isin(VALID).all(axis=1)].index)
                 & set(bronchwide[bronchwide[YEARS5].isin(VALID).all(axis=1)].index))
fivepaths = icswide.loc[fiveids, YEARS5].apply(lambda r: ''.join(x[0] for x in r), axis=1)
assert len(fiveids)==141


def cleanheat(ax, data, rowlabels, collabels, cmap=LIGHTMAP, vmax=None, annotations=True):
    array = np.asarray(data)
    ax.imshow(array, cmap=cmap, vmin=0, vmax=vmax or max(float(np.max(array)), 1), aspect='auto')
    ax.set_xticks(range(len(collabels)), collabels)
    ax.set_yticks(range(len(rowlabels)), rowlabels)
    ax.tick_params(length=0, pad=5)
    ax.set_xticks(np.arange(-.5, len(collabels), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(rowlabels), 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1.5)
    ax.tick_params(which='minor', length=0)
    for spine in ax.spines.values(): spine.set_visible(False)
    if annotations:
        for y in range(array.shape[0]):
            for x in range(array.shape[1]):
                ax.text(x, y, f'{int(array[y,x])}', ha='center', va='center', color='black', fontsize=10)


def supplement1():
    fig = plt.figure(figsize=(13,9))
    gs = fig.add_gridspec(2, 2, left=.12, right=.965, top=.94, bottom=.10,
                          wspace=.58, hspace=.56, width_ratios=[1.03,1])
    ax = fig.add_subplot(gs[0,0]); panel(ax, 'a', 'Unknown answers across five WHO waves')
    labels=[]; matrix=[]; detail=[]
    for med, label in [('吸入激素','ICS'), ('支气管扩张剂','Bronchodilator'), ('复方吸入剂','Combination')]:
        for reason in ["Don't know", 'No report']:
            labels.append(f'{label}: {reason.lower()}'); values=[]
            for year in YEARS5:
                raw=PANEL.loc[PANEL.Year.eq(year), med]
                n=int(raw.eq("Don't know").sum()) if reason=="Don't know" else int(raw.isin(['No response','No data received']).sum())
                structural=int(raw.eq('No observation for year').sum())
                values.append(n)
                detail.append({'year':year,'medicine':label,'missing category':reason,'unknown n':n,'not in API n':structural,'frame n':len(raw)})
            matrix.append(values)
    cleanheat(ax, matrix, labels, YEARS5, vmax=24)
    for r in [4,5]:
        for c in range(4):
            ax.add_patch(Rectangle((c-.5,r-.5),1,1,facecolor='#F2F2F2',edgecolor='#BFC1C5',hatch='///',lw=.3,zorder=4))
    ax.text(.5,-.20,'Cell values are countries out of 194; hatched = not in API.',transform=ax.transAxes,ha='center',fontsize=9)
    source('S1 unknown answers', pd.DataFrame(detail))

    ax = fig.add_subplot(gs[0,1]); panel(ax,'b','2021 covariates in the extraction frame')
    covars=['pm25','gdp','oop','health']
    environment=pd.read_csv(ROOT/'输入数据/呼吸环境社会数据.csv')
    metadata=json.loads((ROOT/'输入数据/呼吸环境社会核验.json').read_text(encoding='utf-8-sig'))
    current=environment[environment.Year.eq(2021)].copy()
    assert len(current)==current['Country code'].nunique()==metadata['csv_country_count']==181
    assert len(environment)==metadata['csv_rows']==905
    current['WB matched']=current['World Bank nonaggregate country'].astype(str).str.lower().eq('true')
    assert set(current.loc[~current['WB matched'],'Country code'])=={'COK','NIU'}
    rawfields=['EN.ATM.PM25.MC.M3','NY.GDP.PCAP.PP.KD','SH.XPD.OOPC.CH.ZS','SH.XPD.CHEX.PP.CD']
    extraction=DF[DF.iso3.isin(current['Country code'])].copy().set_index('iso3')
    rawvalues=current.set_index('Country code')
    for short,rawcol in zip(covars,rawfields):
        assert np.allclose(extraction[short],rawvalues.loc[extraction.index,rawcol],equal_nan=True)
    missing=extraction[covars].isna()
    matched=rawvalues.loc[extraction.index,'WB matched']
    patterns=missing[matched].value_counts().reset_index(name='countries')
    patterns['World Bank matched']=True
    patterns['ISO3']=patterns.apply(lambda row:', '.join(extraction.index[(missing.eq(row[covars].astype(bool))).all(axis=1)&matched]),axis=1)
    unmatchedrow={c:True for c in covars}
    unmatchedrow.update({'countries':2,'World Bank matched':False,'ISO3':'COK, NIU'})
    patterns=pd.concat([patterns,pd.DataFrame([unmatchedrow])],ignore_index=True)
    patternvalues=patterns[covars].astype(int).copy()
    patternvalues.loc[~patterns['World Bank matched'],:]=2
    labels=[f'{int(row.countries)} '+('country' if row.countries==1 else 'countries')+(' *' if not row['World Bank matched'] else '') for _,row in patterns.iterrows()]
    cleanheat(ax,patternvalues,labels,
              ['PM2.5','GDP','OOP','Health'],cmap=colors.ListedColormap([LIGHT,MISSING,GRAY]),vmax=2,annotations=False)
    for j,row in patterns.iterrows():
        for k,col in enumerate(covars):
            label='No match' if not row['World Bank matched'] else ('Missing' if row[col] else 'Present')
            ax.text(k,j,label,ha='center',va='center',fontsize=9,color='black')
    ax.text(.5,-.20,'181-country extraction frame; *2 not matched to World Bank.\n13 other WHO countries were outside this extraction.',transform=ax.transAxes,ha='center',fontsize=9)
    patterns['extraction frame n']=181
    source('S1 WDI missing patterns',patterns)
    collectionstatus=DF[['iso3','country']].copy()
    collectionstatus['extraction status']=collectionstatus.iso3.map(lambda c:'Outside extraction frame' if c not in extraction.index else ('Matched to World Bank' if rawvalues.loc[c,'WB matched'] else 'No World Bank metadata match'))
    source('S1 WDI extraction status',collectionstatus)

    ax = fig.add_subplot(gs[1,0]); panel(ax,'c','Countries retained in 2021 models')
    models=pd.read_csv(ROOT/'表格/模型诊断与分母.csv').set_index('model_id')
    ids=['ics2021_gdp','ics2021_health','combo2021_gdp','combo2021_health']
    names=['ICS: GDP model','ICS: health model','Combination: GDP model','Combination: health model']
    rows=models.loc[ids].reset_index(); yy=np.arange(len(ids))
    ax.barh(yy,rows.complete_n,color=ROSE,height=.56,label='Complete covariates')
    ax.barh(yy,rows.eligible_n-rows.complete_n,left=rows.complete_n,color=GRAY,height=.56,label='Excluded: covariate missing')
    for j,row in rows.iterrows():ax.text(row.eligible_n+3,j,f'{int(row.complete_n)}/{int(row.eligible_n)}',va='center',fontsize=10)
    ax.set_yticks(yy,names);ax.invert_yaxis();ax.set_xlim(0,217);ax.set_xlabel('Countries: retained / eligible');grid(ax,'x')
    ax.legend(loc='lower left',bbox_to_anchor=(-.03,-.38),ncol=1,fontsize=9,handlelength=1.3)
    source('S1 model sample retention',rows[['model_id','eligible_n','complete_n','excluded_missing_n','excluded_missing_iso3']])

    ax = fig.add_subplot(gs[1,1]);panel(ax,'d','2021 bounds for unknown availability')
    bounds=pd.read_csv(ROOT/'表格/缺失极端边界.csv')
    bounds=bounds[bounds.year.eq(2021)&bounds.bound_type.eq('wave_general_availability')].set_index('medicine_or_trajectory').loc[['ics','bronch','combo']].reset_index()
    for y,row in bounds.iterrows():
        ax.plot([row.lower_percent,row.upper_percent],[y,y],color=BURGUNDY,lw=4,solid_capstyle='round')
        ax.scatter([row.lower_percent],[y],s=45,color=BURGUNDY,zorder=3)
        ax.scatter([row.upper_percent],[y],s=45,facecolor='white',edgecolor=BURGUNDY,zorder=3)
        ax.text((row.lower_percent+row.upper_percent)/2,y-.19,f'{row.lower_percent:.1f}-{row.upper_percent:.1f}%',ha='center',fontsize=10)
    ax.set_yticks(range(3),['ICS (13 unknown)','Bronchodilator (6)','Combination (32)'])
    ax.set_ylim(2.65,-.6);ax.set_xlim(0,100);ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0))
    ax.set_xlabel('Yes as a share of 194 countries');grid(ax,'x')
    ax.text(.5,-.26,'Filled: all unknown assigned No; open: all assigned Yes.\nScenario bounds only; original unknown answers are preserved.',transform=ax.transAxes,ha='center',va='top',fontsize=9)
    source('S1 2021 missing scenario bounds',bounds)
    save(fig,'S1',supp=True)


def supplement2():
    fig=plt.figure(figsize=(13.2,12))
    gs=fig.add_gridspec(2,2,left=.07,right=.965,top=.95,bottom=.10,wspace=.39,hspace=.33,height_ratios=[1,1.08])
    ax=fig.add_subplot(gs[0,0]);panel(ax,'a','All observed five-wave ICS sequences')
    freq=fivepaths.value_counts().sort_index()
    matrix=np.array([[int(c=='N') for c in path] for path in freq.index])
    cleanheat(ax,matrix,[f'{p}  (n={n})' for p,n in freq.items()],YEARS5,cmap=BINARY,vmax=1,annotations=False)
    ax.tick_params(axis='y',labelsize=9)
    ax.set_xlabel('Same 141 countries in every wave')
    trajectories=pd.DataFrame({'iso3':fivepaths.index,'sequence':fivepaths.values})
    trajectories['answer changes']=trajectories.sequence.map(lambda p:sum(a!=b for a,b in zip(p,p[1:])))
    source('S2 five-wave country sequences',trajectories)
    source('S2 five-wave sequence frequencies',freq.rename_axis('sequence').reset_index(name='countries'))

    ax=fig.add_subplot(gs[0,1]);panel(ax,'b','Availability in the fixed five-wave panel')
    series=[]
    for medicine,wide,color,marker in [('ICS',icswide,BURGUNDY,'o'),('Bronchodilator',bronchwide,ROSE,'s')]:
        n=wide.loc[fiveids,YEARS5].eq('Yes').sum()
        pct=n/len(fiveids)*100
        ax.plot(YEARS5,pct,color=color,marker=marker,lw=1.7,ms=5,label=medicine)
        for year,val in pct.items():
            ax.text(year,val+2.2,f'{int(n[year])}',ha='center',fontsize=10)
            series.append({'medicine':medicine,'year':year,'yes n':int(n[year]),'denominator':len(fiveids),'yes percent':val})
    ax.set_ylim(0,105);ax.set_xticks(YEARS5);ax.set_ylabel('Reported Yes (%)');ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0));grid(ax)
    ax.legend(loc='lower left');ax.text(.5,-.14,'Labels are Yes counts; denominator = 141.',ha='center',transform=ax.transAxes,fontsize=9)
    source('S2 five-wave availability',pd.DataFrame(series))

    ax=fig.add_subplot(gs[1,0]);panel(ax,'c','ICS change depends on the fixed cohort')
    pairs=[(2017,2019),(2019,2021),(2017,2021)]
    change=[]
    for i,(name,ids,color,shift,marker) in enumerate([
        ('Three-wave panel (168)',list(B.iso3),BURGUNDY,-.1,'o'),
        ('Five-wave panel (141)',fiveids,ROSE,.1,'s')]):
        for j,(before,after) in enumerate(pairs):
            eligible=icswide.loc[ids]
            pct=100*(eligible[after].eq('Yes').sum()-eligible[before].eq('Yes').sum())/len(ids)
            ax.scatter(pct,j+shift,color=color,s=50,marker=marker,label=name if j==0 else None,zorder=3)
            ax.text(pct+.6,j+shift,f'{pct:+.2f}',va='center',fontsize=10)
            change.append({'cohort':name,'n':len(ids),'before':before,'after':after,'change percentage points':pct})
    ax.set_yticks(range(3),[f'{a}-{b}' for a,b in pairs]);ax.set_ylim(2.5,-.7);ax.set_xlim(-1,14)
    ax.axvline(0,color='#777777',lw=.8);grid(ax,'x');ax.set_xlabel('Net change in reported Yes (percentage points)')
    ax.legend(loc='lower left',bbox_to_anchor=(0,-.20),fontsize=9)
    source('S2 paired cohort comparison',pd.DataFrame(change))

    sub=gs[1,1].subgridspec(1,3,wspace=.63)
    reverse=trajectories[trajectories['answer changes'].ge(2)].sort_values(['sequence','iso3'])
    assert len(reverse)==30
    for k in range(3):
        ax=fig.add_subplot(sub[0,k]);chunk=reverse.iloc[k*10:(k+1)*10]
        mat=np.array([[int(c=='N') for c in p] for p in chunk.sequence])
        cleanheat(ax,mat,chunk.iso3,['13','15','17','19','21'],cmap=BINARY,vmax=1,annotations=False)
        ax.tick_params(axis='x',labelsize=8);ax.tick_params(axis='y',labelsize=9)
        if k==0:panel(ax,'d','Countries with at least two answer changes (n=30)')
    source('S2 countries with repeated changes',reverse)
    fig.legend(handles=[Patch(facecolor=YES,label='Y: Yes'),Patch(facecolor=NO,label='N: No')],loc='lower center',bbox_to_anchor=(.5,.045),ncol=2)
    save(fig,'S2',supp=True,footer='2013 and 2015 instrument wording has not been audited; the extended series is exploratory. Changes describe reported answers.')


def burden_share(frame):
    subset=frame[frame.trajectory.eq('NNN')]
    return {'sample n':len(frame),'NNN n':len(subset),'NNN DALYs':subset.daly2021.sum(),
            'sample DALYs':frame.daly2021.sum(),'DALY share':100*subset.daly2021.sum()/frame.daly2021.sum(),
            'NNN population':subset.pop2021.sum(),'sample population':frame.pop2021.sum(),
            'population share':100*subset.pop2021.sum()/frame.pop2021.sum()}


def supplement3():
    fig=plt.figure(figsize=(13.2,10.2))
    gs=fig.add_gridspec(2,2,left=.14,right=.97,top=.94,bottom=.12,wspace=.58,hspace=.44)
    baseline=burden_share(B)
    ax=fig.add_subplot(gs[0,0]);panel(ax,'a','Leave out one high-burden country')
    leave=[]
    for row in B.sort_values('daly2021',ascending=False).itertuples():
        vals=burden_share(B[B.iso3.ne(row.iso3)])
        leave.append({'excluded ISO3':row.iso3,'excluded country':row.country,'excluded trajectory':row.trajectory,
                      'excluded DALYs':row.daly2021,**vals})
    leavedf=pd.DataFrame(leave);display=leavedf.head(10)
    y=np.arange(len(display))
    ax.hlines(y,baseline['DALY share'],display['DALY share'],color=SOFT,lw=2)
    ax.scatter(display['DALY share'],y,c=BURGUNDY,s=30,zorder=3)
    for j,val in enumerate(display['DALY share']):ax.text(val+1,j,f'{val:.1f}',va='center',fontsize=9)
    ax.set_yticks(y,[f'{r["excluded ISO3"]} ({r["excluded trajectory"]})' for _,r in display.iterrows()]);ax.invert_yaxis()
    ax.axvline(baseline['DALY share'],color=BURGUNDY,ls='--',lw=.9)
    ax.set_xlim(0,60);ax.set_xlabel('NNN share of remaining-panel DALYs (%)');grid(ax,'x')
    ax.text(.5,-.20,'Ten largest DALY contributors to the 168-country panel.\nAll 168 leave-one-country-out results are in source data.',transform=ax.transAxes,ha='center',va='top',fontsize=9)
    source('S3 leave one country out',leavedf)
    ordered=B.sort_values(['daly2021','iso3'],ascending=[False,True])
    cumulative=[]
    for k in range(11):
        excluded=ordered.iloc[:k]
        cumulative.append({'excluded top k':k,'excluded ISO3':', '.join(excluded.iso3),
                           'selection rule':'Descending original-panel 2021 DALY total',
                           **burden_share(ordered.iloc[k:])})
    cumulative=pd.DataFrame(cumulative)
    source('S3 cumulative high-burden omissions',cumulative)

    ax=fig.add_subplot(gs[0,1]);panel(ax,'b','Leave out one WHO region')
    regiondata=pd.DataFrame([{'excluded region':reg,'region label':RL[reg],**burden_share(B[B.region.ne(reg)])} for reg in REGIONS])
    for j,row in regiondata.iterrows():
        ax.plot([baseline['DALY share'],row['DALY share']],[j,j],color=SOFT,lw=2)
        ax.scatter(row['DALY share'],j,color=BURGUNDY,s=36,zorder=3)
        ax.text(row['DALY share']+1.3,j,f'{row["DALY share"]:.1f}',va='center',fontsize=10)
    ax.axvline(baseline['DALY share'],color=BURGUNDY,ls='--',lw=.9)
    ax.set_yticks(range(6),[f'{r["excluded region"]} (n={r["sample n"]})' for _,r in regiondata.iterrows()]);ax.invert_yaxis()
    ax.set_xlim(0,85);ax.set_xlabel('NNN share of remaining-panel DALYs (%)');grid(ax,'x')
    ax.text(.5,-.20,'n is the retained sample size; denominator is recalculated.\nDashed lines in panels a-b mark the original 45.69%.',transform=ax.transAxes,ha='center',va='top',fontsize=9)
    source('S3 leave one region out',regiondata)

    ax=fig.add_subplot(gs[1,0]);panel(ax,'c','NNN shares under alternative samples')
    geoflag=B.geo_review.eq('review_required')
    assert int(geoflag.sum())==19
    icsonly=icswide.index[icswide[[2017,2019,2021]].isin(VALID).all(axis=1)]
    cohorts=[('Primary panel',B),('Five-wave panel',DF[DF.iso3.isin(fiveids)]),
             ('ICS-valid panel',DF[DF.iso3.isin(icsonly)]),('Excluding 19 map-scope flags',B[~geoflag])]
    comparisons=pd.DataFrame([{'sample label':name,**burden_share(frame)} for name,frame in cohorts])
    for j,row in comparisons.iterrows():
        for field,color,marker,offset in [('DALY share',BURGUNDY,'o',-.1),('population share',ROSE,'s',.1)]:
            ax.scatter(row[field],j+offset,color=color,s=38,marker=marker,label=field if j==0 else None,zorder=3)
            ax.text(row[field]+.7,j+offset,f'{row[field]:.1f}',va='center',fontsize=9)
    ax.set_yticks(range(4),[f'{r["sample label"]}\n(n={r["sample n"]}; NNN={r["NNN n"]})' for _,r in comparisons.iterrows()],fontsize=9)
    ax.set_ylim(3.6,-.65);ax.set_xlim(0,65);ax.set_xlabel('NNN share of the selected sample (%)');grid(ax,'x')
    ax.legend(handles=[Line2D([],[],marker='o',ls='',color=BURGUNDY,label='DALYs'),Line2D([],[],marker='s',ls='',color=ROSE,label='Resident population 25+')],loc='lower left',bbox_to_anchor=(0,-.27),fontsize=9)
    source('S3 alternative sample shares',comparisons)

    ax=fig.add_subplot(gs[1,1]);panel(ax,'d','Which three-wave trajectories are omitted?')
    excluded_geo=B[geoflag]
    excluded_five=B[~B.iso3.isin(fiveids)]
    groups=[('Full panel\n(n=168)',B),('Map-scope flags\n(n=19)',excluded_geo),('Not five-wave\n(n=27)',excluded_five)]
    matrix=np.array([[int(g.trajectory.eq(p).sum()) for _,g in groups] for p in PATHS])
    cleanheat(ax,matrix,PATHS,[x[0] for x in groups],vmax=99)
    comp=[]
    for label,frame in groups:
        for p in PATHS:
            ids=sorted(frame.loc[frame.trajectory.eq(p),'iso3'])
            comp.append({'group':label.replace('\n',' '),'trajectory':p,'countries':len(ids),'ISO3':', '.join(ids)})
    source('S3 sample composition',pd.DataFrame(comp))
    sensitivity_note=['', '## 补充敏感性独立复算', '',
                      '按原168国样本2021 DALY总数降序逐一剔除国家，同时重算NNN分子与保留样本分母；未把剔除国家保留在分母。', '',
                      '| 累计剔除前k个国家 | 被剔除ISO3 | 保留国家数 | NNN国家数 | NNN DALY份额（%） | NNN居民人口份额（%） |',
                      '|---:|---|---:|---:|---:|---:|']
    for _,r in cumulative.iterrows():
        sensitivity_note.append(f'| {r["excluded top k"]} | {r["excluded ISO3"] or "无"} | {r["sample n"]} | {r["NNN n"]} | {r["DALY share"]:.6f} | {r["population share"]:.6f} |')
    sensitivity_note += ['', '剔除印度后NNN DALY份额由45.69%降至20.82%，因此DALY份额的幅度明显依赖大国组成；不能称其对国家剔除不敏感。累计剔除后的序列也并非单调，因为被移除国家属于不同轨迹。', '',
                         'S3逐地区留出和样本敏感性均保留各自实际分母。19项地图标记来自已有地图范围审计，并非国家ID失配；剔除它们仅为压力测试。源数据提供全部168次逐国留出及前10个大负担国家的累计剔除。', '']
    with (ROOT/'核验/独立统计核验.md').open('a',encoding='utf-8') as handle:
        handle.write('\n'.join(sensitivity_note))
    save(fig,'S3',supp=True,footer='NNN = reported ICS No in 2017, 2019 and 2021. Map-scope flags are cartographic flags, not failed country links. No uncertainty intervals are inferred.')


def captions():
    paragraphs = [
        "**Figure S1. Missing answers and analysis coverage.** (a) Unknown WHO medication answers among 194 countries; hatched cells indicate an indicator absent from that API wave. (b) Covariate coverage within the actual 181-country extraction frame: 172 complete records, six missing GDP, one missing GDP and both expenditure measures, and two unmatched to World Bank country metadata. Thirteen other WHO countries were outside extraction, not established WDI missing observations. (c) Countries retained in four prespecified models after covariate exclusions. (d) Availability bounds obtained by assigning every unknown answer to No or Yes, solely as scenarios; these are not confidence intervals. Original unknown answers remain unchanged. No indicates reported general availability below the survey threshold, not zero supply. Definitions, matching rules, and denominators appear in Supplementary methods.",
        "**Figure S2. Exploratory extension to five survey waves.** (a) All 22 observed ICS answer sequences among 141 countries with valid ICS and bronchodilator answers in every wave from 2013 to 2021. (b) Reported Yes percentages and counts in that fixed cohort. (c) Paired ICS changes in the 168-country three-wave cohort and its 141-country five-wave subset. (d) Actual ISO3-labelled sequences for 30 countries with at least two adjacent-wave answer changes, arranged in three columns. Blue-grey denotes Yes; burgundy denotes No. No intermediate values are inferred. The original 2013 and 2015 question wording has not been audited, so the extended series is exploratory. Changes describe national reported availability rather than policy timing or patient treatment. Sources and comparability limits appear in Supplementary methods.",
        "**Figure S3. Sensitivity to country and sample composition.** NNN denotes reported ICS No in 2017, 2019 and 2021. (a) NNN shares of 2021 adult asthma DALYs after individually omitting the ten largest contributors; source data include all 168 individual omissions and cumulative omissions. (b) Shares after regional exclusions; dashed lines mark the original 45.69%. (c) DALY and resident-population shares under alternative samples. (d) Trajectory counts in the full panel and omitted groups, which may overlap. Numerators and denominators are recalculated for every sample. Map-scope flags are cartographic, not failed country identifiers. Shares are sensitive to India: omission lowers the DALY share to 20.82%. Estimates cover ages 25 and older, using GBD 2023 for calendar year 2021. No uncertainty intervals are inferred without draws. Further definitions appear in Supplementary methods."
    ]
    import re
    wordcounts = [len(re.findall(r"\S+",paragraph)) for paragraph in paragraphs]
    assert all(100 <= n <= 140 for n in wordcounts), wordcounts
    target=ROOT/'报告/Supplementary captions.md'
    target.parent.mkdir(exist_ok=True,parents=True)
    target.write_text('# Supplementary figure captions\n\n'+'\n\n'.join(paragraphs)+'\n',encoding='utf-8')
    methods = """# Supplementary methods

The supplementary figures use the archived WHO CCS/GHO country-wave responses, World Bank WDI covariates, and GBD 2023 results for calendar year 2021. They do not impute missing observations or treat unknown availability as No. WHO medication reporting concerns general availability in public primary health care, defined using the survey's threshold of at least 50% of pharmacies. No means the reported threshold is not met; it does not establish zero supply. The ICS item did not explicitly restrict answers to single-agent products, and an ICS No response cannot establish absence of every anti-inflammatory treatment. National medication reporting is not age-specific. The age restriction of 25 years and older applies only to asthma DALYs and resident population; residents are not counts of patients or medicine users.

For S1a, the denominator is the 194-country WHO frame in every displayed wave. “No report” combines “No response” and “No data received”; “Don't know” remains separate. The combination-inhaler indicator is absent from the downloaded API for 2013–2019. These cells are hatched rather than coded as 194 No or unknown responses. Its 2021 counts are 84 Yes, 78 No, 24 Don't know, and eight No response. S1d evaluates only hypothetical extreme assignments of unknown answers, retaining a denominator of 194. Its endpoint pairs are 66.49–73.20% for ICS, 79.38–82.47% for bronchodilator, and 43.30–59.79% for the combination inhaler. These are arithmetic scenario bounds, not confidence intervals or substituted observations.

For S1b, the archived environmental CSV contains 905 country-year rows: 181 countries in each year from 2017 to 2021. The collection frame is the set with valid 2021 answers for both ICS and bronchodilator. The input audit JSON confirms exact ISO3 and calendar-year matching, with no filling or substitution across years and with World Bank regional aggregates excluded. The column “World Bank nonaggregate country” distinguishes source-country matching from item completeness. Cook Islands (COK) and Niue (NIU) are False and unmatched to those metadata; they are displayed as No match, not as ordinary missing source observations. Among the 179 matched countries, 172 have all four covariates; CUB, ERI, MCO, SSD, VEN, and YEM lack GDP; PRK has PM2.5 but lacks GDP, out-of-pocket share, and health expenditure. Missing patterns are therefore presented in the 181-country extraction frame, with source matching displayed separately. The other 13 WHO countries—AGO, CHN, COD, EGY, GNB, KAZ, KOR, LBR, LSO, MKD, SVK, TCD, and ZMB—were outside this extraction frame. Their absent records do not demonstrate that WDI lacks their measurements. The four indicators are EN.ATM.PM25.MC.M3, NY.GDP.PCAP.PP.KD, SH.XPD.OOPC.CH.ZS, and SH.XPD.CHEX.PP.CD.

S1c uses the model denominators recorded by the main analysis without changing eligibility. ICS models start from 181 countries with valid basic-medicine answers and retain 172 with the GDP covariate specification or 178 with the health-expenditure specification. Combination-inhaler models start from the 157 countries with valid answers for all three medicines and retain 150 or 154, respectively. The extraction-frame omission of 13 countries is not an additional covariate exclusion applied inside these already eligible samples. Exact extraction statuses and missing patterns are included as S1 source CSVs.

For S2, a country enters the 141-country panel only if both basic-medicine items have explicit Yes/No responses in all five waves. The 22 sequences are sorted lexically, and the number beside each sequence is its observed country frequency. The 30 displayed country strips have at least two changes between adjacent responses; strips are ordered by sequence and ISO3, without jitter or interpolated intermediate states. This criterion describes changing answers, not proven changes in care delivery. Paired changes use fixed denominators of either 168 or 141, not independent wave-specific samples. The 141-country values for 2017–2019, 2019–2021, and 2017–2021 are +2.13, +4.26, and +6.38 percentage points, compared with +2.98, +5.95, and +8.93 in the 168-country panel. The original 2017, 2019, and 2021 medication questions were audited separately; the original 2013 and 2015 questions have not been audited. The five-wave extension is therefore exploratory. Binary heatmaps use the same Yes and No colours as the main figures.

For S3, NNN is defined by the three ICS answers in 2017, 2019, and 2021. The baseline includes 35 NNN countries among 168, with 45.6945% of panel DALYs and 36.2061% of the resident population aged 25 and older. All 168 countries are removed individually in the source calculations; the figure shows the ten largest original-panel DALY contributors. Cumulative omissions use this same initial ranking rather than repeatedly selecting countries to maximize or minimize the result. Every removal recalculates both numerator and denominator. Regional leave-out calculations omit all panel countries in the selected WHO region. Alternative samples comprise the five-wave panel (141), the three-wave panel requiring valid ICS answers only (170), and the panel after excluding 19 inherited map-scope flags (149). The flags concern cartographic coverage, territories, islands, or boundary scope; they do not establish national-identifier failure and do not justify a corrected primary sample. Their exclusion is a stress test. Groups omitted under different restrictions can overlap.

The magnitude of burden concentration depends on composition: India's removal lowers the NNN DALY share to 20.8186%, and exclusion of the South-East Asia Region lowers it to 21.5836%. Excluding the 19 map-scope flags gives 17.5841%; the five-wave and ICS-valid alternatives give 49.4983% and 47.1120%. GBD point estimates are summed across countries. Uncertainty bounds for sums or shares are not obtained by summing marginal lower and upper limits; no such intervals are supplied because joint GBD draws are unavailable. All S3 source tables retain actual sample sizes and denominators.

Reproduction uses `代码/补充图.py`, importing the shared `代码/绘图公共.py` without altering it. The independent core audit reconstructs the 168-country sample from raw WHO answers using Python's standard library, sums raw DALY and population inputs, and checks the reported NNN statistics and paired ICS change. WDI collection status is verified against `输入数据/呼吸环境社会数据.csv` and `输入数据/呼吸环境社会核验.json`. Exact analytical tables and country lists accompany the figures in `图形/源数据`; the independent arithmetic audit is in `核验/独立统计核验.md`.
"""
    (ROOT/'报告/Supplementary methods.md').write_text(methods,encoding='utf-8')
    source('S1 caption and extraction audit',{'caption word counts':wordcounts,
        'extraction frame':181,'WHO frame':194,'not collected':13,'World Bank metadata matched':179,
        'World Bank metadata unmatched ISO3':['COK','NIU'],'complete covariates':172,
        'GDP missing only':6,'GDP and expenditure missing':1})
    print('Caption word counts:',wordcounts,flush=True)


if __name__ == '__main__':
    supplement1()
    supplement2()
    supplement3()
    captions()
