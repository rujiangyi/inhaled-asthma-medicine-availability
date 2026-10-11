from pathlib import Path
import sys,json
import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import Patch,PathPatch
from matplotlib.path import Path as MPath
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'图形'
MAIN=FIG/'正文';SUPP=FIG/'补充';SOURCE=FIG/'源数据';PREVIEW=FIG/'预览'
for p in [MAIN,SUPP,SOURCE,PREVIEW]:p.mkdir(exist_ok=True,parents=True)
fm.findfont('Times New Roman',fallback_to_default=False)
plt.rcParams.update({'font.family':'Times New Roman','font.size':11,'axes.titlesize':12.5,'axes.labelsize':11,'xtick.labelsize':10,'ytick.labelsize':10,'text.color':'black','axes.labelcolor':'black','axes.edgecolor':'#70777E','xtick.color':'black','ytick.color':'black','axes.linewidth':.65,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white','figure.facecolor':'white','legend.frameon':False,'legend.fontsize':10,'hatch.linewidth':.5})
plt.rcParams.update({'mathtext.fontset':'custom','mathtext.rm':'Times New Roman','mathtext.it':'Times New Roman:italic','mathtext.bf':'Times New Roman:bold','mathtext.sf':'Times New Roman','mathtext.tt':'Times New Roman','mathtext.cal':'Times New Roman','mathtext.fallback':None})
plt.rcParams.update({'axes.titlesize':11.5,'axes.labelsize':10.5,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9.5,'axes.edgecolor':'#72767C','axes.linewidth':.55})
YES='#4F7899';NO='#8C2D4B';UNKNOWN='#CED1D6';GOLD='#C99961';PALE='#F2F3F5';INK='#273A46'
CMP=colors.LinearSegmentedColormap.from_list('burgundy',['#FCF6F7','#DFB8C4','#B66780','#78223F'])
PATHS=['NNN','NNY','NYN','NYY','YNN','YNY','YYN','YYY']
PC={'NNN':NO,'NNY':'#C99961','NYN':'#C56882','NYY':'#7F9FAE','YNN':'#AA718F','YNY':'#9FAF83','YYN':'#DBA7B6','YYY':YES}
REGIONS=['AFR','AMR','EMR','EUR','SEAR','WPR']
RL={'AFR':'Africa','AMR':'Americas','EMR':'Eastern Mediterranean','EUR':'Europe','SEAR':'South-East Asia','WPR':'Western Pacific'}
DF=pd.read_csv(ROOT/'表格/国家分析表.csv')
DF['balanced168']=DF['balanced168'].astype(str).str.lower().eq('true')
B=DF[DF.balanced168].copy()
PANEL=pd.read_csv(ROOT/'输入数据/呼吸国家轮次.csv')
GBD=pd.read_csv(ROOT/'输入数据/成人哮喘数据.csv')
VALID=['Yes','No']
def state(x):return x if x in VALID else 'Unknown'
def panel(ax,letter,title):
    ax.set_title(title,loc='left',y=1.0,pad=10,fontweight='normal')
    ax.annotate(letter,xy=(0,1),xycoords='axes fraction',xytext=(-18,10),textcoords='offset points',ha='right',va='baseline',fontsize=13.5,fontweight='bold',color='black',annotation_clip=False)
def grid(ax,which='y'):
    ax.set_axisbelow(True);ax.grid(axis=which,color='#E7E9EC',lw=.55)
def source(name,data):
    if isinstance(data,pd.DataFrame):data.to_csv(SOURCE/(name+'.csv'),index=False,encoding='utf-8-sig')
    else:(SOURCE/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding='utf8')
def save(fig,name,supp=False,footer=None):
    if footer:fig.text(.5,.012,footer,ha='center',va='bottom',fontsize=9)
    out=SUPP if supp else MAIN
    for ext in ['pdf','svg','png']:
        fig.savefig(out/(name+'.'+ext),dpi=320,bbox_inches='tight',pad_inches=.06)
    fig.savefig(PREVIEW/(name+'.png'),dpi=120,bbox_inches='tight',pad_inches=.05)
    plt.close(fig);print(name,'saved',flush=True)
def figlegend(fig,items,y=.06,ncol=None):
    handles=[Patch(facecolor=c,edgecolor='white',label=t) for t,c in items]
    return fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,y),ncol=ncol or len(handles),columnspacing=1.7,handlelength=1.4)
