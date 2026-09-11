from typing import Any, Dict, Optional
from app.services.mechanics.base import BaseMechanicValidator, MechanicValidationResult


class TapStrikeMechanicValidator(BaseMechanicValidator):
    """
    Validates the 'tap_strike' / 'strike' mechanic (e.g. axe strike on wedge).
    Accepts confirmation of hit/strike or strike timing telemetry.
    """

    def validate(
        self,
        mechanic_params: Dict[str, Any],
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> MechanicValidationResult:
        if not submission_data:
            return MechanicValidationResult(
                success=True,
                score=100.0,
                max_score_reached=100.0,
                message="Strike completed (default telemetry accepted)",
                details={"mode": "telemetry_omitted"},
            )

        strike_performed = (
            submission_data.get("strike_performed")
            or submission_data.get("hit_wedge")
            or submission_data.get("completed", False)
        )
        taps_count = submission_data.get("taps_count", 0)

        if strike_performed or taps_count >= 1:
            return MechanicValidationResult(
                success=True,
                score=100.0,
                max_score_reached=100.0,
                message="Target struck successfully! Wedge dislodged.",
                details={"strike_performed": True, "taps_count": taps_count},
            )

        return MechanicValidationResult(
            success=False,
            score=0.0,
            max_score_reached=0.0,
            message="Strike action not detected (expected strike_performed=true or hit_wedge=true)",
            details=submission_data,
        )
