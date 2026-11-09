"""Independently recheck retained native kernel certificates without a GPU."""
import json,pathlib
from experiments.binary import fixture
from native_preflight import check_solution
assert __debug__
checked=0
preflight=pathlib.Path('results/native-preflight.json')
if preflight.exists():
    r=json.loads(preflight.read_text());g=r['matrix_generator']
    rows=fixture(g['n'],g['degree'],g['seed'],g['family'])
    assert check_solution(rows,g['n'],r['certificate']['solutions'])==r['independently_verified_rank']
    assert r['native_exit_code']==r['golden_exit_code']==0;checked+=1
for p in pathlib.Path('results').glob('native-*.json'):
    r=json.loads(p.read_text())
    for case in r.get('cases',[]):
        rows=fixture(case['n'],case['degree'],case['seed'],case['family'])
        for observation in case['results']:
            if observation['exit_code']!=0:continue
            assert check_solution(rows,case['n'],observation['certificate']['solutions'])==observation['independent_solution_rank']
            checked+=1
assert checked
diagnosis=pathlib.Path('results/reconstruction-failure.json')
if diagnosis.exists():
    r=json.loads(diagnosis.read_text());g=r['matrix_generator'];rows=fixture(g['n'],g['degree'],g['seed'],g['family'])
    for value in r['vectors'].values():
        bits=value['bits'];assert len(bits)==g['n'] and set(bits)<={0,1}
        assert sum(bits)==value['weight']
        assert sum(sum(bits[j] for j in row)%2 for row in rows)==value['residual_weight']
    assert any(v['residual_weight'] for v in r['vectors'].values())
print(checked,'native solution sets independently verified on CPU')
