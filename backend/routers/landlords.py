from datetime import timezone, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from database import sessionLocal
from models import Landlord

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

@router.post("/login",response_model=Token)
async def login_landlord(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],db:db_dependency):
    landlord = authenticate_landlord(form_data.username, form_data.password, db)
    if not landlord:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(landlord.email, landlord.id, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}