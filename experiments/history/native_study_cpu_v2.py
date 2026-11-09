"""Controlled complete native GF(2) solves with independent CPU certificate checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import subprocess
import time
from experiments.binary import fixture
from native_preflight import check_solution, write_matrix


def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation-only',action='store_true')
    parser.add_argument('--output',default='results/native-study.json')
    args=parser.parse_args();cases=[]
    for seed in (20261109,20261209):
        for family in ('uniform','banded','head'):
            for n in (512,2048):
                rows=fixture(n,12,seed,family)
                started=time.perf_counter();write_matrix(Path('build/study-matrix.bin'),rows)
                preparation_ms=(time.perf_counter()-started)*1000
                for block,tuned in ((64,False),(64,True),(256,False),(256,True)):
                    # All oracles for compatibility probes; production timing retains stage-two
                    # annihilation, SpMM preflight and an independent CPU check on every certificate.
                    oracle=args.validation_only
                    observations=1 if args.validation_only else (30 if n==512 and family=='uniform' else 3)
                    warmups=0 if args.validation_only else (5 if observations==30 else 1)
                    results=[]
                    command=['build/solve-timing','build/study-matrix.bin','build/study-output.json',str(block),str(int(tuned)),str(seed),'0',str(int(oracle))]
                    for trial in range(warmups+observations):
                        start=time.perf_counter()
                        run=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
                        wall_ms=(time.perf_counter()-start)*1000
                        if run.returncode!=0:
                            results.append(dict(trial=trial,exit_code=run.returncode,process_wall_ms=wall_ms,
                                failure_output=run.stdout.replace(str(Path.home()),'HOME')))
                            break
                        value=json.loads(Path('build/study-output.json').read_text())
                        check_start=time.perf_counter();rank=check_solution(rows,n,value['solutions'])
                        cpu_check_ms=(time.perf_counter()-check_start)*1000
                        if trial>=warmups:
                            phase_lines=[line for line in run.stdout.splitlines() if '[STATS]' in line and '[BWSolver]' in line]
                            phases={}
                            for line in phase_lines:
                                match=re.search(r'(Stage [123]|AutoTune)\s*:\s*(?:(\d+)m\s*)?(?:(\d+)s\s*)?([\d.]+)ms',line)
                                if match:
                                    phases[match[1]]=60000*int(match[2] or 0)+1000*int(match[3] or 0)+float(match[4])
                            assert all(f'Stage {stage}' in phases for stage in (1,2,3)),phase_lines
                            results.append(dict(trial=trial-warmups,exit_code=0,process_wall_ms=wall_ms,
                                independent_python_check_ms=cpu_check_ms,independent_solution_rank=rank,certificate=value,
                                native_phase_ms=phases,native_phase_log=phase_lines))
                    cases.append(dict(n=n,degree=12,seed=seed,family=family,block=block,tuned=tuned,oracle=oracle,
                        warmups=warmups,requested_observations=observations,matrix_file_sha256=hashlib.sha256(Path('build/study-matrix.bin').read_bytes()).hexdigest(),
                        export_wall_ms=preparation_ms,results=results))
                    print('CASE',seed,family,n,block,tuned,'exit',results[-1]['exit_code'],flush=True)
                    # Retain partial campaigns after each case, including legitimate unsuccessful solves.
                    record=dict(utc=datetime.now(timezone.utc).isoformat(),cases=cases,validation_only=args.validation_only,
                        source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['native_study.py','native_preflight.py','experiments/binary.py','native/solve.cpp','build_timing.py','patches/batch-reconstruction.patch']},
                        binary_sha256=hashlib.sha256(Path('build/solve-timing').read_bytes()).hexdigest(),
                        timer_scope='Process wall includes launch, reading CSR fixture, constructor, tuning, stages 1-3, native verification and output. Native separate timers retained. Python validation and export separately recorded. Timings do not describe factoring or mining revenue.')
                    Path(args.output).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
