"""Generate solver/layout findings with explicit CPU and GPU-hybrid generator scopes."""
import csv,hashlib,json,pathlib

root=pathlib.Path('.')
native=list(csv.DictReader((root/'results/native-summary.csv').open()))
products=list(csv.DictReader((root/'results/products-summary.csv').open()))
assert len(native)==96 and len(products)==36
assert {r['stage2_backend'] for r in native}=={'cpu','gpu'}
assert all(int(r['failures'])==0 and int(r['successful_observations'])==int(r['requested_observations']) for r in native)
observations=sum(int(r['successful_observations']) for r in native)
assert observations==720
for name in ('native-validation.json','native-gpu-validation.json'):
    value=json.loads((root/'results'/name).read_text());assert value['validation_only'] and len(value['cases'])==48
    assert all(len(c['results'])==1 and c['results'][0]['exit_code']==0 and c['oracle'] for c in value['cases'])

def interval(values,places=2):
    assert len(values)==2
    return f'{min(values):.{places}f}–{max(values):.{places}f}'
def selected(backend,block,tuned,key):
    return [float(r[key]) for r in native if r['stage2_backend']==backend and r['n']=='512' and r['family']=='uniform' and int(r['block'])==block and r['tuned']==str(tuned)]
table=['| Generator path | Block | Tuning | Complete process median, ms | Stage 2 median, ms |','|---|---:|---|---:|---:|']
for backend in ('cpu','gpu'):
    for block in (64,256):
        for tuned in (False,True):
            table.append(f"| {'CPU control' if backend=='cpu' else 'GPU hybrid'} | {block} | {'on' if tuned else 'off'} | {interval(selected(backend,block,tuned,'process_wall_median_ms'))} | {interval(selected(backend,block,tuned,'Stage 2_median_ms'))} |")
table='\n'.join(table)
ptable=['| Matrix family | Layout | 128-product graph median, ms | Conversion + graph median, ms | Layout bytes |','|---|---|---:|---:|---:|']
for family in ('uniform','banded','head'):
    for mode in ('csr','warp_csr','ell'):
        rows=[r for r in products if r['n']=='16384' and r['family']==family and r['method']==mode]
        assert len(rows)==2
        ptable.append(f"| {family} | {mode} | {interval([float(r['resident_graph_ms_median']) for r in rows],4)} | {interval([float(r['conversion_plus_graph_median_ms']) for r in rows],3)} | {min(int(r['layout_bytes']) for r in rows):,}–{max(int(r['layout_bytes']) for r in rows):,} |")
