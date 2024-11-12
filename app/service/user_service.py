import random
import string
import datetime
from datetime import timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from jose import jwt, JWTError
import requests
from typing import Annotated
from sqlalchemy.orm import Session
from app.model.user import Wallet
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/api/user/verify-user')


def generate_otp():
    return ''.join(random.choices(string.digits, k=4))


def send_otp(otp: str, mobile_number: str) -> bool:

    url = f'https://2factor.in/API/V1/74380642-1da4-11ef-8b60-0200cd936042/SMS/{
        mobile_number}/{otp}'
    print(url)
    payload = {}
    headers = {}

    response = requests.request(
        "GET", url,
        headers=headers, data=payload)
    if response.status_code == 200:
        return True
    return False


def create_accesss_token(name: str, user_id: int, expiry: timedelta):
    encode = {
        'sub':  name,
        'id': user_id
    }
    expires = datetime.datetime.utcnow() + expiry
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        name: str = payload.get('sub')
        user_id: int = payload.get('id')
        if name is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid access token")
        return {
            'name': name,
            'user_id': user_id
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")


def generate_wallet_number(db: Session) -> str:
    while True:
        # Generate a random wallet number (e.g., 12 characters long, alphanumeric)
        wallet_number = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=12))

        # Check if the generated wallet number is unique
        existing_wallet = db.query(Wallet).filter(
            Wallet.wallet_number == wallet_number).first()
        if not existing_wallet:
            return wallet_number

        # If it's not unique, generate a new one
        continue
