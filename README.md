# Sparse GF(2) GPU Research

A research project by [Requant Network](https://requant.network).

**Status: active research. Independent CPU checks and a corrected native golden solve pass; full performance campaigns remain in progress.**

This project studies exact sparse binary linear algebra on consumer Blackwell: complete Block Wiedemann solves and repeated sparse matrix-block products. Its relevance is to the linear-algebra stage of factoring and other cryptographic computations. It does not implement a complete factorization pipeline or demonstrate a profitable proof-of-work scheme.

## Findings so far

| Experiment | Observed result |
|---|---|
| CPU elimination and certificates | 72 exhaustively checked small nullspaces; six seeded sparse families; 52 altered certificates rejected |
| Unmodified pinned native golden solve | Fails its own stage-three oracle comparison |
| Independent diagnosis | One faulty batched reconstruction has a nonzero residual, so the discrepancy is a mathematical error rather than only a different vector hash |
| Attributed two-part correction | Group batch candidates by polynomial degree; clear unwritten stripping history |
| Corrected upstream golden test | Completes with all native oracle and annihilation checks enabled |
| Independent controlled solve | Five nonzero, linearly independent vectors satisfy `A*x = 0` under a separate CPU implementation |

These are compatibility and correctness observations. Incidental timings in preflight records were collected during other CPU compilation and are not performance comparisons.

## Why the reconstruction failed

The original batched Horner loop advanced every candidate to the batch's maximum polynomial degree. A candidate with a smaller degree could therefore receive extra applications of the operator after its own polynomial ended. Its degree-local oracle check could pass, even though the value later supplied to stripping was different or already zero.

The stripping history was allocated without initialization. An early backward scan could inspect unwritten slots, resurrecting an initially zero candidate as arbitrary data. Independent residual checking exposed a vector with 256 nonzero residual entries. Both causes are addressed in [patches/batch-reconstruction.patch](patches/batch-reconstruction.patch); no oracle or arithmetic check is disabled.

The patch is over upstream Block Wiedemann commit `ebfe814b759803f61771b36d1fd197b71b751d1d`. Upstream sources remain immutable. [build_native.py](build_native.py) copies and patches the single reconstruction source, compiles a replacement object, and removes the original object from a copied static archive to avoid duplicate CUDA device definitions. Other native objects remain those of the pinned build.

## Independent mathematics and workload scope

[experiments/binary.py](experiments/binary.py) implements GF(2) elimination with Python bit integers, exhaustive small-kernel checks, sparse XOR products, and nonzero certificate validation. The controlled matrix generator has uniform, banded, and heavy-head row patterns. It deliberately duplicates eight columns to guarantee a nontrivial kernel. These fixtures study controlled algebra and irregular memory access; planted kernel vectors do not establish cryptographic hardness.

The native harness explicitly solves the **right kernel of A**, exports every solution, and checks its residual. The Python checker independently verifies the residuals and linear independence. Distinct vectors alone are insufficient. Failures are retained rather than silently removed from timing populations.

Original CSR, warp-per-output CSR, and ELL products are compared over 128 actual Krylov applications with 256-bit blocks. Their outputs are checked against Python integer XOR arithmetic. These original kernels are separate from the upstream solver; a product-kernel win cannot be reported as a measured end-to-end solver speedup.

## Reproduction

CPU controls need Python 3.12:

```sh
python cpu_study.py
python verify_records.py
python verify_results.py
```

Build the pinned upstream with CUDA 13.3, `GPU_TARGET=120`, Release configuration and CUDA graphs enabled. Keep the checkout clean. From this repository:

```sh
python build_native.py ../block-wiedemann ../bw-build
python native_preflight.py
python native_study.py --validation-only --output results/native-validation.json
```

For performance, omit `--validation-only`. Uniform 512-row configurations use five warmups/thirty process observations. Larger and irregular solves use one warmup/three observations, preserving the cost of compatibility checks and unsuccessful solves. Generator seeds `20261109` and `20261209` are distinct from repeated timing observations. Process wall time includes input reading, setup, tuning, all three stages, native checking, and writing the certificates; native phase timers and Python verification are retained separately.

With NumPy 2.2.6 and CuPy 13.6.0, run the original layouts with `python gpu_study.py`; use `--validation-only` for correctness probes. Repeat with `--seed 20261209` and a distinct output file. Resident direct/captured timing includes 128 actual products; initial layout conversion and vector transfers are separately identified. No energy claim is made.

## Evidence, limits and licensing

The [protocol](RESEARCH.md) defines completion gates. Raw records are retained in [results](results), including complete native vectors suitable for CPU-only checking. CI reruns independent CPU arithmetic, checks source bindings, and independently checks committed native certificates; hosted CPU CI does not rerun CUDA solves.

Pending: replicated timing cohorts, complete tuning/block comparisons, layout amortization tables and final reports. The reconstruction correction is tested on bounded fixtures and the upstream golden test; it is not a general proof of solver correctness. Original research code is [MIT licensed](LICENSE). The attributed patch and included upstream material retain LGPL-3.0-only and the upstream NVIDIA CUDA linking exception. No issue or pull request has been sent upstream.
