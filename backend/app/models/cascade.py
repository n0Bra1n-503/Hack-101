"""SQLAlchemy model for cascade simulation records."""

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text
from backend.app.database.connection import Base


class CascadeEvent(Base):
    """Historical or simulation cascade walkthrough."""

    __tablename__ = "cascade_events"

    cascade_id = Column(String, primary_key=True, index=True, nullable=False)
    scenario = Column(String, nullable=False)  # SCENARIO_A, SCENARIO_B, SCENARIO_C
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="completed")
    pipeline_state = Column(Text, nullable=False)  # JSON representation of all 10 stages

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<CascadeEvent(id='{self.cascade_id}', scenario='{self.scenario}')>"
