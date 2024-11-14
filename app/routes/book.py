from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from app.schemas.book import BookingRead
from app.schemas import book as bookSchema
from app.database import SessionLocale
from app.model.book import Booking, BookingSlot
from app.model.user import User, Wallet
from app.model.cng import Station


from datetime import timedelta
from app.service.user_service import create_accesss_token, decode_access_token, hash_pass, verify_user

router = APIRouter(
    prefix="/v1/order",
    tags=["V1 ORDER API"],
)


def get_db():
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()


db_depandancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[dict, Depends(decode_access_token)]


@router.post("/create/", status_code=status.HTTP_200_OK)
async def create_order(user: user_dependancy, bookingcreate: bookSchema.BookingCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        User.id == user['user_id']).first()
    user_wallet = db.query(Wallet).filter(
        Wallet.user_id == user['user_id']).first()
    if db_user:
        if user_wallet.balance > bookingcreate.amount:
            new_order = Booking(
                user_id=db_user.id,
                station_id=bookingcreate.station_id,
                booking_slot=bookingcreate.booking_slot,
                amount=bookingcreate.amount,
                status=bookingcreate.status,
            )
            db.add(new_order)
            db.commit()
            db.refresh(new_order)

            new_balance = user_wallet.balance - bookingcreate.amount
            user_wallet.balance = new_balance
            db.add(user_wallet)
            db.commit()
            db.refresh(user_wallet)
        else:
            return {"message": "Insufficient wallet balance"}

        return {
            "message": "Order created successfully",
            "order_id": new_order.id,
        }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.get("/station-orders/", response_model=list[dict], status_code=status.HTTP_200_OK)
async def station_order(user: user_dependancy, db: Session = Depends(get_db)):
    # Query the bookings, joining with User, Station, and BookingSlot to get the additional info
    orders = db.query(
        Booking.order_id,
        User.name.label('user_name'),  # Alias the user name
        Station.name.label('station_name'),  # Alias the station name
        BookingSlot.start_time_new,
        BookingSlot.end_time_new,
        Booking.amount,
        Booking.status
    ).join(
        User, User.id == Booking.user_id  # Join with User to get the username
    ).join(
        # Join with Station to get the station name
        Station, Station.id == Booking.station_id
    ).join(
        # Join with BookingSlot for the start_time_new
        BookingSlot, BookingSlot.id == Booking.booking_slot
    ).filter(
        # Filter by the station_id of the current user
        Booking.station_id == user['user_id']
    ).all()

    if orders:
        # Format the data to include the user_name, station_name, and other fields
        result = []
        for order in orders:
            result.append({
                "order_id": order.order_id,
                "user_name": order.user_name,  # Access the aliased user_name
                "station_name": order.station_name,  # Access the aliased station_name
                # Access the start_time_new field from BookingSlot
                "slot_start_time": order.start_time_new,
                "slot_end_time": order.end_time_new,
                "amount": order.amount,
                "status": order.status
            })
        return result

    # If no orders found, raise an HTTP 404 exception
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Booking Not Found"
    )


@router.get("/user-orders/", status_code=status.HTTP_200_OK)
async def user_order(user: user_dependancy, db: Session = Depends(get_db)):
    user_order = db.query(Booking).filter(
        Booking.user_id == user['user_id']).all()
    if user_order:
        return user_order

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Booking Not found"
    )
