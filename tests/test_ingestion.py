"""Automated tests for Phase 1 weather reading ingestion, validation, persistence, and retrieval.

Covers canonical contract tests, real AWS schema reconciliation, nullable measurement
channels, extreme weather preservation, Bhadar dam station disambiguation, and duplicate handling.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.database.connection import Base
from backend.app.database.session import get_db
from backend.app.main import app

# In-memory SQLite for isolated test execution
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create fresh database tables before each test and tear down after."""
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
    """TestClient fixture for making HTTP requests against the FastAPI app."""
    return TestClient(app)


# Canonical test payload conforming strictly to the Phase-0 / Phase-1 data contract
SAMPLE_READING = {
    "reading_id": "R123",
    "station_id": "AWS-104",
    "timestamp": "2026-09-04T10:00:00",
    "temperature": 31.2,
    "pressure": 1004.1,
    "humidity": 48.2,
    "wind_speed": 12.4,
    "wind_direction": 220.0,
    "rainfall": 0.0,
    "solar_radiation": 650.0,
    "latitude": 28.61,
    "longitude": 77.21,
    "area": "Delhi",
    "elevation": 216.0,
    "source": "weather_source",
    "quality_flag": "valid",
}


# =====================================================================
# 1. Baseline Service & Health Tests
# =====================================================================

def test_1_health_endpoint(client):
    """Verify health endpoint returns operational status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "skyguard-backend"


def test_root_endpoint(client):
    """Verify root endpoint returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "SkyGuard AI backend is running" in data["message"]


# =====================================================================
# 2. Schema Reconciliation & Structural Tests (14 Requirements)
# =====================================================================

def test_req1_complete_valid_observation(client):
    """TEST REQ 1: Verify a fully populated valid weather reading is accepted and persisted."""
    response = client.post("/api/readings", json=SAMPLE_READING)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Reading accepted and stored"
    stored = data["reading"]
    assert stored["reading_id"] == "R123"
    assert stored["station_id"] == "AWS-104"
    assert stored["temperature"] == 31.2
    assert stored["pressure"] == 1004.1
    assert stored["humidity"] == 48.2
    assert stored["wind_speed"] == 12.4
    assert stored["wind_direction"] == 220.0
    assert stored["rainfall"] == 0.0
    assert stored["solar_radiation"] == 650.0
    assert stored["elevation"] == 216.0


