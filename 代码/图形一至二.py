"""Asymmetric information hierarchy based on the supplied reference article."""
from 绘图公共 import *
from matplotlib.patches import Rectangle,FancyArrowPatch

def fig1():
    fig=plt.figure(figsize=(11.2,8.5))
    ax=fig.add_axes([.065,.705,.90,.225]);panel(ax,'a','Sources linked by country and survey year');ax.set_axis_off()
    cards=[(.015,'WHO capacity surveys','194 country records','2013–2021 · five survey waves',NO),(.36,'GBD 2023 frozen export','204 countries and territories','Adult asthma DALYs and population, 25+',YES),(.705,'World Bank indicators','181-country extraction frame','Environment and economic context, 2017–2021',GOLD)]
    for x,title,large,detail,c in cards:
        ax.add_patch(Rectangle((x,.38),.28,.60,facecolor='white',edgecolor='#C5C8CD',lw=.6))
        ax.plot([x,x+.28],[.98,.98],lw=2.5,color=c,solid_capstyle='butt')
        ax.text(x+.014,.825,title,fontsize=10.5,fontweight='bold',va='center')
        ax.text(x+.014,.62,large,fontsize=12,va='center')
        ax.text(x+.014,.465,detail,fontsize=8.6,va='center')
        ax.add_patch(FancyArrowPatch((x+.14,.36),(.50,.11),arrowstyle='-',lw=.7,color='#A6AAB0'))
    ax.text(.50,.055,'ISO3 + year  →  distinct repeated and cross-sectional samples',ha='center',va='center',fontsize=10)
    ax.set_xlim(0,1);ax.set_ylim(0,1)
    ax=fig.add_axes([.065,.355,.56,.275]);panel(ax,'b','Geography of the repeated panel')
    world(ax,{r.iso3:'Panel' if r.balanced168 else 'Other' for r in DF.itertuples()},{'Panel':NO,'Other':'#D8DCE1'})
    ax.legend(handles=[Patch(color=NO,label='Repeated panel (168)'),Patch(color='#D8DCE1',label='Other WHO records')],loc='lower center',bbox_to_anchor=(.5,-.08),ncol=2,fontsize=8.8,handlelength=1.0,columnspacing=1.4)
    ax=fig.add_axes([.752,.355,.211,.275]);panel(ax,'c','Overlapping analysis samples')
    labels=['Three-wave panel','Five-wave panel','ICS-only panel','Three medicines, 2021'];vals=[168,141,170,157]
    ax.barh(range(4),vals,height=.32,color=[NO,'#ACBAC3',YES,GOLD]);ax.set_yticks(range(4),labels,fontsize=9)
    for y,v in enumerate(vals):ax.text(v+3,y,str(v),va='center',fontsize=10)
    ax.set_xlim(0,200);ax.set_xticks([0,100,200]);ax.set_xlabel('Countries');ax.invert_yaxis();grid(ax,'x')
    ax=fig.add_axes([.065,.135,.9,.135]);panel(ax,'d','Country-level completeness across five waves')
    order=DF.assign(rank=DF.region.map({r:i for i,r in enumerate(REGIONS)})).sort_values(['rank','iso3']);ids=order.iso3.tolist();years=[2013,2015,2017,2019,2021]
    raw=PANEL.set_index(['Country code','Year']);arr=np.zeros((5,len(ids)),int);rows=[]
    for j,iso in enumerate(ids):
        for i,y in enumerate(years):
            rr=raw.loc[(iso,y)];k=int(rr['吸入激素'] in VALID)+int(rr['支气管扩张剂'] in VALID);arr[i,j]=k
            rows.append({'iso3':iso,'region':order.iloc[j].region,'year':y,'valid_basic_items':k})
    ax.imshow(arr,aspect='auto',interpolation='nearest',cmap=colors.ListedColormap(['#E4E6E9','#D7B494',YES]),vmin=0,vmax=2)
    ax.set_yticks(range(5),years);ax.set_xticks([]);ax.tick_params(length=0)
    start=0
    for reg in REGIONS:
        size=int((order.region==reg).sum());ax.axvline(start-.5,color='white',lw=1.5)
        ax.text(start+(size-1)/2,5.04,RL[reg].replace('Eastern Mediterranean','Eastern\nMediterranean').replace('South-East Asia','South-East\nAsia').replace('Western Pacific','Western\nPacific'),ha='center',va='top',fontsize=8.6,clip_on=False);start+=size
    for s in ax.spines.values():s.set_visible(False)
    figlegend(fig,[('Both basic answers valid',YES),('One valid answer','#D7B494'),('Neither valid','#E4E6E9')],y=.027,ncol=3)
    source('Figure 1 country completeness',pd.DataFrame(rows));source('Figure 1 analysis samples',pd.DataFrame({'sample':labels,'countries':vals}));source('Figure 1 geography',DF[['iso3','country','region','balanced168']])
    save(fig,'Figure 1')

