"""Exhaustive small nullspaces and seeded sparse-family correctness controls."""
import argparse,hashlib,itertools,json,pathlib,random
from experiments.binary import fixture,kernel,sparse_product,verify

assert __debug__
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='results/cpu-study.json');args=parser.parse_args()
checks=0;negatives=0;families=[];rng=random.Random(20261109)
for n in range(1,7):
    for trial in range(12):
        rows=[rng.randrange(1<<n) for _ in range(n)];vectors,rank=kernel(rows,n);span={0}
        for v in vectors:span|={x^v for x in list(span)}
        exact={v for v in range(1<<n) if all(not((row&v).bit_count()&1) for row in rows)}
        assert span==exact and len(span)==1<<(n-rank);assert not verify(rows,n,0);checks+=1
for seed,family in itertools.product((20261109,20261209),('uniform','banded','head')):
    rows=fixture(128,12,seed,family);packed=[sum(1<<j for j in row) for row in rows];vectors,rank=kernel(packed,128)
    assert len(vectors)>=8 and all(verify(packed,128,v) for v in vectors)
    for j in range(8):assert verify(packed,128,(1<<j)|(1<<(120+j)))
    for v in vectors:
        for j in range(128):
            if not verify(packed,128,v^(1<<j)):negatives+=1;break
    values=[rng.getrandbits(128) for _ in range(128)];actual=sparse_product(rows,values)
    for row,out in zip(packed,actual):
        reference=0
        for j in range(128):
            if row>>j&1:reference^=values[j]
        assert reference==out
    families.append(dict(seed=seed,family=family,rank=rank,nullity=len(vectors),nonzeros=sum(map(len,rows))))
record=dict(exhaustive_small_matrices=checks,altered_certificates_rejected=negatives,families=families,
    source_sha256={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in ('cpu_study.py','experiments/binary.py')},
    scope='Independent exact elimination and sparse block products. Benchmark families plant repeated columns to guarantee nonzero nullspace; no hardness/mining claim.')
p=pathlib.Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
print(checks,'exhaustive small nullspaces;',len(families),'sparse families;',negatives,'altered certificates rejected')
