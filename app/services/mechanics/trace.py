import math
from typing import Any, Dict, List, Optional, Tuple
from app.services.mechanics.base import BaseMechanicValidator, MechanicValidationResult


def point_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def min_dist_to_segment(p: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Distance from point p to line segment a-b."""
    ab_len_sq = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    if ab_len_sq == 0.0:
        return point_distance(p, a)
    # Project point p onto segment a-b, clamped between 0 and 1
    t = max(0.0, min(1.0, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / ab_len_sq))
    projection = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return point_distance(p, projection)


class TraceMechanicValidator(BaseMechanicValidator):
    """
    Validates the 'trace' contour finger-drawing mechanic.
    
    Formula & parameters:
      - path: array of normalized (0-1) points defining the target log crack contour
      - tolerance: allowed deviation in pixels (or normalized units)
    """

    def validate(
        self,
        mechanic_params: Dict[str, Any],
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> MechanicValidationResult:
        raw_path = mechanic_params.get("path")
        tolerance_px = float(mechanic_params.get("tolerance", 20.0))

        if not submission_data:
            # If no telemetry passed (simple complete), accept in demo mode
            return MechanicValidationResult(
                success=True,
                score=100.0,
                max_score_reached=100.0,
                message="Trace completed (default telemetry accepted)",
                details={"mode": "telemetry_omitted"},
            )

        user_points_raw = submission_data.get("user_path")
        if not user_points_raw:
            # Fallback if other client reported success
            if submission_data.get("completed", False):
                return MechanicValidationResult(
                    success=True,
                    score=100.0,
                    max_score_reached=100.0,
                    message="Trace completion verified by client",
                    details=submission_data,
                )
            return MechanicValidationResult(
                success=False,
                score=0.0,
                max_score_reached=0.0,
                message="Missing 'user_path' coordinates for trace mechanic",
                details=submission_data,
            )

        # Parse user points [(x, y), ...]
        user_points: List[Tuple[float, float]] = []
        for pt in user_points_raw:
            if isinstance(pt, dict):
                user_points.append((float(pt.get("x", 0.0)), float(pt.get("y", 0.0))))
            elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
                user_points.append((float(pt[0]), float(pt[1])))

        if len(user_points) < 2:
            return MechanicValidationResult(
                success=False,
                score=0.0,
                max_score_reached=0.0,
                message="Trace requires at least 2 points to form a path",
                details={"points_count": len(user_points)},
            )

        # Case 1: Reference path is still an artist placeholder string (before 3D model export)
        if isinstance(raw_path, str):
            # Verify coordinates are in normalized range 0.0 - 1.0
            in_bounds = all(0.0 <= p[0] <= 1.0 and 0.0 <= p[1] <= 1.0 for p in user_points)
            if in_bounds:
                return MechanicValidationResult(
                    success=True,
                    score=100.0,
                    max_score_reached=100.0,
                    message="Trace contour accepted (validated normalized bounds 0.0 - 1.0)",
                    details={
                        "points_count": len(user_points),
                        "reference_status": "placeholder_artist_export",
                    },
                )

        # Case 2: Reference path is a concrete list of points
        ref_points: List[Tuple[float, float]] = []
        if isinstance(raw_path, list):
            for pt in raw_path:
                if isinstance(pt, dict):
                    ref_points.append((float(pt.get("x", 0.0)), float(pt.get("y", 0.0))))
                elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    ref_points.append((float(pt[0]), float(pt[1])))

        if not ref_points or len(ref_points) < 2:
            # If reference path not yet populated, accept valid non-empty user trace
            return MechanicValidationResult(
                success=True,
                score=100.0,
                max_score_reached=100.0,
                message="Trace accepted (reference path not specified)",
                details={"points_count": len(user_points)},
            )

        # Compare user trace against reference segments
        # Screen normalized tolerance: assume standard viewport ~1000px, so 20px ~ 0.02
        # Or if viewport dimensions passed in submission_data:
        screen_width = float(submission_data.get("screen_width", 1000.0))
        normalized_tolerance = tolerance_px / screen_width

        deviations: List[float] = []
        for up in user_points:
            min_d = float("inf")
            for i in range(len(ref_points) - 1):
                d = min_dist_to_segment(up, ref_points[i], ref_points[i + 1])
                if d < min_d:
                    min_d = d
            deviations.append(min_d)

        max_dev = max(deviations)
        mean_dev = sum(deviations) / len(deviations)
        max_dev_px = max_dev * screen_width

        is_accurate = max_dev_px <= tolerance_px

        accuracy_score = max(0.0, round(100.0 - (mean_dev * screen_width), 1))

        return MechanicValidationResult(
            success=is_accurate,
            score=accuracy_score,
            max_score_reached=accuracy_score,
            message=(
                f"Trace successful! Max deviation: {max_dev_px:.1f}px (tolerance: {tolerance_px:.0f}px)"
                if is_accurate
                else f"Finger deviated too far: {max_dev_px:.1f}px (max allowed: {tolerance_px:.0f}px)"
            ),
            details={
                "max_deviation_px": round(max_dev_px, 2),
                "tolerance_px": tolerance_px,
                "user_points_count": len(user_points),
                "ref_points_count": len(ref_points),
                "accuracy_score": accuracy_score,
            },
        )
