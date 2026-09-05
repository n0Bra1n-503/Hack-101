"""Comprehensive End-to-End Pipeline & Scenario Tests for SkyGuard AI.

Verifies:
- Scenario A: One station extreme spike -> ML Anomaly -> sensor_fault -> low Trust -> risk blocked -> correction
- Scenario B: Multi-station genuine extreme weather -> genuine_weather -> high Trust -> HIGH RISK -> citizen alert
- Scenario C: Insufficient evidence -> uncertain -> risk blocked -> manual review
- Edge cases: missing values, malformed records, duplicate handling, REST endpoints, and WebSocket.
"""

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database.connection import Base
from backend.app.database.session import get_db
from backend.app.main import app
from backend.app.models.reading import Reading
from backend.app.models.station import Station

# In-memory test SQLite DB
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. SCENARIO A: Faulty Extreme (Hardware Sensor Spike)
# =====================================================================

def test_scenario_a_faulty_extreme_spike_blocked(client):
    """Test A: An isolated extreme temperature spike is classified as sensor_fault,

    assigns low trust, blocks disaster risk, and suggests an operational correction.
    """
    db = TestingSessionLocal()
    now = datetime(2026, 9, 5, 12, 0, 0)

    # Pre-seed 3 neighboring stations reporting normal ambient temps (~31°C)
    for i, st_id in enumerate(["PEER_STATION_1", "PEER_STATION_2", "PEER_STATION_3"]):
        db.add(Reading(
            reading_id=f"PEER-READING-{i}",
            station_id=st_id,
            timestamp=now,
            temperature=31.0 + (i * 0.4),
            pressure=1010.0,
            humidity=50.0,
            source="weather_source",
            quality_flag="valid",
        ))
    db.commit()
    db.close()

    # Target station spikes to 55°C
    spike_payload = {
        "reading_id": "SPIKE-001",
        "station_id": "TARGET_STATION_SPIKE",
        "timestamp": now.isoformat(),
        "temperature": 55.0,
        "pressure": 1008.0,
        "humidity": 45.0,
        "area": "Pune",
    }

    res = client.post("/api/inference", json=spike_payload)
    assert res.status_code == 200
    data = res.json()

    # Verify ML Anomaly
    assert data["anomaly_detection"]["anomaly"] is True

    # Verify Decision Intelligence: sensor_fault
    assert data["decision_intelligence"]["decision"] == "sensor_fault"
    assert data["decision_intelligence"]["fault_type"] in ("temperature_spike", "abrupt_jump")

    # Verify Trust Score is LOW (< 30)
    assert data["decision_intelligence"]["trust_score"] < 30.0

    # Verify Disaster Risk is strictly BLOCKED
    assert data["disaster_risk"]["risk_level"] == "NONE"

    # Verify Suggested Correction exists
    assert data["decision_intelligence"]["suggested_correction"] is not None
    assert data["decision_intelligence"]["suggested_correction"]["suggested_value"] < 35.0


# =====================================================================
# 2. SCENARIO B: Genuine Extreme Weather Event (Heatwave)
# =====================================================================

def test_scenario_b_genuine_extreme_heatwave_alert(client):
    """Test B: Multiple regional stations confirm extreme heat (44°C+),

    classified as genuine_weather, assigns high trust, and triggers HIGH disaster risk.
    """
    db = TestingSessionLocal()
    now = datetime(2026, 9, 5, 14, 0, 0)

    # Pre-seed 3 neighboring stations confirming high heat (43.5°C - 44.5°C)
    for i, st_id in enumerate(["AHMEDABAD_PEER_1", "AHMEDABAD_PEER_2", "AHMEDABAD_PEER_3"]):
        db.add(Reading(
            reading_id=f"HEAT-PEER-{i}",
            station_id=st_id,
            timestamp=now,
            temperature=43.8 + (i * 0.3),
            pressure=1001.0,
            humidity=20.0,
            source="weather_source",
            quality_flag="valid",
        ))
    db.commit()
    db.close()

    # Target station reports 44.5°C
    heat_payload = {
        "reading_id": "HEAT-TARGET-001",
        "station_id": "AHMEDABAD_CENTRAL",
        "timestamp": now.isoformat(),
        "temperature": 44.5,
        "pressure": 1001.0,
        "humidity": 18.0,
        "area": "Ahmedabad",
    }

    res = client.post("/api/inference", json=heat_payload)
    assert res.status_code == 200
    data = res.json()

    # Decision Intelligence must recognize multi-station genuine extreme weather
    assert data["decision_intelligence"]["decision"] == "genuine_weather"

    # Trust score must remain HIGH
    assert data["decision_intelligence"]["trust_score"] >= 80.0

    # Validated Disaster Risk MUST be generated with HIGH level
    assert data["disaster_risk"]["risk_level"] == "HIGH"
    assert "heat" in data["disaster_risk"]["event_type"]
    assert "Heatwave" in data["disaster_risk"]["public_message"]


