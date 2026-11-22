from typing import Tuple
import sympy as sp
from ssi_core.interfaces import BaseConstraint, BaseValidator
from ssi_core.models import ClaimNode


class ConservationOfEnergyConstraint(BaseConstraint):
    constraint_id = "K-PHYS-ENERGY-01"

    def check(self, claim: ClaimNode) -> Tuple[bool, str]:
        if claim.metadata.get("violates_energy_conservation", False):
            return False, "Proposal violates local conservation of energy."
        return True, "Consistent with energy conservation."


class SymPyIdentityValidator(BaseValidator):
    validator_id = "V-SYMPY-ALGEBRA"

    def validate(self, claim: ClaimNode) -> Tuple[bool, str]:
        lhs_str = claim.metadata.get("lhs")
        rhs_str = claim.metadata.get("rhs")
        if not lhs_str or not rhs_str:
            return False, "Missing symbolic 'lhs' or 'rhs' expressions in claim metadata."

        try:
            lhs = sp.sympify(lhs_str)
            rhs = sp.sympify(rhs_str)
            diff = sp.simplify(lhs - rhs)
            if diff == 0:
                return True, f"Verified symbolic identity: simplify(({lhs_str}) - ({rhs_str})) == 0"
            return False, f"Symbolic mismatch: residual = {diff}"
        except Exception as exc:
            return False, f"SymPy parsing error: {exc}"
