import uuid
import pytest
from httpx import AsyncClient
from app.services.mechanics.tap_climb import TapClimbMechanicValidator
from app.services.mechanics.trace import TraceMechanicValidator


def test_tap_climb_validator_math():
    validator = TapClimbMechanicValidator()
    params = {
        "gain_per_tap": 4.0,
        "decay_per_interval": 1.0,
        "decay_interval_seconds": 0.3,  # decay rate = 3.33 pts/sec
        "success_threshold": 100.0,
    }

    # Case A: Tapping fast (35 taps in 5 seconds -> rate = 7 taps/sec, gain=140, decay=16.6 -> score ~123.3)
    res_fast = validator.validate(params, {"taps_count": 35, "duration_seconds": 5.0})
    assert res_fast.success is True
    assert res_fast.score >= 100.0

    # Case B: Tapping too slowly (10 taps in 20 seconds -> rate = 0.5 taps/sec, gain=40, decay=66.6 -> score 0)
    res_slow = validator.validate(params, {"taps_count": 10, "duration_seconds": 20.0})
    assert res_slow.success is False
    assert res_slow.score < 100.0

    # Case C: Realistic timestamps sequence where user climbs up
    # 25 taps separated by 0.1s (total 2.5s -> gain = 100, decay = 8.3 -> reaches ~92)
    # 30 taps separated by 0.1s (total 3.0s -> gain = 120, decay = 10 -> reaches 110)
    timestamps = [i * 0.1 for i in range(30)]
    res_ts = validator.validate(params, {"tap_timestamps": timestamps})
    assert res_ts.success is True
    assert res_ts.max_score_reached >= 100.0


def test_trace_validator_geometry():
    validator = TraceMechanicValidator()
    
    # Concrete reference path from (0.1, 0.1) to (0.9, 0.1)
    params = {
        "path": [{"x": 0.1, "y": 0.1}, {"x": 0.9, "y": 0.1}],
        "tolerance": 20.0,  # pixels on 1000px screen (0.02 normalized)
    }

    # User draws straight along the line
    good_user_path = [
        {"x": 0.1, "y": 0.1},
        {"x": 0.5, "y": 0.105},  # 5px deviation
        {"x": 0.9, "y": 0.1},
    ]
    res_good = validator.validate(params, {"user_path": good_user_path, "screen_width": 1000.0})
    assert res_good.success is True
    assert res_good.details["max_deviation_px"] <= 20.0

    # User draws way off the line (e.g. y = 0.3 -> 200px off)
    bad_user_path = [
        {"x": 0.1, "y": 0.1},
        {"x": 0.5, "y": 0.35},  # 250px deviation
        {"x": 0.9, "y": 0.1},
    ]
    res_bad = validator.validate(params, {"user_path": bad_user_path, "screen_width": 1000.0})
    assert res_bad.success is False
    assert res_bad.details["max_deviation_px"] > 20.0


def test_tap_climb_grace_period():
    validator = TapClimbMechanicValidator()
    params = {
        "gain_per_tap": 4.0,
        "decay_per_interval": 1.0,
        "decay_interval_seconds": 0.3,
        "grace_period_seconds": 1.0,
        "success_threshold": 100.0,
    }

    # Pauses of 0.8s between taps are within 1.0s grace period -> no decay
    timestamps = [i * 0.8 for i in range(26)]
    res = validator.validate(params, {"tap_timestamps": timestamps})
    assert res.success is True
    assert res.max_score_reached >= 100.0

    # Long pauses of 2.5s (> 1.0s grace period) -> decays 1.5s / 0.3 = 5 points per tap interval
    timestamps_slow = [i * 2.5 for i in range(10)]
    res_slow = validator.validate(params, {"tap_timestamps": timestamps_slow})
    assert res_slow.success is False