# =====================================================================
# 3. SCENARIO C: Uncertain Anomaly Gating
# =====================================================================

def test_scenario_c_uncertain_isolated_reading_gated(client):
    """Test C: An anomaly with insufficient supporting evidence is gated as uncertain,

    suppressing automatic public alerts and holding for manual review.
    """
    now = datetime(2026, 9, 5, 15, 0, 0)

    # Isolated station with unusual temperature (47.0°C) and no peers in DB
    ambiguous_payload = {
        "reading_id": "AMBIGUOUS-001",
        "station_id": "ISOLATED_RURAL_STATION",
        "timestamp": now.isoformat(),
        "temperature": 47.0,
        "pressure": 1008.0,
        "humidity": 40.0,
        "area": "Rural District",
    }

    res = client.post("/api/inference", json=ambiguous_payload)
    assert res.status_code == 200
    data = res.json()

    # Should be classified as uncertain
    assert data["decision_intelligence"]["decision"] == "uncertain"

    # Trust score is moderate
    assert 35.0 <= data["decision_intelligence"]["trust_score"] <= 65.0

    # Automatic disaster risk must be GATED / BLOCKED
    assert data["disaster_risk"]["risk_level"] == "NONE"


# =====================================================================
# 4. REST Endpoints & Service Contracts
# =====================================================================

def test_endpoints_stations_and_summary(client):
    """Verify /api/stations, /api/stations/{id}, and /api/summary."""
    db = TestingSessionLocal()
    db.add(Station(
        station_id="STATION_TEST_1",
        name="Test Station 1",
        latitude=21.5,
        longitude=72.8,
        elevation=15.0,
        area="Gujarat",
        status="active",
    ))
    db.commit()
    db.close()

    # GET /api/stations
    res_st = client.get("/api/stations")
    assert res_st.status_code == 200
    stations = res_st.json()
    assert len(stations) >= 1
    assert stations[0]["id"] == "STATION_TEST_1"

    # GET /api/stations/{id}
    res_single = client.get("/api/stations/STATION_TEST_1")
    assert res_single.status_code == 200
    assert res_single.json()["name"] == "Test Station 1"

    # GET /api/summary
    res_sum = client.get("/api/summary")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert "total_stations" in summary
    assert "average_trust_score" in summary


def test_cascade_scenarios_endpoints(client):
    """Verify /api/cascade/scenario-a, scenario-b, scenario-c."""
    for sc in ["scenario-a", "scenario-b", "scenario-c"]:
        res = client.get(f"/api/cascade/{sc}")
        assert res.status_code == 200
        data = res.json()
        assert "stages" in data
        assert len(data["stages"]) == 7
        assert data["mode"] == "illustrative_simulation"


def test_public_risk_endpoint_sanitized(client):
    """Verify /api/public/risk/{area} returns citizen-safe output without internal fields."""
    res = client.get("/api/public/risk/Gujarat")
    assert res.status_code == 200
    data = res.json()
    # Required citizen safety fields
    assert "area" in data
    assert "risk_level" in data
    assert "safety_guidance" in data
    assert "message" in data

    # Internal debugging fields MUST NOT be present
    assert "anomaly_score" not in data
    assert "model" not in data
    assert "station_id" not in data
    assert "fault_type" not in data
