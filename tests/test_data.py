from pathlib import Path
import pandas as pd
import pytest

from src.data.loader import load_sensor_data, load_merged_sensor_data
from src.data.schema import SensorSchema, validate_sensor_columns


def test_missing_file_handling():
    """Verify FileNotFoundError is raised when target CSV does not exist."""
    non_existent = Path("data/raw/does_not_exist_xyz.csv")
    with pytest.raises(FileNotFoundError) as exc_info:
        load_sensor_data(non_existent)
    assert "not found" in str(exc_info.value).lower()


def test_load_sensor_data_csv(tmp_path):
    """Verify CSV loader reads file without modifying it and returns DataFrame."""
    dummy_csv = tmp_path / "test_data.csv"
    dummy_csv.write_text("temperature,pressure,humidity\n25.0,1013.25,60.0\n")

    df = load_sensor_data(dummy_csv)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 3)
    assert list(df.columns) == ["temperature", "pressure", "humidity"]
    assert dummy_csv.read_text() == "temperature,pressure,humidity\n25.0,1013.25,60.0\n"


def test_load_merged_sensor_data_3_files(tmp_path):
    """Verify 3-file merge on station_id and timestamp."""
    t_file = tmp_path / "temperature.csv"
    p_file = tmp_path / "pressure.csv"
    h_file = tmp_path / "humidity.csv"

    t_file.write_text("station_id,timestamp,temperature\nSTN1,2024-05-11 00:00:00,25.0\n")
    p_file.write_text("station_id,timestamp,pressure\nSTN1,2024-05-11 00:00:00,950.0\n")
    h_file.write_text("station_id,timestamp,humidity\nSTN1,2024-05-11 00:00:00,65.0\n")

    df = load_merged_sensor_data(temperature_path=t_file, pressure_path=p_file, humidity_path=h_file)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 5)
    assert set(["station_id", "timestamp", "temperature", "pressure", "humidity"]).issubset(df.columns)


def test_validate_sensor_columns_all_present():
    """Verify validation passes when required columns are present."""
    df = pd.DataFrame(columns=["temperature", "pressure", "humidity"])
    is_valid, missing = validate_sensor_columns(df)
    assert is_valid is True
    assert missing == []


def test_validate_sensor_columns_missing_fields():
    """Verify validation correctly identifies missing required columns."""
    df = pd.DataFrame(columns=["temperature"])
    is_valid, missing = validate_sensor_columns(df)
    assert is_valid is False
    assert missing == ["pressure", "humidity"]


def test_validate_sensor_columns_custom_schema():
    """Verify validation with custom column mapping schema."""
    custom_schema = SensorSchema(
        temperature="temp_c",
        pressure="press_hpa",
        humidity="rel_hum",
    )
    df = pd.DataFrame(columns=["temp_c", "press_hpa", "rel_hum", "other_col"])
    is_valid, missing = validate_sensor_columns(df, schema=custom_schema)
    assert is_valid is True
    assert missing == []

    df_incomplete = pd.DataFrame(columns=["temp_c", "other_col"])
    is_valid, missing = validate_sensor_columns(df_incomplete, schema=custom_schema)
    assert is_valid is False
    assert set(missing) == {"press_hpa", "rel_hum"}