def test_req2_missing_temperature_accepted(client):
    """TEST REQ 2: Verify missing temperature (None/omitted) is accepted and preserved as NULL."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-TEMP"
    payload["temperature"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["temperature"] is None


def test_req3_missing_humidity_accepted(client):
    """TEST REQ 3: Verify missing humidity is accepted and preserved as NULL."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-HUMID"
    payload["humidity"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["humidity"] is None


def test_req4_missing_pressure_accepted(client):
    """TEST REQ 4: Verify missing pressure is accepted and preserved as NULL."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-PRESS"
    payload["pressure"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["pressure"] is None


def test_req5_missing_rainfall_accepted(client):
    """TEST REQ 5: Verify missing rainfall is accepted and preserved as NULL (NOT 0.0)."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-RAIN"
    payload["rainfall"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["rainfall"] is None
    assert stored["rainfall"] != 0.0


def test_req6_missing_wind_speed_accepted(client):
    """TEST REQ 6: Verify missing wind_speed is accepted and preserved as NULL."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-WIND"
    payload["wind_speed"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["wind_speed"] is None


def test_req7_missing_elevation_accepted(client):
    """TEST REQ 7: Verify missing elevation is accepted and preserved as NULL."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-ELEV"
    payload["elevation"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["elevation"] is None


def test_req8_missing_wind_direction_accepted(client):
    """TEST REQ 8: Verify missing wind_direction is accepted and preserved as NULL."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-WDIR"
    payload["wind_direction"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["wind_direction"] is None


def test_req9_missing_solar_radiation_accepted(client):
    """TEST REQ 9: Verify missing solar_radiation is accepted and preserved as NULL."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-NO-SOLAR"
    payload["solar_radiation"] = None

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["solar_radiation"] is None


def test_req10_extreme_temperature_accepted(client):
    """TEST REQ 10: Verify extreme meteorological temperature (55.0°C) is accepted structurally."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-EXTREME-55"
    payload["temperature"] = 55.0

    response = client.post("/api/readings", json=payload)
    assert response.status_code == 201
    stored = response.json()["reading"]
    assert stored["temperature"] == 55.0


def test_req11_duplicate_physical_observation_rejected(client):
    """TEST REQ 11: Verify duplicate physical observation triggers HTTP 409 conflict."""
    payload = SAMPLE_READING.copy()
    payload["reading_id"] = "R-DUP-1"

    # First submission succeeds
    response1 = client.post("/api/readings", json=payload)
    assert response1.status_code == 201

    # Second submission with same reading_id rejected
    response2 = client.post("/api/readings", json=payload)
    assert response2.status_code == 409
    assert response2.json()["detail"]["error"] == "duplicate_reading"

    # Third submission with different reading_id but same (station_id, timestamp) rejected
    payload_new_id = payload.copy()
    payload_new_id["reading_id"] = "R-DUP-2"
    response3 = client.post("/api/readings", json=payload_new_id)
    assert response3.status_code == 409
    assert response3.json()["detail"]["error"] == "duplicate_reading"


def test_req12_two_bhadar_dam_stations_disambiguated(client):
    """TEST REQ 12: Verify two distinct physical stations sharing 'Bhadar dam' name are both stored without collision."""
    # Location 1: Rajkot district (Lat: 21.8100, Lon: 70.7689)
    bhadar_rajkot = {
        "station_id": "Bhadar dam",
        "timestamp": "2024-01-01T00:00:00",
        "relative_humidity": 73.0,
        "atmospheric_pressure": 1001.35,
        "rainfall": 287.0,
        "latitude": 21.81,
        "longitude": 70.76888889,
        "altitude": None,
    }

    # Location 2: Aravalli district (Lat: 23.3250, Lon: 73.6917)
    bhadar_aravalli = {
        "station_id": "Bhadar dam",
        "timestamp": "2024-01-01T00:00:00",
        "temperature": 18.85,
        "wind_speed": 2.15,
        "latitude": 23.325,
        "longitude": 73.69166667,
        "altitude": None,
    }

    # Both ingested at exact same timestamp
    res1 = client.post("/api/readings", json=bhadar_rajkot)
    assert res1.status_code == 201
    stored1 = res1.json()["reading"]

    res2 = client.post("/api/readings", json=bhadar_aravalli)
    assert res2.status_code == 201
    stored2 = res2.json()["reading"]

    # Both exist with distinct physical station IDs and reading IDs
    assert stored1["station_id"] == "Bhadar_Dam_Rajkot"
    assert stored2["station_id"] == "Bhadar_Dam_Aravalli"
    assert stored1["reading_id"] != stored2["reading_id"]

    # Original values preserved
    assert stored1["humidity"] == 73.0
    assert stored1["pressure"] == 1001.35
    assert stored2["temperature"] == 18.85
    assert stored2["wind_speed"] == 2.15

    # Retrieve all readings for 'Bhadar dam' station umbrella
    res_umbrella = client.get("/api/stations/Bhadar dam/readings")
    assert res_umbrella.status_code == 200
    readings = res_umbrella.json()
    assert len(readings) == 2


def test_req13_raw_values_preserved_accurately(client):
    """TEST REQ 13: Verify raw observation values remain strictly unmodified after retrieval."""
    test_data = {
        "reading_id": "R-EXACT-VALS",
        "station_id": "ANKLESHWAR",
        "timestamp": "2024-01-01T01:00:00",
        "temperature": 21.8,
        "pressure": 1010.1,
        "humidity": 84.0,
        "wind_speed": 0.3,
        "rainfall": 307.0,
        "latitude": 21.61055556,
        "longitude": 72.99,
        "elevation": None,
    }

    res = client.post("/api/readings", json=test_data)
    assert res.status_code == 201

    retrieved = client.get("/api/readings/R-EXACT-VALS").json()
    assert retrieved["temperature"] == 21.8
    assert retrieved["pressure"] == 1010.1
    assert retrieved["humidity"] == 84.0
    assert retrieved["wind_speed"] == 0.3
    assert retrieved["rainfall"] == 307.0
    assert retrieved["latitude"] == 21.61055556
    assert retrieved["longitude"] == 72.99


def test_req14_no_fake_values_inserted_for_missing_fields(client):
    """TEST REQ 14: Verify missing fields strictly remain None/NULL and are NOT replaced with 0 or 0.0."""
    raw_payload = {
        "station_id": "ANKLESHWAR",
        "timestamp": "2024-01-01T02:00:00",
        "temperature": 21.4,
        "relative_humidity": 88.0,
        "atmospheric_pressure": 1010.0,
        "rainfall": None,
        "wind_speed": 0.4,
        "latitude": 21.61055556,
        "longitude": 72.99,
        "altitude": None,
    }

    res = client.post("/api/readings", json=raw_payload)
    assert res.status_code == 201
    reading = res.json()["reading"]

    # Verify NULL/None preservation
    assert reading["rainfall"] is None
    assert reading["rainfall"] != 0
    assert reading["rainfall"] != 0.0

    assert reading["elevation"] is None
    assert reading["elevation"] != 0

    assert reading["wind_direction"] is None
    assert reading["wind_direction"] != 0

    assert reading["solar_radiation"] is None
    assert reading["solar_radiation"] != 0

    assert reading["area"] is None


# =====================================================================
# 3. Validation Boundary & Query Tests
# =====================================================================

def test_missing_mandatory_identity_fields_rejected(client):
    """Verify that omitting truly mandatory identity fields (station_id, timestamp) returns 422."""
    no_station = SAMPLE_READING.copy()
    del no_station["station_id"]
    res1 = client.post("/api/readings", json=no_station)
    assert res1.status_code == 422

    no_timestamp = SAMPLE_READING.copy()
    del no_timestamp["timestamp"]
    res2 = client.post("/api/readings", json=no_timestamp)
    assert res2.status_code == 422


def test_invalid_datatype_rejected(client):
    """Verify rejection when field types or coordinates are malformed."""
    invalid_temp = SAMPLE_READING.copy()
    invalid_temp["temperature"] = "hot"
    res1 = client.post("/api/readings", json=invalid_temp)
    assert res1.status_code == 422

    invalid_lat = SAMPLE_READING.copy()
    invalid_lat["reading_id"] = "R-INVALID-LAT"
    invalid_lat["latitude"] = 150.0  # Out of range [-90, 90]
    res2 = client.post("/api/readings", json=invalid_lat)
    assert res2.status_code == 422


def test_reading_retrieval_by_id_and_404(client):
    """Verify single reading retrieval by reading_id and 404 behavior."""
    client.post("/api/readings", json=SAMPLE_READING)

    res_found = client.get("/api/readings/R123")
    assert res_found.status_code == 200
    assert res_found.json()["reading_id"] == "R123"

    res_404 = client.get("/api/readings/NON-EXISTENT")
    assert res_404.status_code == 404
    assert res_404.json()["detail"]["error"] == "reading_not_found"
