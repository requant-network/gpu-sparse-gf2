# Research protocol

A research project by [Requant Network](https://requant.network).

## Required experiments

1. Implement independent CPU GF(2) rank/nullspace, sparse matrix-block products and kernel-vector checks; reject zero and corrupted certificates.
2. Build pinned upstream Block Wiedemann for SM120, run all three stages, export matrices and nonzero solutions, and independently recheck A*x=0.
3. Compare untuned/tuned preprocessing and block sizes on controlled sparse matrix families, with two generator seeds; include complete solve, preparation, verification, memory and unsuccessful solves.
4. Implement and validate original alternative sparse block-product layouts on CPU/GPU, compare complete repeated Krylov work including conversion, and test whether an observed kernel win survives full-solve costs.
5. Publish replicated raw evidence, five/thirty fixed-input timings where practical, exact coverage and stage boundaries, pinned upstream provenance and final conclusions without treating a matrix microbenchmark as a complete solver.

## Evidence and completion gates

Original code is MIT licensed; upstream code and patches retain attribution and applicable licenses. Execute GPU timing campaigns sequentially on the available RTX 5060 Ti 16 GB. Keep independent generator seeds distinct from repeated timing samples. Preserve unsuccessful trials, negative findings, exact integer/proof checks, raw source/result hashes, compiler flags and hardware/software metadata. No energy claim without sampled measurements.

Completion requires all experiments above, executable CPU/GPU studies, independently recheckable retained evidence, derived tables, a detailed English README, METHODS.md, RESULTS.md and FINAL_REPORT.md. Public repository topics/homepage identify Requant Network. Latest published-head CPU/reference/artifact CI must pass. A documented negative experiment may complete a hypothesis test; a missing required experiment may not.
