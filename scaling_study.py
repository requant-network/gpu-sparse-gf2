"""Larger characterized complete solves with retained resource/verification failures."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from experiments.binary import fixture
from native_preflight import write_matrix,check_solution


def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seed',type=int,default=20261112)
    parser.add_argument('--output',default='results/scaling-study.json');parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args();cases=[]
    profiles=[(8192,'uniform')] if args.pilot else [(n,family) for n in (8192,32768) for family in ('uniform','head')]
    for n,family in profiles:
        begin=time.perf_counter();rows=fixture(n,12,args.seed,family);matrix=Path('build/scaling-matrix.bin');write_matrix(matrix,rows)
        preparation_ms=(time.perf_counter()-begin)*1000;matrix_hash=hashlib.sha256(matrix.read_bytes()).hexdigest()
        degree=[len(row) for row in rows]
        configurations=[('gpu',64,False),('gpu',64,True),('gpu',128,True),('gpu',256,True)]
        if n==8192 and family=='uniform':configurations += [('cpu',64,True),('cpu',256,True)]
        for backend,block,tuned in configurations:
            executable=Path('build/solve-gpu-timing' if backend=='gpu' else 'build/solve-timing')
            observations=[];warmups=0 if args.pilot else 1;requested=1 if args.pilot else 3
            for trial in range(warmups+requested):
                command=[str(executable),str(matrix),'build/scaling-output.json',str(block),str(int(tuned)),str(args.seed),'0','0']
                start=time.perf_counter()
                try:run=subprocess.run(command,capture_output=True,text=True,timeout=180)
                except subprocess.TimeoutExpired as error:
                    output=error.stdout or ''
                    if isinstance(output,bytes):output=output.decode(errors='replace')
                    run=subprocess.CompletedProcess(command,124,stdout=output,stderr='timeout180s')
                elapsed=(time.perf_counter()-start)*1000
                observation=dict(trial=trial-warmups,warmup=trial<warmups,exit_code=run.returncode,process_wall_ms=elapsed,
                                 independently_valid=False)
                if run.returncode==0:
                    value=json.loads(Path('build/scaling-output.json').read_text());begin=time.perf_counter()
                    try:
                        rank=check_solution(rows,n,value['solutions']);observation.update(independently_valid=True,independent_solution_rank=rank)
                    except (AssertionError,ValueError) as error:observation['certificate_rejection']=str(error)
                    observation.update(certificate=value,independent_python_check_ms=(time.perf_counter()-begin)*1000)
                phase_lines=[line for line in run.stdout.splitlines() if '[STATS]' in line and '[BWSolver]' in line]
                phases={}
                for line in phase_lines:
                    match=re.search(r'(Stage [123]|AutoTune)\s*:\s*(?:(\d+)m\s*)?(?:(\d+)s\s*)?([\d.]+)ms',line)
                    if match:phases[match[1]]=60000*int(match[2] or 0)+1000*int(match[3] or 0)+float(match[4])
                observation.update(native_phase_ms=phases,native_phase_log=phase_lines)
                if run.returncode or not observation['independently_valid']:
                    observation['failure_output']='\n'.join((run.stdout+run.stderr).splitlines()[-50:]).replace(str(Path.home()),'HOME')
                observations.append(observation)
                if run.returncode or not observation['independently_valid']:break
            cases.append(dict(n=n,family=family,degree_parameter=12,nullity_construction=8,seed=args.seed,backend=backend,block=block,tuned=tuned,
                              row_degree_min=min(degree),row_degree_max=max(degree),nonzeros=sum(degree),
                              matrix_file_sha256=matrix_hash,preparation_ms=preparation_ms,warmups=warmups,requested_observations=requested,
                              binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),observations=observations))
            record=dict(utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,pilot=args.pilot,cases=cases,per_process_timeout_seconds=180,
                        source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
                            ('scaling_study.py','native_study.py','native_preflight.py','experiments/binary.py','native/solve.cpp','build_timing.py','build_gpu_timing.py','patches/batch-reconstruction.patch')},
                        scope='Controlled sparse8192/32768-row matrices with explicit uniform/heavy-head degree distribution and planted nullspace. Same pinned corrected native solver, explicit CPU/GPU-hybrid generator, tuned/untuned block choices. All existing configured annihilation/SpMM/initializer cross-checks and independent full CPU residual/independence checks retained. Complete fresh-process costs include validation; matrix generation/export and Python check separate. One warmup/three observations for expensive complete solves;180s resource cap and all failures retained. No full factorization or cryptographic-hardness claim.')
            Path(args.output).write_text(json.dumps(record,indent=2)+'\n')
            last=observations[-1];print(args.seed,n,family,backend,block,tuned,'exit',last['exit_code'],'valid',last['independently_valid'],'wall_ms',round(last['process_wall_ms'],2),flush=True)


if __name__=='__main__':main()
