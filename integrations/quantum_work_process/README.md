# QoW + QoP unified software acceptance v0.2

Run `bash run_qow_qop.sh` with Rust stable. A single binary executes a 16-lane f32 FMA fixture, rejects nonfinite results and over-budget **reported** power values, and signs three causally ordered QoP receipts. Verifier independently checks QoW metadata/digests, all chain roots, sequence/ticks, and Ed25519 signatures against an **externally trusted** key. This is a software demonstration, **not** real SIMT/NPU execution, independently measured power, a physical Chronos clock, CIH approval, or a quantum-resistant signature.

The test key [0x33;32] is **public and insecure for production**. All output is `PENDING PROOF OF PROCESS — CIH VERIFICATION`. Receipt output is `build_qow_qop/qow_qop_pending_chain.json`.

**Post-quantum gate:** ML-DSA and ML-KEM are **not implemented by this Rust crate**. Ed25519 is classical. Production post-quantum claims require an independently validated FIPS 203/204 backend, trusted key lifecycle, interoperability tests, and separate CI. Do not relabel this build as post-quantum.

This additive integration intentionally does not modify existing Python QoW services or any production PoP/DEPC interfaces.
