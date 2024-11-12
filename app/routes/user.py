from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from app.schemas.user import OTPVerify, LoginRequest, UserResponse, CreateVehicle, VehicleResponse
from app.database import SessionLocale
from app.model.user import User, Vehicle, Wallet


from datetime import timedelta
from app.service.user_service import generate_otp, send_otp, create_accesss_token, decode_access_token, generate_wallet_number

router = APIRouter(
    prefix="/v1/user",
    tags=["v1 user API"],
)


def get_db():
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()


db_depandancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[dict, Depends(decode_access_token)]


async def register_user(
    icon: UploadFile = File(None),
    name: str = Form(...),
    phone_number: str = Form(...),
    db: Session = Depends(get_db)
):
    # Read the icon file if provided
    icon_data = await icon.read() if icon else None

    # Generate OTP
    otp = generate_otp()

    # Send OTP to the phone number
    try:
        send_otp(otp=otp, mobile_number=phone_number)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send OTP: {str(e)}"
        )

    # Create the user object
    user = User(
        name=name,
        phone_number=phone_number,
        icon=icon_data,
        otp=otp  # Store OTP for future verification
    )

    # Add user to the database and commit to get the user ID
    try:
        db.add(user)
        db.commit()
        db.refresh(user)  # Refresh to get the user ID
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

    # Now that the user is created and we have the user ID, create the wallet
    wallet_number = generate_wallet_number(db)
    wallet = Wallet(
        user_id=user.id,  # Assign the user ID to the wallet
        balance=0,
        wallet_number=wallet_number
    )

    # Add wallet to the database
    try:
        db.add(wallet)
        db.commit()
        db.refresh(wallet)  # Refresh to get the wallet data
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wallet: {str(e)}"
        )

    return {"message": "OTP sent successfully. Please verify your phone number."}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(loginrequest: LoginRequest, db: Session = Depends(get_db)):
    # Retrieve user based on phone number
    user = db.query(User).filter(User.phone_number ==
                                 loginrequest.phone_number).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if the user's account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please verify your phone number first."
        )

    # Generate a new OTP
    otp = generate_otp()
    user.otp = otp  # Update the OTP in the database

    # Send the OTP to the user's phone number
    try:
        send_otp(otp=otp, mobile_number=loginrequest.phone_number)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send OTP: {str(e)}"
        )

    # Commit the OTP change to the database
    db.commit()
    db.refresh(user)

    return {"message": "OTP sent successfully. Please verify to proceed."}


@router.post("/verify", status_code=status.HTTP_201_CREATED)
async def verify_login(verifyrequest: OTPVerify, db: Session = Depends(get_db)):
    # Retrieve user based on phone number
    user = db.query(User).filter(User.phone_number ==
                                 verifyrequest.phone_number).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if the OTP matches
    print(user.otp)
    if user.otp != verifyrequest.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    # OTP verification successful - activate user and reset OTP
    user.is_active = True
    user.otp = None  # Clear OTP after successful verification
    db.commit()
    db.refresh(user)
    access = create_accesss_token(
        user.name, user.id, timedelta(days=90))

    return {
        "message": "Phone number verified successfully",
        "access_token": access,
    }


@router.get("/profile/", response_model=UserResponse)
async def read_users(user: user_dependancy, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user.id).first()
    if db_user:
        return db_user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.post("/vehicle", response_model=VehicleResponse)
async def create_vehicle(
    user: user_dependancy,
    vehicle: CreateVehicle,
    db: Session = Depends(get_db)
):
    # Check if the user exists in the database
    db_user = db.query(User).filter(User.id == user['id']).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create a new vehicle associated with the user
    try:
        new_vehicle = Vehicle(
            user_id=user['id'],  # Set the user ID from the authenticated user
            vehicle_number=vehicle.vehicle_number,
            vehicle_make=vehicle.vehicle_make,
            vehicle_model=vehicle.vehicle_model,
        )
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        return {
            "message": "Vehicle created successfully",
            "vehicle_id": new_vehicle.id,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create vehicle: {str(e)}"
        )


@router.get("/users/", response_model=list[UserResponse])
async def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")
