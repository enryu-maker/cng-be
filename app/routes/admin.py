from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from app.schemas.admin import AdminLogin, AdminRegister
from app.schemas import user as userSchema
from app.database import SessionLocale
from app.model.admin import Admin
from app.model import user

from datetime import timedelta
from app.service.user_service import create_accesss_token, decode_access_token, hash_pass, verify_user

router = APIRouter(
    prefix="/v1/admin",
    tags=["V1 ADMIN API"],
)


def get_db():
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()


db_depandancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[dict, Depends(decode_access_token)]


@router.post("/admin-register", status_code=status.HTTP_201_CREATED)
async def admin_register(loginrequest: AdminRegister, db: Session = Depends(get_db)):

    admin = db.query(Admin).filter(Admin.email ==
                                   loginrequest.email).first()
    if not admin:
        try:
            new_admin = Admin(
                name=loginrequest.name,
                email=loginrequest.email,
                password=hash_pass(loginrequest.password),
                is_active=True
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            return {
                "message": "Admin Created successfully",
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{e}"
            )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Admin Already Exist"
    )


@router.post("/admin-login", status_code=status.HTTP_200_OK)
async def worker_login(loginrequest: AdminLogin, db: Session = Depends(get_db)):
    admin = verify_user(loginrequest=loginrequest, db=db, Model=Admin)

    if admin:
        access = create_accesss_token(
            admin.name, admin.id, timedelta(days=90))

        return {
            "message": "Login successfully",
            "access_token": access,
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Error in Admin Login"
    )

# Add Station


@router.post("/station-register", status_code=status.HTTP_201_CREATED)
async def station_register(
    user: user_dependancy,
    name: str = Form(...),
    image: UploadFile = File(None),
    phone_number: str = Form(...),
    passcode: str = Form(...),
    description: str = Form(None),
    latitude: str = Form(...),
    longitude: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    country: str = Form(...),
    postal_code: str = Form(...),
    fuel_available: bool = Form(True),
    price: str = Form(...),
    db: Session = Depends(get_db)
):
    pass

# User API


@router.get("/get-users/", response_model=list[userSchema.UserResponse])
async def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(user.User).offset(skip).limit(limit).all()


@router.delete("/delete-users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(user.User).filter(user.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")
