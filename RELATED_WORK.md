# Related work and contribution boundaries

A research project by [Requant Network](https://requant.network).

Coppersmith's [Solving homogeneous linear equations over GF(2) via block Wiedemann algorithm](https://research.ibm.com/publications/solving-homogeneous-linear-equations-over-gf2-via-block-wiedemann-algorithm) introduces blocked sparse binary linear algebra with relevance to the linear-algebra stage of integer factorization. Kaltofen's [analysis of the block Wiedemann method](https://kaltofen.math.ncsu.edu/bibliography/95/Ka95_mathcomp.pdf) discusses projected matrix sequences and generating matrix polynomials. These references motivate separating sparse sequence generation from the dense polynomial-generator work.

The native implementation tested here is the pinned upstream Block Wiedemann project recorded in [results/native-build.json](results/native-build.json). Its author supplies the solver, stage implementations and oracle machinery. This research supplies an independently checkable experimental harness, controlled matrix families, an attributed correction to batched solution reconstruction, independent CPU certificate checks and separate sparse-product layout experiments.

## What is measured

The original CSR, warp-CSR and ELL kernels implement established sparse-layout ideas for a binary XOR product. The contribution is their controlled SM120 comparison over a real 128-step dependency chain, including conversion, graph dispatch and transfers. The layouts are not integrated into the upstream solver, so their timing is not a solver throughput measurement.

The whole native solve includes its generator backend, initialization, preprocessing and reconstruction. An important implementation detail is explicit backend selection: the pinned configuration defaults the generator to CPU mode. GPU annihilation verification alone does not select the GPU generator. The retained CPU-generator measurements and the separately selected GPU-hybrid path answer different questions and remain labelled separately.

The batched reconstruction failure is established by retained vectors and a deterministic matrix generator, rather than by a hash mismatch alone. A scalar vector has zero residual; the failing batched vector has 256 nonzero residual entries. Corrected results retain the native checks and pass an independent CPU residual and independence test.

## Limits

Planted-kernel fixtures permit controlled comparisons but do not model the difficulty of a complete factorization workload. Small-case block-size rankings need not hold on million-row matrices. Amdahl ceilings derived from native phases bound potential integration benefits; they are not measurements of an unimplemented integration. The work makes no mining profitability, cryptanalytic breakthrough or asymptotic performance claim.