def heat(ax,array,rows,cols,fmt='d',vmax=None,cmap=CMP,annot=True):
    a=np.asarray(array,dtype=float);maxv=float(vmax if vmax is not None else np.nanmax(a))
    im=ax.imshow(a,cmap=cmap,vmin=0,vmax=max(1,maxv),aspect='auto')
    ax.set_xticks(range(len(cols)),cols);ax.set_yticks(range(len(rows)),rows)
    ax.tick_params(length=0,pad=6)
    ax.set_xticks(np.arange(-.5,len(cols),1),minor=True);ax.set_yticks(np.arange(-.5,len(rows),1),minor=True)
    ax.grid(which='minor',color='white',lw=1.2);ax.tick_params(which='minor',length=0)
    for s in ax.spines.values():s.set_visible(False)
    if annot:
        for (i,j),v in np.ndenumerate(a):
            text=f'{int(v)}' if fmt=='d' else format(v,fmt)
            ax.text(j,i,text,ha='center',va='center',fontsize=10,color='white' if maxv and v/maxv>.60 else 'black')
    return im

GEO=json.loads((ROOT/'输入数据/地图/世界简化边界.geojson').read_text(encoding='utf8'))
PROJ=Transformer.from_crs('EPSG:4326','+proj=robin +datum=WGS84 +units=m +no_defs',always_xy=True)
def world(ax,values,palette=None,cmap=CMP,norm=None):
    polys=[];fills=[]
    for f in GEO['features']:
        if f['properties']['iso3']=='ATA':continue
        v=values.get(f['properties']['iso3'],None)
        if palette is not None:color=palette.get(v,PALE)
        elif v is None or not np.isfinite(v):color=PALE
        else:color=cmap(norm(v))
        geo=f['geometry'];parts=geo['coordinates'] if geo['type']=='MultiPolygon' else [geo['coordinates']]
        for poly in parts:
            pts=np.asarray(poly[0]);xx,yy=PROJ.transform(pts[:,0],pts[:,1]);polys.append(np.column_stack([xx,yy]));fills.append(color)
    ax.add_collection(PolyCollection(polys,facecolors=fills,edgecolors='#ABB0B5',linewidths=.22,rasterized=False))
    ax.set(xlim=(-17400000,17400000),ylim=(-6600000,8700000));ax.set_aspect('equal');ax.set_anchor('N');ax.set_axis_off()
    return ax
def flow(ax,frame=B):
    counts=frame['trajectory'].value_counts().reindex(PATHS,fill_value=0)
    n=int(counts.sum());height=168;gaps=9;offsets={};order={}
    for j in range(3):
        order[j]=sorted(PATHS,key=lambda p:(p[j]=='Y',p))
        cur=0
        for ss in ['N','Y']:
            for p in order[j]:
                if p[j]!=ss:continue
                offsets[j,p]=(cur,cur+counts[p]);cur+=counts[p]
            if ss=='N':cur+=gaps
    for p in PATHS:
        if not counts[p]:continue
        for j in range(2):
            x0=j+.07;x1=j+1-.07;a,b=offsets[j,p];c,d=offsets[j+1,p]
            vertices=[(x0,a),(x0+.43,a),(x1-.43,c),(x1,c),(x1,d),(x1-.43,d),(x0+.43,b),(x0,b),(x0,a)]
            codes=[MPath.MOVETO,MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.LINETO,MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MPath(vertices,codes),facecolor=PC[p],edgecolor='white',lw=.25,alpha=.84))
    for j in range(3):
        for ss,col in [('N',NO),('Y',YES)]:
            relevant=[offsets[j,p] for p in PATHS if p[j]==ss and counts[p]>0];lo=min(a for a,b in relevant);hi=max(b for a,b in relevant)
            ax.bar(j,hi-lo,bottom=lo,width=.12,color=col,edgecolor='white',lw=.6)
            ax.text(j,(hi+lo)/2,f'{ss}\n{int(hi-lo)}',ha='center',va='center',color='white',fontsize=10,fontweight='bold')
    ax.set_xlim(-.18,2.18);ax.set_ylim(n+gaps+3,-3);ax.set_xticks([0,1,2],['2017','2019','2021']);ax.set_yticks([])
    ax.tick_params(axis='x',length=0,pad=8)
    for s in ax.spines.values():s.set_visible(False)
