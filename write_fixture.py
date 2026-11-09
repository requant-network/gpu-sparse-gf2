"""Write a deterministic sparse fixture in the original harness binary format."""
import argparse,pathlib,struct
from experiments.binary import fixture

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--n',type=int,default=512);p.add_argument('--degree',type=int,default=12)
p.add_argument('--seed',type=int,default=20261109);p.add_argument('--family',choices=('uniform','banded','head'),default='uniform')
p.add_argument('--output',default='build/matrix.bin');a=p.parse_args();rows=fixture(a.n,a.degree,a.seed,a.family)
path=pathlib.Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
with path.open('wb') as f:
    f.write(struct.pack('<II',0x32464752,a.n))
    for row in rows:f.write(struct.pack('<I',len(row)));f.write(struct.pack('<'+'I'*len(row),*row))
print(a.n,a.family,sum(map(len,rows)),'nonzeros')
