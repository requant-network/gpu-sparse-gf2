"""CPU replay of follow-up evidence, provenance and derived timing summaries."""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median
assert __debug__
PATTERNS = ('scaling-*.json',)
paths=sorted(set(p for pattern in PATTERNS for p in Path('results').glob(pattern)))
assert len(paths)==2,(len(paths),[p.name for p in paths])
records={p.name:json.loads(p.read_text()) for p in paths}
def binding(name,expected,result=False):
 p=(Path('results')/name) if result else Path(name)
 assert not Path(name).is_absolute() and ':' not in name and '..' not in Path(name).parts
 assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,(p,expected)
def provenance(r):
 if isinstance(r,dict):
  for key,v in r.items():
   if key in ('source_sha256','artifacts_sha256','public_artifacts_sha256','result_sha256'):
    for name,expected in v.items():binding(name,expected,key=='result_sha256')
   elif isinstance(v,(dict,list)):provenance(v)
 elif isinstance(r,list):
  for v in r:provenance(v)
for r in records.values():provenance(r)
from experiments.binary import fixture
from native_preflight import check_solution
for r in records.values():
 assert not r['pilot'] and len(r['cases'])==18
 matrices={}
 for c in r['cases']:
  key=(c['n'],c['family'],c['seed'])
  if key not in matrices:matrices[key]=fixture(c['n'],12,c['seed'],c['family'])
  for o in c['observations']:
   if not o['exit_code']:
    assert o['independently_valid']
    assert check_solution(matrices[key],c['n'],o['certificate']['solutions'])==o['independent_solution_rank']
   else:assert not o['independently_valid'] and o.get('failure_output')

rows=[]
def timings(value,labels,route=''):
 if isinstance(value,list):
  assert len(value)==30 and all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in value),(labels,route)
  rows.append(dict(**labels,variant_scope=route,median_ms=median(value),p95_ms=sorted(value)[28],repetitions=len(value)))
 elif isinstance(value,dict):
  for key,v in value.items():timings(v,labels,(route+'/' if route else '')+key)
for name,r in records.items():
 for index,c in enumerate(r.get('cases',[])):
  labels=dict(file=name,case=index,seed=c.get('seed',r.get('seed','')),**{key:c.get(key,'') for key in ('application','n','m','k','p','columns','steps','payload_bytes','batch','variant','pattern')})
  v=c.get('result',c)
  for key in ('samples','samples_ms','resident_graph_device_ms'):
   if isinstance(v.get(key),(dict,list)):timings(v[key],labels,key)
for name,r in records.items():
 for c in r['cases']:
  measured=[o for o in c['observations'] if not o['warmup'] and o['exit_code']==0 and o['independently_valid']]
  values=[o['process_wall_ms'] for o in measured]
  phases={phase:median([o['native_phase_ms'][phase] for o in measured if phase in o['native_phase_ms']]) for phase in ('Stage 1','Stage 2','Stage 3','AutoTune') if any(phase in o['native_phase_ms'] for o in measured)}
  rows.append(dict(file=name,seed=c['seed'],n=c['n'],family=c['family'],nonzeros=c['nonzeros'],backend=c['backend'],block=c['block'],tuned=c['tuned'],
                   measured_successes=len(values),requested=c['requested_observations'],last_exit_code=c['observations'][-1]['exit_code'],
                   process_median_ms=median(values) if values else '',process_max_ms=max(values) if values else '',
                   native_complete_median_ms=median(o['certificate']['complete_verified_wall_ms'] for o in measured) if values else '',
                   **{phase.replace(' ','_')+'_median_ms':phases.get(phase,'') for phase in ('Stage 1','Stage 2','Stage 3','AutoTune')}))
if rows:
 with Path('results/followup-summary.csv').open('w',newline='') as out:
  writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
print(len(records),'follow-up records validated;',len(rows),'median/p95 timing rows')
