"""Derive sparse-product and complete-native-solve tables without conflating their scopes."""
import csv,json,pathlib,statistics


def table(path,rows):
    assert rows
    with pathlib.Path(path).open('w',encoding='utf-8',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)


products=[]
for path in sorted(pathlib.Path('results').glob('gpu-study-*.json')):
    record=json.loads(path.read_text());assert not record['validation_only']
    for case in record['cases']:
        row={key:case[key] for key in ('n','family','method','nonzeros','block_bits','steps','layout_bytes','conversion_h2d_wall_ms')};row['seed']=record['seed']
        for name in ('resident_direct_ms','resident_graph_ms','vector_transfer_inclusive_ms'):
            values=case[name];assert len(values)==30
            row[name+'_median']=statistics.median(values);row[name+'_min']=min(values);row[name+'_max']=max(values)
        row['conversion_plus_graph_median_ms']=case['conversion_plus_graph_median_ms'];products.append(row)
assert {r['seed'] for r in products}=={20261109,20261209}
for row in products:
    baseline=next(r for r in products if all(r[k]==row[k] for k in ('seed','n','family')) and r['method']=='csr')
    row['graph_speedup_vs_csr']=baseline['resident_graph_ms_median']/row['resident_graph_ms_median']
    row['conversion_inclusive_speedup_vs_csr']=baseline['conversion_plus_graph_median_ms']/row['conversion_plus_graph_median_ms']
table('results/products-summary.csv',products)
solves=[]
for path in ('results/native-study.json','results/native-gpu-study.json'):
    native=json.loads(pathlib.Path(path).read_text());assert not native['validation_only'] and len(native['cases'])==48
    for case in native['cases']:
        good=[v for v in case['results'] if v['exit_code']==0]
        row={key:case[key] for key in ('stage2_backend','n','degree','seed','family','block','tuned','warmups','requested_observations')}
        row['successful_observations']=len(good);row['failures']=len(case['results'])-len(good)
        row['process_wall_median_ms']=statistics.median([v['process_wall_ms'] for v in good]) if good else ''
        row['native_verified_wall_median_ms']=statistics.median([v['certificate']['complete_verified_wall_ms'] for v in good]) if good else ''
        row['python_check_median_ms']=statistics.median([v['independent_python_check_ms'] for v in good]) if good else ''
        for phase in ('Stage 1','Stage 2','Stage 3','AutoTune'):
            row[phase+'_median_ms']=statistics.median([v['native_phase_ms'].get(phase,0) for v in good]) if good else ''
        # Eliminating whole phases 1 and 3 is more generous than removing their SpMM calls.
        ceilings=[]
        for v in good:
            total=v['process_wall_ms'];removable=v['native_phase_ms']['Stage 1']+v['native_phase_ms']['Stage 3']
            assert removable<total
            ceilings.append(total/(total-removable))
        row['optimistic_eliminate_stages_1_and_3_speedup_ceiling']=statistics.median(ceilings) if ceilings else ''
        row['peak_host_rss_kib']=max(v['certificate']['peak_rss_kib'] for v in good) if good else ''
        solves.append(row)
table('results/native-summary.csv',solves)
print(len(products),'product rows;',len(solves),'native solve rows; scopes retained separately')
