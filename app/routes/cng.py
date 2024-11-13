from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from app.schemas.cng import cngLogin
from app.database import SessionLocale
from app.model.cng import Station, Worker
from datetime import timedelta
from app.service.user_service import create_accesss_token, decode_access_token

router = APIRouter(
    prefix="/v1/station",
    tags=["V1 CNG STATION API"],
)


def get_db():
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()


db_depandancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[dict, Depends(decode_access_token)]


@router.post("/station-login", status_code=status.HTTP_200_OK)
async def station_login(loginrequest: cngLogin, db: Session = Depends(get_db)):
    station = db.query(Station).filter(Station.phone_number ==
                                       loginrequest.phone_number).first()

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )

    if station.passcode != loginrequest.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    access = create_accesss_token(
        station.name, station.id, timedelta(days=90))

    return {
        "message": "Login successfully",
        "access_token": access,
    }


@router.post("/worker-login", status_code=status.HTTP_200_OK)
async def worker_login(loginrequest: cngLogin, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.phone_number ==
                                     loginrequest.phone_number).first()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )

    if worker.passcode != loginrequest.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    access = create_accesss_token(
        worker.name, worker.id, timedelta(days=90))

    return {
        "message": "Login successfully",
        "access_token": access,
    }


@router.post("/worker-register", status_code=status.HTTP_201_CREATED)
async def worker_register(user: user_dependancy, loginrequest: cngLogin, db: Session = Depends(get_db)):
    station = db.query(Station).filter(Station.id == user['id']).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )
    worker = db.query(Worker).filter(Worker.phone_number ==
                                     loginrequest.phone_number).first()
    if not worker:
        try:
            new_worker = Worker(
                name=loginrequest.name,
                phone_number=loginrequest.phone_number,
                passcode=loginrequest.passcode,
                station_id=user['user_id']
            )
            db.add(new_worker)
            db.commit()
            db.refresh(new_worker)
            return {
                "message": "Worker Created successfully",
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{e}"
            )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Worker Already Exist"
    )
