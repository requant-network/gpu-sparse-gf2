"""Plot distinct full-solve and product experiments with per-cohort median ranges."""
import csv,pathlib,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

native=list(csv.DictReader(open('results/native-summary.csv',encoding='utf-8')))
products=list(csv.DictReader(open('results/products-summary.csv',encoding='utf-8')))
fig,axes=plt.subplots(1,2,figsize=(12,5.2),layout='constrained')
for j,(backend,label,color) in enumerate((('cpu','CPU generator control','#8da5bc'),('gpu','GPU-hybrid generator','#187f94'))):
    groups=[[float(r['process_wall_median_ms']) for r in native if r['stage2_backend']==backend and r['n']=='512' and r['family']=='uniform' and int(r['block'])==b and r['tuned']==str(t)] for b,t in ((64,False),(64,True),(256,False),(256,True))]
    assert all(len(v)==2 for v in groups);m=[statistics.mean(v) for v in groups]
    axes[0].bar([i+(j-.5)*.32 for i in range(4)],m,.31,color=color,label=label,
        yerr=[[a-min(v) for a,v in zip(m,groups)],[max(v)-a for a,v in zip(m,groups)]],capsize=2)
axes[0].set_xticks(range(4),('64 / raw','64 / tuned','256 / raw','256 / tuned'),rotation=12)
axes[0].set_yscale('log');axes[0].set_ylabel('Complete process milliseconds');axes[0].set_title('Native solve · 512-row uniform matrix',loc='left',fontsize=12)
axes[0].legend(frameon=False,fontsize=9)
for j,(mode,color) in enumerate((('csr','#345e88'),('warp_csr','#9eb2c5'),('ell','#168c91'))):
    groups=[[float(r['resident_graph_ms_median']) for r in products if r['n']=='16384' and r['family']==family and r['method']==mode] for family in ('uniform','banded','head')]
    assert all(len(v)==2 for v in groups);m=[statistics.mean(v) for v in groups]
    axes[1].bar([i+(j-1)*.24 for i in range(3)],m,.23,color=color,label=mode,
        yerr=[[a-min(v) for a,v in zip(m,groups)],[max(v)-a for a,v in zip(m,groups)]],capsize=2)
axes[1].set_xticks(range(3),('Uniform','Banded','Heavy head'));axes[1].set_ylabel('128-product graph milliseconds')
axes[1].set_title('Original products · 16,384 rows / 256-bit block',loc='left',fontsize=12);axes[1].legend(frameon=False,fontsize=9)
for ax in axes:
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.suptitle('Sparse GF(2): complete solver costs and separate layout experiments',fontsize=15)
fig.supxlabel('Requant Network research · Bars: midpoint of two input-cohort medians; whiskers: their range, not confidence intervals.\nBoth native paths use GPU stages 1/3. Original layouts are not integrated into that solver.',fontsize=9)
pathlib.Path('figures').mkdir(exist_ok=True);fig.savefig('figures/sparse-study.png',dpi=180);fig.savefig('figures/sparse-study.svg')
svg=pathlib.Path('figures/sparse-study.svg');svg.write_bytes(svg.read_bytes().replace(b'\r\n',b'\n'))
print('Rendered distinct native-solve and sparse-product scopes')
