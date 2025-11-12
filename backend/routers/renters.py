from datetime import timedelta, timezone, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException , Response ,Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from starlette import status

from database import sessionLocal
from models import Renter, Booking, Property

from passlib.context import CryptContext
router = APIRouter(
    prefix="/renter",
    tags=["Renter"],
)
SECRET_KEY ='6f408c3e0d7ee3080195315503428775490515771538572097e23c5588e1f702'
ALGORITHM = 'HS256'
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='renter/login')

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency=Annotated[Session, Depends(get_db)]

# functions
def authenticate_renter(email:str, password:str,db):
    renter = db.query(Renter).filter(Renter.email == email).first()
    if not renter:
        return False
    if not bcrypt_context.verify(password, renter.hashed_password):
        return False
    return renter

def create_access_token(email:str,renter_id:str,expires_delta:timedelta):
    expires = datetime.now(timezone.utc) + expires_delta
    encode ={'sub':email,'id':renter_id,'exp': expires.timestamp()}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_renter(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return HTTPException(status_code=401, detail="Not Authorized")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        renter_id: int = payload.get("id")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email, "id": renter_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class CreateRenterRequest(BaseModel):
    fullname :str
    email : str
    hashed_password :str
    photo_url:str
    phone_number : str

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def create_renter(db:db_dependency,create_renter_request: CreateRenterRequest):

    renter = db.query(Renter).filter(Renter.email == create_renter_request.email).first()
    if renter:
        raise HTTPException(status_code=400, detail="Email already registered")
    create_renter_model = Renter(
        fullname=create_renter_request.fullname,
        email=create_renter_request.email,
        hashed_password=bcrypt_context.hash(create_renter_request.hashed_password),
        photo_url=create_renter_request.photo_url,
        phone_number=create_renter_request.phone_number
    )
    db.add(create_renter_model)
    db.commit()
    return {"message": "Renter registered successfully"}
@router.get("/all")
async def get_all_renters(db:db_dependency):
    return db.query(Renter).all()

@router.post("/login")
async def login_renter(response:Response,form_data:Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency):
    renter = authenticate_renter(form_data.username, form_data.password, db)
    if not renter:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(renter.email, renter.id,timedelta(minutes=20))
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1200
    )
    return {"message": "Renter Login successful"}


@router.get("/me")
async def get_renter_me(current_landlord: dict = Depends(get_current_renter)):
    return {"message": f"Welcome {current_landlord['email']}"}

@router.post("/logout")
async def logout_landlord(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/dashboard")
async def renter_dashboard(db: db_dependency, current_renter: dict = Depends(get_current_renter)):
    renter_id = current_renter["id"]

    renter_data = (
        db.query(Renter)
        .options(
            joinedload(Renter.bookings)
            .joinedload(Booking.property)
            .joinedload(Property.landlord)
        )
        .filter(Renter.id == renter_id)
        .first()
    )

    if not renter_data:
        raise HTTPException(status_code=404, detail="Renter not found")

    # Serialize data
    renter_info = {
        "id": renter_data.id,
        "fullname": renter_data.fullname,
        "email": renter_data.email,
        "phone_number": renter_data.phone_number,
        "photo_url": renter_data.photo_url,
        "created_at": renter_data.created_at,
        "bookings": []
    }

    for booking in renter_data.bookings:
        renter_info["bookings"].append({
            "booking_id": booking.id,
            "status": booking.status,
            "start_date": booking.start_date,
            "end_date": booking.end_date,
            "total_amount": booking.total_amount,
            "property": {
                "title": booking.property.title,
                "address": booking.property.address,
                "rent": booking.property.rent,
                "property_type": booking.property.property_type,
                "landlord": {
                    "fullname": booking.property.landlord.fullname,
                    "email": booking.property.landlord.email,
                    "phone_number": booking.property.landlord.phone_number,
                }
            }
        })

    return renter_info