# Sparse GF(2) GPU Research

Complete sparse binary linear algebra, Block Wiedemann, representation and setup amortization.

A research project by [Requant Network](https://requant.network).

**Status: research in progress. No performance result is claimed yet.**

## Research question and scope

Implement independent CPU GF(2) rank/nullspace, sparse matrix-block products and kernel-vector checks; reject zero and corrupted certificates.

Build pinned upstream Block Wiedemann for SM120, run all three stages, export matrices and nonzero solutions, and independently recheck A*x=0.

Compare untuned/tuned preprocessing and block sizes on controlled sparse matrix families, with two generator seeds; include complete solve, preparation, verification, memory and unsuccessful solves.

Implement and validate original alternative sparse block-product layouts on CPU/GPU, compare complete repeated Krylov work including conversion, and test whether an observed kernel win survives full-solve costs.

Publish replicated raw evidence, five/thirty fixed-input timings where practical, exact coverage and stage boundaries, pinned upstream provenance and final conclusions without treating a matrix microbenchmark as a complete solver.

## Experimental approach

Start from independent exact CPU controls and pinned upstream references. Build hardware-specific paths with validation enabled, then compare complete workloads rather than isolated instruction rates. Retain both independent input cohorts and unsuccessful/negative outcomes.

Fixed-input studies use five warm-ups and thirty measured observations where practical. Stochastic solves and proof commitments use independent inputs and separately identify repeated latency observations. Correctness checks, allocation, compilation, transfer and setup boundaries will be documented per timer.

## Reproduction and evidence

Executable studies and commands are added as experiments become runnable. The committed [research protocol](RESEARCH.md) defines the required experiments and completion gates; reports will distinguish completed measurements from pending work. No GPU benchmark is implied by this initial protocol checkpoint.

## Intended deliverables

- Independent CPU reference and negative correctness controls.
- Executable GPU/native implementations with exact upstream revisions.
- Raw seeded results, derived tables and source/result/build provenance.
- Complete English methods, findings, reproduction commands and limitations.
- CPU/reference/artifact CI on the final published commit.

## License and contributions

Original research code is [MIT licensed](LICENSE). Third-party implementations retain their own licenses. Contributions should include the source revision, environment, exact command, correctness evidence, complete timing boundaries and retained negative results.
