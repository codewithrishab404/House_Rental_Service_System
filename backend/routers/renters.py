from datetime import timedelta, timezone, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from database import sessionLocal
from models import Renter

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

class Token(BaseModel):
    access_token: str
    token_type: str

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

@router.post("/login",response_model=Token)
async def login_renter(form_data:Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency):
    renter = authenticate_renter(form_data.username, form_data.password, db)
    if not renter:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(renter.email, renter.id,timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}