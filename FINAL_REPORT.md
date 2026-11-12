# Final report

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

The original CSR/warp-CSR/ELL workload measures 128 actual products at 4096/16384 rows with 256-bit blocks. It includes direct and captured execution, layout conversion, storage and vector transfers. These kernels are not a drop-in measured replacement inside the solver. The report instead uses an intentionally generous bound that eliminates entire native phases 1 and 3. For the reported GPU-hybrid block-256 case, that ceiling is only 1.025–1.025×, so a large product microbenchmark advantage cannot repair that parameter choice.

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

## Follow-up closure, 12 November 2026

The [follow-up report](FOLLOWUP_REPORT.md) resolves the concrete priorities above with additional experiments, resource gates and updated conclusions. Its findings supersede the open-work wording in this historical campaign.
