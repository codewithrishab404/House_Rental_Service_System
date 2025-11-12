from sqlalchemy import Integer, Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class Renter(Base):
    __tablename__ = "renter"
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    photo_url = Column(String)
    phone_number = Column(String)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    bookings = relationship("Booking", back_populates="renter", cascade="all, delete") #relationship

class Landlord(Base):
    __tablename__ = "landlord"
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone_number = Column(String)
    properties = relationship("Property", back_populates="landlord", cascade="all, delete")

class Property(Base):
    __tablename__ = "property"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    address = Column(String)
    rent = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    property_type = Column(String)  # "apartment", "house", etc.
    landlord_id = Column(Integer, ForeignKey("landlord.id"))

    # Relationship
    landlord = relationship("Landlord", back_populates="properties")
    bookings = relationship("Booking", back_populates="property", cascade="all, delete")


class Booking(Base):
    __tablename__ = "booking"
    id = Column(Integer, primary_key=True, index=True)
    renter_id = Column(Integer, ForeignKey("renter.id"))
    property_id = Column(Integer, ForeignKey("property.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    total_amount = Column(Float)
    status = Column(String, default="Pending")  # e.g., "Pending", "Confirmed", "Cancelled"

    # Relationships
    renter = relationship("Renter", back_populates="bookings")
    property = relationship("Property", back_populates="bookings")
