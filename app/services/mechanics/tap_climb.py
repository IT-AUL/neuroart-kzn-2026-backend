import math
from typing import Any, Dict, List, Optional
from app.services.mechanics.base import BaseMechanicValidator, MechanicValidationResult


class TapClimbMechanicValidator(BaseMechanicValidator):
    """
    Validates the 'tap_climb' pole-climbing mechanic.
    
    Formula from storyboard.md:
      - gain_per_tap: 4 (each tap moves the climber up)
      - decay_per_interval: 1 (slips down by 1 point)
      - decay_interval_seconds: 0.3 (slip occurs every 0.3s)
      - success_threshold: 100 (climber reaches the top and grabs the prize)
    """

    def validate(
        self,
        mechanic_params: Dict[str, Any],
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> MechanicValidationResult:
        gain_per_tap = float(mechanic_params.get("gain_per_tap", 4.0))
        decay_per_interval = float(mechanic_params.get("decay_per_interval", 1.0))
        decay_interval = float(mechanic_params.get("decay_interval_seconds", 0.3))
        grace_period = float(mechanic_params.get("grace_period_seconds", 1.0))
        threshold = float(mechanic_params.get("success_threshold", 100.0))

        if not submission_data:
            # If no telemetry provided, accept completion in demo mode
            return MechanicValidationResult(
                success=True,
                score=threshold,
                max_score_reached=threshold,
                message="Tap climb completed (default telemetry accepted)",
                details={"mode": "telemetry_omitted"},
            )

        # Check explicit score claimed
        claimed_score = submission_data.get("score")
        if claimed_score is not None and float(claimed_score) >= threshold:
            return MechanicValidationResult(
                success=True,
                score=float(claimed_score),
                max_score_reached=float(claimed_score),
                message=f"Victory! Climber reached threshold {threshold:.0f} points.",
                details={"claimed_score": claimed_score},
            )

        # 1. Full simulation with tap timestamps: [t0, t1, t2, ...]
        timestamps: Optional[List[float]] = submission_data.get("tap_timestamps")
        if timestamps and len(timestamps) > 0:
            sorted_times = sorted([float(t) for t in timestamps])
            current_score = 0.0
            peak_score = 0.0
            last_time = sorted_times[0]

            for t in sorted_times:
                elapsed = max(0.0, t - last_time)
                # Player only starts slipping if idle time exceeds grace_period
                if elapsed > grace_period:
                    decay_ticks = (elapsed - grace_period) / decay_interval
                    current_score = max(0.0, current_score - (decay_ticks * decay_per_interval))
                current_score += gain_per_tap
                if current_score > peak_score:
                    peak_score = current_score
                last_time = t

            reached = peak_score >= threshold
            return MechanicValidationResult(
                success=reached,
                score=round(current_score, 2),
                max_score_reached=round(peak_score, 2),
                message=(
                    f"Victory! Climber reached top ({peak_score:.1f}/{threshold:.0f})"
                    if reached
                    else f"Climber slipped down! Max reached: {peak_score:.1f}/{threshold:.0f}"
                ),
                details={
                    "total_taps": len(sorted_times),
                    "duration_seconds": round(sorted_times[-1] - sorted_times[0], 2) if len(sorted_times) > 1 else 0.0,
                    "peak_score": round(peak_score, 2),
                    "final_score": round(current_score, 2),
                    "grace_period_seconds": grace_period,
                },
            )

        # 2. Rate simulation with taps_count and duration_seconds
        taps_count = submission_data.get("taps_count")
        duration_seconds = submission_data.get("duration_seconds")

        if taps_count is not None and duration_seconds is not None:
            taps = int(taps_count)
            duration = max(0.1, float(duration_seconds))

            total_gain = taps * gain_per_tap
            decay_rate_per_sec = decay_per_interval / decay_interval

            avg_interval = duration / max(1, taps)
            if avg_interval > grace_period:
                unbuffered_decay_time = (avg_interval - grace_period) * taps
                total_decay = unbuffered_decay_time * decay_rate_per_sec
            else:
                total_decay = 0.0

            effective_score = max(0.0, total_gain - total_decay)
            reached = effective_score >= threshold

            return MechanicValidationResult(
                success=reached,
                score=round(effective_score, 2),
                max_score_reached=round(max(effective_score, threshold if reached else total_gain), 2),
                message=(
                    f"Victory! Climber grabbed the prize (effective score: {effective_score:.1f}/{threshold:.0f})"
                    if reached
                    else f"Climber fell down! Taps: {taps}, duration: {duration:.1f}s, net score: {effective_score:.1f}/{threshold:.0f}"
                ),
                details={
                    "taps_count": taps,
                    "duration_seconds": duration,
                    "taps_per_second": round(taps / duration, 2),
                    "grace_period_seconds": grace_period,
                    "effective_score": round(effective_score, 2),
                },
            )

        # Fallback if unknown payload passed
        return MechanicValidationResult(
            success=False,
            score=0.0,
            max_score_reached=0.0,
            message="Invalid tap_climb submission: provide 'tap_timestamps' or ('taps_count' and 'duration_seconds')",
            details=submission_data,
        )
