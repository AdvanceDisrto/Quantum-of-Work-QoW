"""Verified receipt + fresh SMT solver instance."""
from .truthculator_v2 import independently_recheck,verify_dag
from .truthculator import verify_receipt
def independent_check(receipt,pinned_pubkey):
    return independently_recheck(receipt,pinned_pubkey)
