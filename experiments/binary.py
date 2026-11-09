"""Independent bit-integer GF(2) elimination, sparse products and certificates."""
import random

def kernel(rows,n):
    basis={}
    for row in rows:
        assert 0<=row<1<<n
        while row:
            pivot=row.bit_length()-1
            if pivot in basis:row^=basis[pivot]
            else:basis[pivot]=row;break
    result=[]
    for free in sorted(set(range(n))-set(basis)):
        v=1<<free
        for pivot,row in sorted(basis.items()):
            if (row&v).bit_count()&1:v^=1<<pivot
        assert verify(rows,n,v);result.append(v)
    return result,len(basis)

def verify(rows,n,v):return 0<v<1<<n and all(not((row&v).bit_count()&1) for row in rows)

def sparse_product(rows,values):
    result=[]
    for row in rows:
        value=0
        for index in row:value^=values[index]
        result.append(value)
    return result

def fixture(n,degree,seed,family='uniform',nullity=8):
    assert n>2*nullity and 0<degree<n-nullity
    rng=random.Random(seed);rows=[]
    for i in range(n):
        if family=='banded':choices={(i+rng.randrange(-32,33))%(n-nullity) for _ in range(degree)}
        else:
            count=min(n-nullity,degree*(8 if family=='head' and i<n//32 else 1))
            choices=set(rng.sample(range(n-nullity),count))
        choices|={n-nullity+j for j in range(nullity) if j in choices}
        rows.append(sorted(choices))
    return rows
