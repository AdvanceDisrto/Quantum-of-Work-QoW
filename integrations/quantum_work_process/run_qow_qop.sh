#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cargo --version
cargo fmt --all -- --check
cargo test --release --all-targets
cargo build --release
./target/release/quantum_work_process self-test
echo QOW_QOP_SOFTWARE_ACCEPTANCE_PASS
