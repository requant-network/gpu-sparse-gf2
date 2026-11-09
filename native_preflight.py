"""Check the corrected native solver and its upstream golden run with all oracles."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from experiments.binary import fixture, verify


def check_solution(rows, n, solutions):
    packed=[sum(1<<j for j in row) for row in rows];basis={}
    for words in solutions:
        v=sum(int(word)<<(64*i) for i,word in enumerate(words))
        assert verify(packed,n,v), 'Independent CPU A*x failed'
        while v:
            p=v.bit_length()-1
            if p in basis:v^=basis[p]
            else:basis[p]=v;break
        assert v, 'Linearly dependent certificate'
    assert solutions
    return len(basis)


def write_matrix(path, rows):
    with path.open('wb') as output:
        output.write(struct.pack('<II',0x32464752,len(rows)))
        for row in rows:output.write(struct.pack('<I',len(row))+struct.pack('<'+'I'*len(row),*row))


def main():
    assert __debug__
    rows=fixture(512,12,20261109,'uniform');write_matrix(Path('build/preflight.bin'),rows)
    command=['build/solve-corrected','build/preflight.bin','build/preflight.json','64','0','20261109','0','1']
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
    assert result.returncode==0,result.stdout[-6000:]
    certificate=json.loads(Path('build/preflight.json').read_text())
    independent=check_solution(rows,512,certificate['solutions'])
    golden=Path('build/golden-controlled');assert not golden.exists(),'Preserve previous runs'
    golden.mkdir()
    golden_result=subprocess.run([str(Path('build/smoke-corrected').resolve()),'--golden'],cwd=golden,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)
    assert golden_result.returncode==0,golden_result.stdout[-6000:]
    record=dict(utc=datetime.now(timezone.utc).isoformat(),certificate=certificate,independently_verified_rank=independent,
        matrix_generator=dict(n=512,degree=12,seed=20261109,family='uniform'),
        native_command=command,native_exit_code=result.returncode,native_output=result.stdout.replace(str(Path.home()),'HOME'),
        golden_command=['build/smoke-corrected','--golden'],golden_exit_code=golden_result.returncode,
        golden_output=golden_result.stdout.replace(str(Path.home()),'HOME'),
        source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['native_preflight.py','experiments/binary.py','patches/batch-reconstruction.patch']},
        binary_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['build/solve-corrected','build/smoke-corrected']},
        performance_claim=False)
    Path('results/native-preflight.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS upstream golden run, all native oracles, and',independent,'independent CPU-verified kernel vectors')


if __name__=='__main__':main()
