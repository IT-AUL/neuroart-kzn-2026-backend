from typing import Any, Dict, Optional
from app.services.mechanics.base import BaseMechanicValidator, MechanicValidationResult


class NoneMechanicValidator(BaseMechanicValidator):
    """
    Validates 'none' mechanic (point 3: tea & chak-chak).
    Requires no progress; artifact is awarded upon scene interaction.
    """

    def validate(
        self,
        mechanic_params: Dict[str, Any],
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> MechanicValidationResult:
        return MechanicValidationResult(
            success=True,
            score=100.0,
            max_score_reached=100.0,
            message="Scene interacted. No game progress required.",
            details={"mechanic": "none"},
        )
