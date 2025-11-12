from datetime import timezone, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException ,Response ,Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from starlette import status

from database import sessionLocal
from models import Landlord, Property, Booking

router = APIRouter(
    prefix="/landlord",
    tags=["Landlord"],
)
SECRET_KEY ='6f408c3e0d7ee3080195315503428775490515771538572097e23c5588e1f702'
ALGORITHM = 'HS256'
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='landlord/login')
def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session, Depends(get_db)]

class CreateLandlordRequest(BaseModel):
    fullname: str
    email: str
    password: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

#functions
def authenticate_landlord(email:str, password:str,db):
    landlord = db.query(Landlord).filter(Landlord.email == email).first()
    if not landlord:
        return False
    if not bcrypt_context.verify(password, landlord.hashed_password):
        return False
    return landlord

def create_access_token(email:str,landlord_id:str,expires_delta:timedelta):
    expires = datetime.now(timezone.utc) + expires_delta
    encode ={'sub':email,'id':landlord_id, 'exp': expires.timestamp()}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_landlord(request:Request):
    token = request.cookies.get("access_token")
    if not token:
        return HTTPException(status_code=401 , detail="Not Authorized")
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email:str = payload.get("sub")
        landlord_id :str = payload.get("id")
        if not email:
            raise HTTPException(status_code=401 , detail="Invalid Token")
        return {"email":email,"landlord_id":landlord_id}
    except JWTError:
        raise HTTPException(status_code=401 , detail="Invalid Token")

@router.get("/all",status_code=status.HTTP_200_OK)
async def get_all_landlord(db:db_dependency):
    return db.query(Landlord).all()

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def create_landlord(db:db_dependency, create_landlord_request:CreateLandlordRequest):
    landlord = db.query(Landlord).filter(Landlord.email == create_landlord_request.email).first()
    if landlord:
        raise HTTPException(status_code=400, detail="Email already registered")
    create_landlord_model = Landlord(
        fullname=create_landlord_request.fullname,
        email=create_landlord_request.email,
        hashed_password=bcrypt_context.hash(create_landlord_request.password),
        phone_number=create_landlord_request.phone_number,
    )
    db.add(create_landlord_model)
    db.commit()
    return {"message": "Landlord registered successfully"}

@router.post("/login")
async def login_landlord(response:Response,form_data: Annotated[OAuth2PasswordRequestForm,Depends()],db:db_dependency):
    landlord = authenticate_landlord(form_data.username, form_data.password, db)
    if not landlord:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(landlord.email, landlord.id, timedelta(minutes=20))
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=1200
    )
    return {"message":"Landlord Login Successful"}

@router.post("/logout")
def logout_landlord(response:Response):
    response.delete_cookie("access_token")
    return {"message":"Landlord Logout Successful"}


@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def landlord_dashboard(
    db: db_dependency,
    current_landlord: dict = Depends(get_current_landlord)
):
    landlord_id = current_landlord["id"]


    landlord_data = (
        db.query(Landlord)
        .options(
            joinedload(Landlord.properties)
            .joinedload(Property.bookings)
            .joinedload(Booking.renter)
        )
        .filter(Landlord.id == landlord_id)
        .first()
    )

    if not landlord_data:
        raise HTTPException(status_code=404, detail="Landlord not found")

    #response dictionary
    landlord_info = {
        "id": landlord_data.id,
        "fullname": landlord_data.fullname,
        "email": landlord_data.email,
        "phone_number": landlord_data.phone_number,
        "total_properties": len(landlord_data.properties),
        "total_bookings": sum(len(p.bookings) for p in landlord_data.properties),
        "properties": []
    }

    for property in landlord_data.properties:
        property_info = {
            "id": property.id,
            "title": property.title,
            "address": property.address,
            "description": property.description,
            "rent": property.rent,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "property_type": property.property_type,
            "total_bookings": len(property.bookings),
            "bookings": []
        }

        for booking in property.bookings:
            property_info["bookings"].append({
                "booking_id": booking.id,
                "status": booking.status,
                "start_date": booking.start_date,
                "end_date": booking.end_date,
                "total_amount": booking.total_amount,
                "renter": {
                    "id": booking.renter.id,
                    "fullname": booking.renter.fullname,
                    "email": booking.renter.email,
                    "phone_number": booking.renter.phone_number,
                    "photo_url": booking.renter.photo_url
                }
            })

        landlord_info["properties"].append(property_info)

    return landlord_info
