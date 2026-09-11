from typing import Dict
from app.services.mechanics.base import BaseMechanicValidator, MechanicValidationResult
from app.services.mechanics.none_mechanic import NoneMechanicValidator
from app.services.mechanics.tap_climb import TapClimbMechanicValidator
from app.services.mechanics.tap_strike import TapStrikeMechanicValidator
from app.services.mechanics.trace import TraceMechanicValidator

VALIDATORS: Dict[str, BaseMechanicValidator] = {
    "trace": TraceMechanicValidator(),
    "tap_climb": TapClimbMechanicValidator(),
    "tap_strike": TapStrikeMechanicValidator(),
    "strike": TapStrikeMechanicValidator(),
    "none": NoneMechanicValidator(),
}


def get_mechanic_validator(mechanic_type: str) -> BaseMechanicValidator:
    """Return the validator for a specific quest mechanic."""
    return VALIDATORS.get(mechanic_type, NoneMechanicValidator())


__all__ = [
    "BaseMechanicValidator",
    "MechanicValidationResult",
    "TraceMechanicValidator",
    "TapClimbMechanicValidator",
    "TapStrikeMechanicValidator",
    "NoneMechanicValidator",
    "get_mechanic_validator",
]

