"""Relink the checked harness with native statistics enabled for phase attribution."""
import argparse,hashlib,json,pathlib,subprocess

p=argparse.ArgumentParser(description=__doc__);p.add_argument('upstream',type=pathlib.Path);p.add_argument('upstream_build',type=pathlib.Path);p.add_argument('--nvcc',default='nvcc');a=p.parse_args()
up=a.upstream.resolve();ub=a.upstream_build.resolve()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()=='ebfe814b759803f61771b36d1fd197b71b751d1d'
previous=json.loads(pathlib.Path('results/native-build.json').read_text())
for name,digest in previous['source_sha256'].items():assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==digest
source=pathlib.Path('native/solve.cpp').read_text();assert source.count('log.min_severity_cout=LOG_INFO')==1
generated=pathlib.Path('build/solve-timing.cpp');generated.write_text(source.replace('log.min_severity_cout=LOG_INFO','log.min_severity_cout=LOG_STATS'),encoding='utf-8',newline='\n')
inputs=['build/solution-corrected.o','build/liblingen-corrected.a']
command=[a.nvcc,'-O3','-std=c++17','-arch=sm_120','-rdc=true','-Xcompiler=-fopenmp',str(generated)]
command+=['-I'+str(up/name) for name in ('include','src','cuda_spmm/include','utils')]+['-I'+str(ub/'generated')]
command+=inputs+[str(ub/'cuda_spmm/libspmm_core.a'),str(ub/'cuda_spmm/libhpc_logger.a'),'-lcudart','-lgomp','-lpthread','-ldl','-o','build/solve-timing']
subprocess.run(command,check=True)
record=dict(upstream_revision=previous['upstream_revision'],source_sha256={name:hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() for name in ('build_timing.py','native/solve.cpp','patches/batch-reconstruction.patch')},
    generated_harness_sha256=hashlib.sha256(generated.read_bytes()).hexdigest(),
    input_objects_sha256={name:hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() for name in inputs},
    binary_sha256=hashlib.sha256(pathlib.Path('build/solve-timing').read_bytes()).hexdigest(),
    command=[s.replace(str(up),'UPSTREAM').replace(str(ub),'UPSTREAM_BUILD') for s in command],scope='Only the log threshold changes from INFO to STATS; arithmetic, oracles, independent checks and configuration remain unchanged.')
pathlib.Path('results/timing-build.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
