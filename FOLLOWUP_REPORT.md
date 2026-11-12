# Larger complete solves and generator-cost closure

Requant Network, 12 November 2026. This supplement resolves the larger-matrix, generator-backend and complete-cost questions from the [historical report](FINAL_REPORT.md).

## Workload and independent certificates

Two matrix seeds each cover 8,192 and 32,768 rows, with uniform and heavy-head degree families. The degree parameter is 12, and eight unused columns plant a nullspace; this is not a claim that the true nullity is exactly eight or that the matrices are cryptographically hard. Actual row-degree range and nonzero counts are retained per matrix. Both profiles are sparse controlled workloads, not relation collection or a full factorization pipeline.

Each matrix compares the explicit GPU-hybrid generator at block64 untuned/tuned, block128 tuned and block256 tuned. The 8,192-row uniform matrix also compares the native CPU generator at blocks64/256. The same corrected pinned solver, sparse operator and reconstruction path are used. Annihilation, initialization cross-checks and configured SpMM validation remain enabled. Every returned vector passes a full independent CPU `A*x=0` check, and the retained vectors must be nonzero and linearly independent.

There is one warm-up and three measured **fresh-process complete solves** per configuration, not a thirty-sample latency claim. The 180-second process cap and failures are retained. All 36 configurations completed their three measured observations successfully, giving 108 independently validated measured solves, plus 36 validated warm-ups. Matrix generation/export and the external Python certificate replay are separate preparation/check boundaries. Native complete timing includes initialization, solve and native residual checking; process wall additionally includes startup and output. Timed solver phases and autotuning are retained in full.

## Complete-process outcome

Selected process medians, milliseconds; this boundary includes autotuning when enabled. Full data and native phase medians are in [followup-summary.csv](results/followup-summary.csv).

| Seed | Rows | Family | Nonzeros | Degree min..max | GPU64 untuned | GPU64 tuned | GPU128 tuned | GPU256 tuned |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 20261112 | 8192 | uniform | 98391 | 12..14 | 539.11 | 579.06 | 679.10 | 3763.99 |
| 20261112 | 8192 | head | 119923 | 12..97 | 510.83 | 553.17 | 655.14 | 3764.58 |
| 20261112 | 32768 | uniform | 393305 | 12..13 | 1233.20 | 1349.56 | 1471.78 | 6717.74 |
| 20261112 | 32768 | head | 479339 | 12..97 | 1309.95 | 1506.75 | 1594.48 | 6667.67 |
| 20261212 | 8192 | uniform | 98411 | 12..14 | 497.80 | 523.35 | 636.77 | 3656.73 |
| 20261212 | 8192 | head | 119933 | 12..98 | 547.27 | 624.95 | 700.50 | 3885.80 |
| 20261212 | 32768 | uniform | 393309 | 12..13 | 1276.64 | 1424.96 | 1542.79 | 6657.40 |
| 20261212 | 32768 | head | 479351 | 12..97 | 1319.06 | 1476.41 | 1595.87 | 6724.54 |

The block64 ranking survives both larger sizes and both characterized families in this campaign. Block256 remains much slower despite shorter projected sequences, because dense generator work grows. Autotuning lowers some sparse-phase costs but its setup is paid by each fresh solve: the untuned block64 process is faster in every retained size/family/cohort. That does not show tuning is useless when a matrix/configuration is reused; this study deliberately disables checkpoint/tuning reuse and charges its real cost.

## Explicit generator backend and phases

8,192-row uniform controls, median native phase-2 and complete process wall:

| Seed | Backend | Block | Stage 2, ms | Process wall, ms |
| --- | --- | ---: | ---: | ---: |
| 20261112 | gpu | 64 | 111.13 | 579.06 |
| 20261112 | gpu | 256 | 3262.86 | 3763.99 |
| 20261112 | cpu | 64 | 1190.44 | 1633.96 |
| 20261112 | cpu | 256 | 10049.33 | 10529.85 |
| 20261212 | gpu | 64 | 113.15 | 523.35 |
| 20261212 | gpu | 256 | 3188.59 | 3656.73 |
| 20261212 | cpu | 64 | 1209.59 | 1632.10 |
| 20261212 | cpu | 256 | 9696.99 | 10199.40 |

The GPU-hybrid generator improves complete solves relative to these CPU-generator controls, but that does not make the larger block a good choice: the block64 GPU-hybrid configuration remains better. This directly distinguishes GPU use in the dense generator from merely using the GPU in sparse phases. Full phase costs include the retained initialization/cross-check work; a fast isolated dense product is not used as a substitute.

## Layout integration decision

The earlier original-layout sparse product is independently qualified, but has not been inserted into the complete solver. The prior optimistic ceiling for eliminating its entire sparse phase-1/3 contribution was only about 1.025x in the generator-dominated case. The new complete phase records reinforce the bottleneck decision: preserve the current verified operator while choosing the generator/backend/block using complete solve cost. Conversion, index layout, buffer lifetime and solver ownership would all have to be paid by any later layout replacement; this campaign does not call that unimplemented integration complete or assign it a fictitious application speedup.

The completed recommendation for these controlled matrices is GPU-hybrid block64; charge tuning explicitly and retain the untuned fresh-solve baseline. Do not generalize this ranking to million-row cryptanalytic matrices, or infer a complete factorization/mining workload.

## Reproduction and checks

[scaling_study.py](scaling_study.py) reuses the pinned corrected native timing executables. Run `python scaling_study.py --pilot` first, then `python scaling_study.py`; repeat with `--seed 20261212 --output results/scaling-replication.json`. Existing documented native CPU/GPU-generator builds and correction patches remain required. Every observation retains its binary identity, matrix identity, certificate, independent rank, native phase log and complete timing. `python verify_followups.py` regenerates each characterized matrix and rechecks every retained successful certificate, source binding and derived summary on CPU. CI does not repeat GPU timings.

GPU campaigns run serially on the same RTX 5060 Ti. Clocks, power limits and unrelated server services are unchanged. No energy, production hardness or heterogeneous multi-GPU claim follows.
