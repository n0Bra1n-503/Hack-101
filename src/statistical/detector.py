from pathlib import Path
from typing import Optional, Union, Dict, Any
import pandas as pd
from src.data.schema import SensorSchema
from .baselines import BaselineReference, fit_statistical_baselines
from .config import StatisticalConfig
from .scoring import calculate_statistical_scores
from .evidence import extract_statistical_evidence


class StatisticalBaselineDetector:
    """Statistical Anomaly Baseline Detector for Automatic Weather Station (AWS) data."""

    def __init__(
        self,
        config: Optional[Union[StatisticalConfig, str, Path]] = None,
        schema: Optional[SensorSchema] = None,
    ):
        if config is None:
            self.config = StatisticalConfig()
        elif isinstance(config, (str, Path)):
            self.config = StatisticalConfig.from_yaml(config)
        else:
            self.config = config

        self.schema = schema or SensorSchema()
        self.baselines: Optional[BaselineReference] = None

    def fit(self, df: pd.DataFrame) -> "StatisticalBaselineDetector":
        """Fit baseline distributions (global, station, diurnal) from reference data."""
        self.baselines = fit_statistical_baselines(df, schema=self.schema)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score observations and extract statistical evidence."""
        if self.baselines is None:
            # If not explicitly fitted, fit on the incoming dataframe
            self.fit(df)

        df_scores = calculate_statistical_scores(
            df=df,
            baselines=self.baselines,
            config=self.config,
            schema=self.schema,
        )

        df_evidence = extract_statistical_evidence(
            df_raw=df,
            df_scores=df_scores,
            config=self.config,
            schema=self.schema,
        )

        # Merge original data + statistical scores + evidence
        # Ensure no overlapping columns get duplicated
        new_cols_scores = [c for c in df_scores.columns if c not in df.columns]
        new_cols_ev = [c for c in df_evidence.columns if c not in df.columns and c not in new_cols_scores]

        result = pd.concat([df, df_scores[new_cols_scores], df_evidence[new_cols_ev]], axis=1)
        return result

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit baselines and score observations in one pass."""
        return self.fit(df).transform(df)


def detect_statistical_anomalies(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    config: Optional[Union[StatisticalConfig, str, Path]] = None,
) -> pd.DataFrame:
    """Convenience function to run statistical anomaly detection on a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame (raw or with engineered features).
    schema : Optional[SensorSchema]
        Column schema definition.
    config : Optional[Union[StatisticalConfig, str, Path]]
        Configuration instance or path to YAML config.

    Returns
    -------
    pd.DataFrame
        Enriched DataFrame with statistical scores, anomaly flags, evidence, and reasons.
    """
    detector = StatisticalBaselineDetector(config=config, schema=schema)
    return detector.fit_transform(df)
