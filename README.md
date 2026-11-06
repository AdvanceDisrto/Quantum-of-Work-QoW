# iNNOVULIS™ Quantum of Work (QoW)

**Patent pending — U.S. Application 19/031,838.** This is an application identifier, not an issued patent or a determination that any particular QoW feature is covered by an allowed claim. Verify the current USPTO record before making legal representations.

## What this review branch implements

Local Z3 SMT adjudication relative to explicitly declared axioms; Ed25519-signed QoW receipts; fresh local Z3 recomputation; multi-parent hash-linked receipt DAG; an experimental radial PNG optical carrier; a PDF attachment carrier; a hash-bound sidecar that preserves original model bytes; and a local QoW Merkle commitment.

**QoW** means a discrete auditable unit of computational work, not a quantum-physics state, coin, transferable token, proof of economic value, or unconditional truth.

Verdicts distinguish PROVEN_TRUE, REFUTED_FALSE (axioms entail negation), NOT_ENTAILED (counterexample exists but negation need not be entailed), INCONSISTENT_AXIOMS, UNKNOWN and INSUFFICIENT_EVIDENCE.

## Run the checks

Requires Python 3.11+, pip, and the dependencies in requirements.txt.

- python -m pip install -r requirements.txt
- PYTHONPATH=. python -m unittest discover -s tests -v
- PYTHONPATH=. python run_e2e.py

GitHub Actions executes 14 unit tests plus a fresh end-to-end signed receipt, optical PNG round trip and local Merkle commitment. Generated receipts use random signing keys; their root hashes are not expected to equal the previously reported sha256:1135bc9e... from a separate local run.

## Trust boundaries

- Ed25519 verifies a signed solver **assertion**; a fresh Z3 run checks the formal claim separately, but is not an independently checkable proof certificate.
- This is a local QoW Merkle construction, **not** a claim of compatibility with Proof-of-Process-PoP's production domain-separated Merkle algorithm.
- An ipQR PNG round trip does **not** establish real printed-paper or smartphone-camera acceptance.
- TEE-backed execution, independent remote witnesses, RFC 3161 timestamping, ZK proofs, consensus, payments, physical measurements and cloud deployment remain **NOT_VERIFIED**.
- Sidecar integrity is not an inference-engine runtime enforcement guarantee.
- This branch is review-only. No automatic merge or production deployment.

## PoP bridge

The PoP repository has a separate integration adapter under integrations/qow_pop_bridge.py (PR #56); the adapter's positive test callback is a test double. A real Z3 callback and end-to-end schema verification remain necessary before claims of integrated production enforcement.
