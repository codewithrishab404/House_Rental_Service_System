from sqlalchemy import Integer, Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from database import Base

class Renter(Base):
    __tablename__ = "renter"
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    photo_url = Column(String)
    phone_number = Column(String)


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
    # Relationship back to landlord
    landlord = relationship("Landlord", back_populates="properties")



