"""Original CSR, warp-CSR and ELL layouts for exact repeated GF(2) Krylov work."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time
import cupy as cp
import numpy as np
from experiments.binary import fixture,sparse_product


def main():
    assert __debug__
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=20261109)
    parser.add_argument('--validation-only',action='store_true')
    parser.add_argument('--output',default='results/gpu-study.json')
    args=parser.parse_args();rng=np.random.default_rng(args.seed);cases=[]
    stream=cp.cuda.Stream(non_blocking=True);stream.use()
    module=cp.RawModule(code=Path('cuda/products.cu').read_text(),options=('--std=c++17',))
    kernels={name:module.get_function(name) for name in ('csr','warp_csr','ell')}

    def samples(function):
        for _ in range(5):function()
        stream.synchronize();result=[]
        for _ in range(30):
            a,b=cp.cuda.Event(),cp.cuda.Event();a.record();function();b.record();b.synchronize();result.append(cp.cuda.get_elapsed_time(a,b))
        return result

    for n in (4096,16384):
        for family in ('uniform','banded','head'):
            rows=fixture(n,12,args.seed,family);nnz=sum(map(len,rows));width=max(map(len,rows));steps=128;words=4
            initial=rng.integers(0,2**64,(n,words),np.uint64)
            values=[sum(int(v)<<(64*w) for w,v in enumerate(row)) for row in initial]
            begin=time.perf_counter()
            for _ in range(steps):values=sparse_product(rows,values)
            cpu_ms=(time.perf_counter()-begin)*1000
            expected=np.array([[(v>>(64*w))&((1<<64)-1) for w in range(words)] for v in values],np.uint64)
            original=cp.asarray(initial);first=cp.empty_like(original);second=cp.empty_like(original)
            for method in kernels:
                begin=time.perf_counter()
                offsets=np.array([0]+list(np.cumsum([len(row) for row in rows])),np.int32)
                columns=np.array([j for row in rows for j in row],np.int32)
                if method=='ell':
                    layout=np.full((width,n),-1,np.int32)
                    for r,row in enumerate(rows):layout[:len(row),r]=row
                    gpu_layout=cp.asarray(layout);storage=layout.nbytes
                else:
                    gpu_offsets=cp.asarray(offsets);gpu_columns=cp.asarray(columns);storage=offsets.nbytes+columns.nbytes
                stream.synchronize();conversion_ms=(time.perf_counter()-begin)*1000

                def run():
                    x=original
                    for s in range(steps):
                        y=first if s%2==0 else second
                        if method=='ell':
                            arguments=(gpu_layout,x,y,np.int32(n),np.int32(width),np.int32(words));threads=n*words
                        else:
                            arguments=(gpu_offsets,gpu_columns,x,y,np.int32(n),np.int32(words));threads=n*words*(32 if method=='warp_csr' else 1)
                        kernels[method](((threads+255)//256,),(256,),arguments);x=y
                run();stream.synchronize();actual=cp.asnumpy(second)
                assert np.array_equal(actual,expected),(n,family,method)
                record=dict(n=n,family=family,degree=12,nonzeros=nnz,block_bits=64*words,steps=steps,method=method,
                    layout_bytes=storage,conversion_h2d_wall_ms=conversion_ms,cpu_reference_wall_ms=cpu_ms,
                    exact_output_words=actual.size,input_sha256=hashlib.sha256(initial.tobytes()+columns.tobytes()+offsets.tobytes()).hexdigest(),
                    output_sha256=hashlib.sha256(actual.tobytes()).hexdigest())
                if not args.validation_only:
                    record['resident_direct_ms']=samples(run)
                    stream.begin_capture();run();graph=stream.end_capture()
                    record['resident_graph_ms']=samples(lambda:graph.launch(stream))
                    graph.launch(stream);stream.synchronize();assert np.array_equal(cp.asnumpy(second),expected)
                    def with_vector_transfer():original.set(initial);graph.launch(stream);second.get()
                    for _ in range(5):with_vector_transfer()
                    transfer=[]
                    for _ in range(30):
                        start=time.perf_counter();with_vector_transfer();stream.synchronize();transfer.append((time.perf_counter()-start)*1000)
                    record['vector_transfer_inclusive_ms']=transfer
                    # Include layout construction/upload anew for amortization, separately from persistent-layout samples.
                    record['conversion_plus_graph_median_ms']=conversion_ms+float(np.median(record['resident_graph_ms']))
                cases.append(record);print('PASS',n,family,method,flush=True)
    files=['gpu_study.py','cuda/products.cu','experiments/binary.py']
    record=dict(utc=datetime.now(timezone.utc).isoformat(),seed=args.seed,cases=cases,validation_only=args.validation_only,
        source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files},
        scope='128 actual sparse matrix-block applications with exact CPU integer XOR reference. Original layouts are not integrated into upstream Block Wiedemann; no full-solver speedup inferred.')
    Path(args.output).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