def fig2():
    fig=plt.figure(figsize=(11.2,8.7))
    ax=fig.add_axes([.068,.555,.605,.355]);panel(ax,'a','Reported ICS availability across three waves');flow(ax)
    ax=fig.add_axes([.745,.555,.205,.355]);panel(ax,'b','Eight observed sequences');ax.set_axis_off()
    counts=B.trajectory.value_counts().reindex(PATHS,fill_value=0)
    ax.text(.80,1.00,'Countries',ha='center',fontsize=9)
    for i,p in enumerate(PATHS):
        y=.92-i*.12
        ax.add_patch(Rectangle((0,y-.025),.08,.05,color=PC[p],lw=0))
        ax.text(.16,y,p,va='center',fontsize=10.5)
        ax.text(.82,y,f'{counts[p]}',va='center',ha='center',fontsize=11)
        ax.plot([.10,.98],[y-.057,y-.057],color='#E4E6E9',lw=.45)
    ax.text(.02,-.055,'N: No     Y: Yes',fontsize=9.5)
    fig.text(.047,.469,'c',fontsize=13.5,fontweight='bold');fig.text(.068,.47,'Availability within the same countries in each WHO region',fontsize=11.5)
    regional=[]
    for k,reg in enumerate(REGIONS):
        i,j=divmod(k,3);x=.078+j*.306;y=.282-i*.171
        a=fig.add_axes([x,y,.238,.116]);g=B[B.region.eq(reg)];v=[g[f'ics{yr}'].eq('Yes').mean()*100 for yr in [2017,2019,2021]]
        a.plot([2017,2019,2021],v,color=YES,lw=1.4,marker='o',ms=4,mec='white',mew=.45)
        a.set(xticks=[2017,2019,2021],ylim=(-5,105),yticks=[0,50,100],xlim=(2016.8,2021.25));a.tick_params(labelsize=8.5,length=2);grid(a)
        if j==0:a.set_ylabel('Yes (%)',fontsize=9)
        else:a.tick_params(labelleft=False)
        name=RL[reg];a.text(0,1.10,f'{name}  (n={len(g)})',transform=a.transAxes,fontsize=9.5)
        a.text(2021.12,v[-1],f'{v[-1]:.0f}',va='center',ha='left',fontsize=8.5,bbox={'facecolor':'white','edgecolor':'none','pad':.1})
        regional.extend({'region':reg,'n':len(g),'year':yr,'yes_percent':vv} for yr,vv in zip([2017,2019,2021],v))
    fig.text(.17,.044,'21 countries: No → Yes',ha='center',fontsize=10.5)
    fig.text(.51,.044,'6 countries: Yes → No',ha='center',fontsize=10.5)
    fig.text(.84,.044,'Net change: +8.93 pp',ha='center',fontsize=10.5,fontweight='bold')
    fig.text(.51,.013,'2017–2021 paired comparison; exact McNemar p=0.0059, Holm-adjusted p=0.0178.',ha='center',fontsize=8.8)
    source('Figure 2 sequences',B[['iso3','country','region','trajectory','ics2017','ics2019','ics2021']]);source('Figure 2 region microplots',pd.DataFrame(regional))
    save(fig,'Figure 2')

if __name__=='__main__':
    fig1();fig2()
    (ROOT/'报告/Figures 1–2 captions.md').write_text('''# Figures 1–2 captions

**Figure 1. Data linkage, sample geography and survey completeness.** (a) The three sources and their distinct country frames. (b) The 168-country repeated panel. (c) Overlapping analysis samples; these are not a nested flow. (d) Every WHO country record across five waves, grouped by region; columns retain the same country order. Completeness refers to explicit Yes/No answers for ICS and bronchodilators, irrespective of the answer itself. The World Bank extraction frame does not cover all WHO records. Country-level map values are displayed without spatial re-aggregation.

**Figure 2. Country trajectories in reported ICS availability.** (a) Observed three-wave pathways, with ribbon widths proportional to country counts. (b) Counts for all eight sequences and matching ribbon colours. (c) Six regional small multiples using the same countries at each wave and a shared percentage scale. The bottom comparison gives the two directions of change between 2017 and 2021. N and Y denote reported No and Yes, not uninterrupted supply between surveys. All analyses use the fixed 168-country panel; pp denotes percentage points.
''',encoding='utf8')
