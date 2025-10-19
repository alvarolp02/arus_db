from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

DATABASE_URL = "postgresql://admin:admin@localhost/arusdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class DriverEnum(enum.Enum):
    DV = "DV"
    Salva = "Salva"
    PedroAndreu = "PedroAndreu"
    Correa = "Correa"
    Lucas = "Lucas"
    Cabello = "Cabello"
    Tornay = "Tornay"

class CarEnum(enum.Enum):
    ART24D = "ART24D"
    ART25D = "ART25D"
    ART26D = "ART26D"

class MissionEnum(enum.Enum):
    Acceleration = "Acceleration"
    Skidpad = "Skidpad"
    Autocross = "Autocross"
    Endurance = "Endurance"
    DV_Acceleration = "DV_Acceleration"
    DV_Skidpad = "DV_Skidpad"
    DV_Autocross = "DV_Autocross"
    DV_Trackdrive = "DV_Trackdrive"
    Other = "Other"

class LogTypeEnum(enum.Enum):
    CAN = "CAN"
    ROSbag = "ROSbag"


class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    logs = relationship("Log", back_populates="test", cascade="all, delete-orphan")


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    vehicle = Column(Enum(CarEnum, name="car_enum"), nullable=True)
    mission = Column(Enum(MissionEnum, name="mission_enum"), nullable=True)
    log_type = Column(Enum(LogTypeEnum, name="log_type_enum"), nullable=True)
    driver = Column(Enum(DriverEnum, name="driver_enum"), nullable=True)
    filepath = Column(Text)
    plots_path = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    duration_sec = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    test_id = Column(Integer, ForeignKey("tests.id"))

    test = relationship("Test", back_populates="logs")

def init_db():
    Base.metadata.create_all(bind=engine)
