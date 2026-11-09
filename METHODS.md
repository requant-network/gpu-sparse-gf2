# Methods

A research project by [Requant Network](https://requant.network).

## Questions and workload construction

This study separates complete Block Wiedemann solves from sparse matrix-block products. The first question is whether a pinned SM120 build can produce independently checkable right-kernel certificates. The second is how block size and native preprocessing affect complete cost. The third is whether an original product-layout advantage survives conversion and the other solver stages.

Controlled square matrices have uniform, banded and heavy-head row patterns. Eight columns duplicate the first eight to guarantee a nontrivial kernel. This construction is explicit: the matrices are not hardness instances, and a planted kernel does not support a cryptographic or mining claim. Matrix seeds 20261109 and 20261209 are distinct from repeated timing observations.

Independent Python bit-integer elimination checks rank and nullspaces on small matrices exhaustively. Sparse block products use integer XOR. A valid certificate must be nonzero, within the declared vector length, and have zero residual on every row. Multiple certificates are additionally checked for linear independence; distinct hashes are insufficient. The native harness solves A directly, rather than silently switching to the kernel of AᵀA.

## Pinned native implementation and correction

The reference is Block Wiedemann revision `ebfe814b759803f61771b36d1fd197b71b751d1d`, built Release for GPU target 120 with CUDA graphs enabled. An unmodified golden solve and an independently generated fixture fail a stage-three oracle comparison. The retained diagnostic includes the scalar and batched vector contents. The incorrect batched vector has nonzero residual under the independent CPU matrix generator.

The attributed correction keeps batches at one polynomial degree so Horner evaluation does not advance a finished candidate. It clears the stripping history before the first snapshot so a backward scan cannot read unwritten allocation contents. The original oracle, stage-two annihilation checks and SpMM preflight remain enabled in compatibility tests. The clean upstream checkout is not edited; one copied source is patched, compiled and substituted into a copied static library. The original CUDA object is removed from that copy to avoid duplicate device definitions.

The corrected upstream golden test runs with all of its original checks and its explicitly selected GPU generator. A separate 512-row fixture exports five independently CPU-verified kernel vectors. Two compatibility campaigns each cover 48 cases: two seeds, three row patterns, dimensions 512/2048 and four combinations of block size 64/256 with native SpMM tuning off/on. One uses the pinned CPU-generator default; the other explicitly selects the experimental GPU-hybrid recursive path. All native oracles are enabled. This bounded regression campaign is not a mathematical proof of the entire native solver.

## Native timing boundaries

Performance solves retain native SpMM verification, GPU stage-two annihilation and independent CPU residual/independence checks. Exhaustive internal scalar-oracle mode is reserved for the compatibility campaign, and that difference is explicit in each record. Both timing harnesses enable STATS logging. The GPU-hybrid executable additionally selects `stage2_gpu_mode=true`, retains GPU initialization and its configured CPU cross-check, and keeps the same operator/certificate checks. Detailed phase logs, source transformations and binary hashes identify both executables. The original CPU-mode script is archived and its observations are labelled as a control; GPU annihilation alone does not select the generator backend.

Uniform 512-row cases use five warmups and thirty fresh-process observations for each block/tuning setting and seed. Larger and irregular cases use one warmup and three observations. Failures are retained separately and do not become zero-duration successes. Process wall time includes process launch, matrix-file reading, initialization, preprocessing, all three stages, native certificate checking and output writing. Export and independent Python validation have separate timers. Native stage statistics support phase attribution; they are not substituted for process wall time.

The process is restarted for each observation, so library initialization and CUDA context costs are part of that workload. Results must not be described as a persistent-service solve latency. Peak host RSS is retained. No energy claim is made.

## Original sparse products

Three original exact layouts are compared: one thread per row/word in CSR, one warp per row/word with XOR shuffle reduction in CSR, and column-major ELL with padding. Inputs are 256-bit blocks, stored as four 64-bit words per row. Each trial performs 128 actual applications of A starting from the same seeded input block. Dimensions are 4096 and 16384 with all three row patterns.

The reference applies the same matrix repeatedly using Python integer XOR and compares every output word. Resident direct timing includes all 128 launches and their dispatch gaps. Captured timing executes the same dependency chain in a CUDA graph. Both use five warmups/thirty CUDA-event observations. Vector-transfer host timing adds H2D input and D2H output while retaining the layout. Layout conversion, its H2D upload and storage footprint are separately recorded. Conversion-inclusive derived latency is the measured one-time conversion plus the graph median, rather than a separately sampled distribution.

The original layouts are not integrated into the upstream solver. A measured product win is therefore reported as a product win. Complete native tuning/block comparisons test actual solver costs independently. An optimistic Amdahl ceiling additionally removes whole native phases 1 and 3 from process wall time, which is more generous than removing their SpMM work alone. It bounds an extrapolation and is never labelled an observed integrated-layout solver speedup.

## Analysis and limits

Two input cohorts are reported separately with their raw observations. Repetition count, warmups, correctness settings, binary hashes and timer boundaries remain attached to each population. Host CPU compilation is stopped before comparative timing, and GPU jobs run sequentially. Compatibility-only incidental times are excluded from comparative tables.

The controlled matrices are small for factoring applications, have planted kernel structure, and do not measure relation collection or filtering. The original layouts may favor different degree distributions, and ELL padding cost is part of the result. Conclusions do not establish asymptotic behavior, production factorization throughput or mining income. Original code is MIT licensed; upstream-derived patches retain LGPL-3.0-only and its CUDA linking exception.
