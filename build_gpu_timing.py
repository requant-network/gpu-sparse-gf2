"""Build the checked harness with the GPU generator explicitly selected and phase statistics."""
import argparse,hashlib,json,pathlib,subprocess

p=argparse.ArgumentParser(description=__doc__);p.add_argument('upstream',type=pathlib.Path);p.add_argument('upstream_build',type=pathlib.Path);p.add_argument('--nvcc',default='nvcc');a=p.parse_args()
up=a.upstream.resolve();ub=a.upstream_build.resolve()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=up,text=True).strip()=='ebfe814b759803f61771b36d1fd197b71b751d1d'
previous=json.loads(pathlib.Path('results/native-build.json').read_text())
for name,digest in previous['source_sha256'].items():assert hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()==digest
source=pathlib.Path('native/solve.cpp').read_text()
assert source.count('log.min_severity_cout=LOG_INFO')==1 and source.count('cfg.solve_transposed=false;')==1
source=source.replace('log.min_severity_cout=LOG_INFO','log.min_severity_cout=LOG_STATS')
source=source.replace('cfg.solve_transposed=false;','cfg.solve_transposed=false;cfg.stage2_gpu_mode=true;')
generated=pathlib.Path('build/solve-gpu-timing.cpp');generated.write_text(source,encoding='utf-8',newline='\n')
inputs=['build/solution-corrected.o','build/liblingen-corrected.a']
command=[a.nvcc,'-O3','-std=c++17','-arch=sm_120','-rdc=true','-Xcompiler=-fopenmp',str(generated)]
command+=['-I'+str(up/name) for name in ('include','src','cuda_spmm/include','utils')]+['-I'+str(ub/'generated')]
command+=inputs+[str(ub/'cuda_spmm/libspmm_core.a'),str(ub/'cuda_spmm/libhpc_logger.a'),'-lcudart','-lgomp','-lpthread','-ldl','-o','build/solve-gpu-timing']
subprocess.run(command,check=True)
record=dict(upstream_revision=previous['upstream_revision'],stage2_backend='gpu',
    source_sha256={name:hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() for name in ('build_gpu_timing.py','native/solve.cpp','patches/batch-reconstruction.patch')},
    generated_harness_sha256=hashlib.sha256(generated.read_bytes()).hexdigest(),
    input_objects_sha256={name:hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest() for name in inputs},
    binary_sha256=hashlib.sha256(pathlib.Path('build/solve-gpu-timing').read_bytes()).hexdigest(),
    command=[s.replace(str(up),'UPSTREAM').replace(str(ub),'UPSTREAM_BUILD') for s in command],
    scope='Explicit stage2_gpu_mode=true and LOG_STATS. Same operator, correction, oracle controls and independent certificate checks. Compare with the retained CPU-generator control; do not infer backend from GPU use in annihilation alone.')
pathlib.Path('results/gpu-timing-build.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
