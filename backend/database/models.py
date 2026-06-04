from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float)
    risk_score = Column(Integer)
    action = Column(String)  # "ALLOW" or "BLOCK TRANSACTION"


class GeoProfile(Base):
    __tablename__ = 'geo_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    seen_count = Column(Integer, default=1, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GeoEvent(Base):
    __tablename__ = 'geo_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    event_time = Column(DateTime, default=datetime.utcnow, nullable=False)