def test_tap_strike_validator():
    from app.services.mechanics.tap_strike import TapStrikeMechanicValidator

    strike_validator = TapStrikeMechanicValidator()
    res1 = strike_validator.validate({}, {"hit_wedge": True})
    assert res1.success is True

    res2 = strike_validator.validate({}, {"strike_performed": True})
    assert res2.success is True

    res3 = strike_validator.validate({}, {"taps_count": 0, "hit_wedge": False})
    assert res3.success is False


@pytest.mark.asyncio
async def test_api_trace_with_wedge_strike(client: AsyncClient):
    session_id = str(uuid.uuid4())
    headers = {"X-Session-ID": session_id}

    payload = {
        "user_path": [{"x": 0.1, "y": 0.2}, {"x": 0.5, "y": 0.5}],
        "hit_wedge": True,
    }
    response = await client.post("/progress/loc_1_shurale", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_new_unlock"] is True
    assert data["artifact"]["id"] == "klin"
    assert data["validation"]["details"]["hit_wedge"] is True


@pytest.mark.asyncio
async def test_api_tap_climb_success(client: AsyncClient):
    session_id = str(uuid.uuid4())
    headers = {"X-Session-ID": session_id}

    # Submit sufficient taps to climb the pole
    payload = {
        "taps_count": 40,
        "duration_seconds": 6.0,
    }
    response = await client.post("/progress/loc_2_sabantuy", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_new_unlock"] is True
    assert data["artifact"]["id"] == "polotentse"
    assert data["validation"]["success"] is True


@pytest.mark.asyncio
async def test_api_tap_climb_failure_under_threshold(client: AsyncClient):
    session_id = str(uuid.uuid4())
    headers = {"X-Session-ID": session_id}

    # Insufficient taps to beat the decay rate
    payload = {
        "taps_count": 5,
        "duration_seconds": 15.0,
    }
    response = await client.post("/progress/loc_2_sabantuy", json=payload, headers=headers)
    assert response.status_code == 422
    data = response.json()
    assert "validation failed" in data["detail"]["error"]


@pytest.mark.asyncio
async def test_api_verify_simulation_endpoint(client: AsyncClient):
    # Verify simulation without modifying DB
    payload = {
        "taps_count": 35,
        "duration_seconds": 5.0,
    }
    response = await client.post("/progress/verify/loc_2_sabantuy", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["score"] >= 100.0


def test_none_mechanic_validator_and_fallback():
    from app.services.mechanics import get_mechanic_validator
    from app.services.mechanics.none_mechanic import NoneMechanicValidator

    validator = NoneMechanicValidator()
    res1 = validator.validate({}, None)
    assert res1.success is True
    assert res1.score == 100.0

    res2 = validator.validate({}, {"arbitrary_key": "val"})
    assert res2.success is True

    # Fallback to NoneMechanicValidator on unknown mechanic name
    fallback_val = get_mechanic_validator("completely_unknown_mechanic")
    assert isinstance(fallback_val, NoneMechanicValidator)


def test_trace_placeholder_path_and_empty_handling():
    validator = TraceMechanicValidator()

    # Artist placeholder string path with completed=True
    res_placeholder_ok = validator.validate({"path": "contour_mesh_placeholder"}, {"completed": True})
    assert res_placeholder_ok.success is True
    assert res_placeholder_ok.score == 100.0

    # Artist placeholder string path with completed=False
    res_placeholder_fail = validator.validate({"path": "contour_mesh_placeholder"}, {"completed": False})
    assert res_placeholder_fail.success is False

    # Empty user path without completed flag
    res_empty = validator.validate({"path": [{"x": 0.1, "y": 0.1}]}, {"user_path": []})
    assert res_empty.success is False


@pytest.mark.asyncio
async def test_api_verify_simulation_failure_returns_200_with_false(client: AsyncClient):
    # Verify that the simulation endpoint returns HTTP 200 with success=False, NOT a 422 HTTP exception
    payload = {
        "taps_count": 3,
        "duration_seconds": 12.0,
    }
    response = await client.post("/progress/verify/loc_2_sabantuy", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["score"] < 100.0