ptable='\n'.join(ptable)
ceilings=selected('gpu',256,False,'optimistic_eliminate_stages_1_and_3_speedup_ceiling')
results=f'''# Results

A research project by [Requant Network](https://requant.network).

## Correctness and complete solver coverage

The corrected native solver completes 720 timed fresh-process observations across 96 parameter cases: two generator backends, two input seeds, three matrix families, dimensions 512/2048, blocks 64/256 and tuning off/on. All observations return nonzero certificates that pass independent CPU residual and linear-independence checks. The requested output is at most five certificates, not the entire nullspace basis.

Separate compatibility campaigns contain 48 CPU-generator and 48 GPU-hybrid-generator cases with all native oracles enabled. All 96 pass. The upstream golden run also passes with its GPU generator and original checks enabled. Independent small CPU tests retain 72 exhaustively checked nullspaces, six sparse families and 52 targeted invalid-certificate rejections.

The original unmodified golden solve fails an oracle comparison. The retained [diagnostic vectors](results/reconstruction-failure.json) establish a real mathematical error: the batched vector has residual weight 256 while the scalar reference has zero residual under the same deterministic matrix. The two-part correction groups equal-degree Horner candidates and initializes stripping history. No oracle is removed.

## Generator and block choice: uniform 512-row case

Each interval spans the two input-cohort medians and is not a confidence interval. These cases use five warmups and thirty retained observations. Process time includes launch, input reading, initialization, tuning, all stages, native checking and certificate writing. Python certificate checking is separate. Native STATS logging is enabled in both timing executables.

{table}

The pinned configuration defaults `stage2_gpu_mode` to false. The first harness inherited that setting, so its measurements are retained as an explicit CPU-generator control. The second harness selects the GPU-hybrid recursive path explicitly; GPU initialization and the configured CPU cross-check remain active. GPU annihilation verification alone would not select that backend. These paths are now labelled separately in every summary row and its provenance.

The GPU-hybrid generator reduces the large block's dense-generator cost substantially, but block 256 remains much slower than block 64 in this bounded example. A wider block cannot be ranked from sparse-product throughput alone. Native preprocessing can improve stage-one work while its own cost and fresh-process setup leave the complete latency nearly unchanged.

## Original layout experiment: 16,384 rows and 256-bit blocks

Every observation performs 128 actual dependent products, with outputs compared against independent Python integer XOR. Each fixed case has five warmups/thirty direct, graph and vector-transfer observations. The rows below describe a separate product workload, not an integrated solver substitution.

{ptable}

CSR is the most consistent baseline in these cases. Warp-per-output CSR is slower despite using more lanes per row. ELL has a small banded-family resident win in one cohort, while the other cohort does not reproduce that win; its conversion-inclusive result loses in both. The heavy-head family makes ELL padding costly in storage and runtime. This is useful negative evidence against treating a layout as universally superior.

Conversion-inclusive latency is one measured layout conversion/upload plus the graph median, not a separately sampled distribution. Vector-transfer-inclusive measurements are retained in [products-summary.csv](results/products-summary.csv). Original layouts are not integrated into the upstream solver, and no measured integrated-layout speedup is claimed.

![Complete solver and separate layout workloads](figures/sparse-study.png)

## Full-solve bound and limits

For the GPU-hybrid 512-row/block-256/untuned case, even an optimistic bound that removes **all** of native phases 1 and 3 gives only {interval(ceilings,3)}× process speedup. Removing their sparse products alone can do no better. This is an Amdahl ceiling for that native workload, not an application of a kernel-speed ratio measured on a different matrix size.

The controlled matrices deliberately plant at least eight kernel dimensions through duplicated columns. They do not establish factoring-instance hardness. Fresh-process times include context/library setup and are not persistent-service latency. Larger/irregular solves use one warmup/three observations, rather than a thirty-sample distribution. Both backend data sets, exact settings, raw phase logs, failures and memory fields remain separate.

See [native-summary.csv](results/native-summary.csv), [Methods](METHODS.md), [related work](RELATED_WORK.md), [final conclusions](FINAL_REPORT.md) and the [protocol](RESEARCH.md). No complete factorization, mining-income or energy conclusion follows from these experiments.
'''
final=f'''# Final report

A research project by [Requant Network](https://requant.network).

## Conclusion

The study produces a corrected, independently checkable SM120 Block Wiedemann experiment and a measured separation between sparse-product cost and complete solver cost. All 720 timed solve observations and both 48-case oracle campaigns pass their configured checks. The original reconstruction defect is retained as a reproducible vector/residual counterexample and an attributed patch.

Backend selection and dense polynomial-generator work matter more than an isolated sparse-layout result in the small controlled cases. The GPU-hybrid path improves the block-256 generator, but block 64 remains much faster in the reported uniform 512-row example. Among the original layout experiments, CSR is the more consistent choice; an ELL resident win on one banded input does not survive conversion and is not replicated by the other input.

## Mathematical and implementation findings

The unmodified batched Horner evaluation could apply the operator after a candidate's own degree ended. An uninitialized history ring could then resurrect an initially zero value as arbitrary data. The independent CPU residual establishes that the observed discrepancy is not simply another valid basis or a harmless hash normalization. Grouping equal-degree batches and clearing the ring addresses those two causes while retaining the original oracle comparison.

Every exported certificate is checked for nonzero value, vector range, zero A*x residual and independence from the other returned vectors. Independence is a property of the returned set; it is not a claim to have computed the entire matrix rank or full kernel basis. The controlled matrix generator intentionally creates a nontrivial kernel and remains unsuitable as evidence of cryptographic hardness.

The backend audit also corrected a measurement assumption. The initial harness inherited the library's CPU-generator default. Its data remain useful as a labelled control, while a second executable explicitly selects the experimental GPU-hybrid path. Both executables retain the same configured certificate, SpMM and annihilation checks. The GPU initializer also runs its configured CPU cross-check. Complete timing includes those implementation and validation costs.

## Performance interpretation

Wider blocks shorten some projected sequences but enlarge dense generator work. The measured tradeoff therefore requires all three native phases and the complete process boundary. Tuning a sparse product is useful only to the extent that its gain survives preprocessing and the remaining solver. The retained phase statistics make that boundary visible.

The original CSR/warp-CSR/ELL workload measures 128 actual products at 4096/16384 rows with 256-bit blocks. It includes direct and captured execution, layout conversion, storage and vector transfers. These kernels are not a drop-in measured replacement inside the solver. The report instead uses an intentionally generous bound that eliminates entire native phases 1 and 3. For the reported GPU-hybrid block-256 case, that ceiling is only {interval(ceilings,3)}×, so a large product microbenchmark advantage cannot repair that parameter choice.

Repeated observations remain attached to their input seed. Uniform 512-row cases have five warmups/thirty fresh-process samples; larger and irregular cases have one warmup/three. This is an explicit feasibility choice for expensive complete solves, not a missing repetition disguised as a thirty-sample result. The retained counts and raw vectors permit independent CPU rechecking of every successful solve.

## Completed protocol gates

| Required experiment | Retained evidence |
|---|---|
| Independent GF(2) reference and invalid certificates | Exhaustive small elimination, sparse XOR, nonzero/residual/independence checks and targeted rejections |
| Native SM120 solver through all stages | Corrected upstream golden run, separate fixtures, CPU and GPU-hybrid oracle campaigns |
| Block/tuning/family comparisons and full costs | 96 parameter cases, 720 timed observations, setup/phase/verification/RSS data |
| Original product layouts and integration-cost test | 36 replicated layout cases, 128-step chains, conversion/storage/transfer measurements and conservative full-solve ceilings |
| Reproducible evidence, negative results and CPU CI | Original failing vectors, exact patch/source/build hashes, both backends, all exported certificates and deterministic reports |

## Follow-up priorities

First, optimize and qualify the dense generator at larger block sizes, including its validation and initialization costs. That target follows from measured phase attribution. Second, use much larger, explicitly characterized sparse matrices before generalizing the small-case block-size ranking. Third, integrate an alternative sparse layout only when its conversion/amortization model predicts a meaningful complete-solve gain; retain the current independent residual checks during that work.

The study does not include relation collection, matrix filtering, a full number-field sieve, an integrated original-layout solver, a cryptographic challenge design or energy measurements. Those are separate application workloads. [Results](RESULTS.md), [Methods](METHODS.md), [related work](RELATED_WORK.md) and the [research protocol](RESEARCH.md) retain the full source and claim boundaries.
'''
final += '\n## Follow-up closure, 12 November 2026\n\nThe [follow-up report](FOLLOWUP_REPORT.md) resolves the concrete priorities above with additional experiments, resource gates and updated conclusions. Its findings supersede the open-work wording in this historical campaign.\n'
(root/'RESULTS.md').write_text(results,encoding='utf-8',newline='\n');(root/'FINAL_REPORT.md').write_text(final,encoding='utf-8',newline='\n')
record=dict(source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['generate_report.py','summarize_results.py']},
    artifacts_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['RESULTS.md','FINAL_REPORT.md','results/products-summary.csv','results/native-summary.csv']},
    timed_solve_observations=observations,compatibility_cases=96,stage2_backends=['cpu','gpu-hybrid'])
(root/'results/report-provenance.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Generated complete-solve/layout findings and explicit backend conclusions')
