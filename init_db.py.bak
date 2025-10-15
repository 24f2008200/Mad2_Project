from backend.models import db, User, ParkingLot, ParkingSpot, Reservation
from datetime import datetime, timedelta, UTC
from werkzeug.security import generate_password_hash
from backend.app import create_app, db
from backend.models import User

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # --- Add Admin ---
    admin = User(
        name="Admin",
        email="admin@example.com",
        password=generate_password_hash("admin123"),
        role="admin",
        is_admin=True,
        mobile="9999999999",
        address="Admin Address"
    )
    db.session.add(admin)

    # --- Add Some Users ---
    user1 = User(
        name="Ram",
        email="ram@example.com",
        password=generate_password_hash("ram123"),
        is_admin=False,
        mobile="8888888888",
        role="user",
        address="Ram's Address"
    )
    user2 = User(
        name="Murugan",
        email="murugan@example.com",
        password=generate_password_hash("murugan123"),
        is_admin=False,
        mobile="7777777777",
        role="user", address="Murugan's Address"
    )
    user3 = User(
        name="Chandran",
        email="chandran@example.com",
        password=generate_password_hash("chandran123"),
        is_admin=False,
        mobile="6666666666",
        role="user", address="Chandran's Address"
    )
    user4 = User(
        name="Devika",
        email="devika@example.com",
        password=generate_password_hash("devika123"),
        is_admin=False,
        mobile="5555555555",
        role="user", address="Devika's Address"
    )
    user5 = User(
        name="Lakshmi",
        email="lakshmi@example.com",
        password=generate_password_hash("lakshmi123"),
        is_admin=False,
        mobile="4444444444",
        role="user", address="Lakshmi's Address"
    )
    db.session.add_all([user1, user2, user3, user4, user5])
    db.session.commit()

    # --- Add Parking Lots with Spots ---
    lot1 = ParkingLot(
        name="Railway Station",
        prefix="RS",
        address="123 Main Street",
        pin_code="600001",
        price=50,
        max_slots=10
    )
    lot2 = ParkingLot(
        name="Mall Parking Lot",
        prefix="MPL",
        address="456 Side Street",
        pin_code="600002",
        price=40,
        max_slots=30
    )   
    lot3 = ParkingLot(
        name="City Center",
        prefix="CC",
        address="789 Market Road",
        pin_code="600003",
        price=30,
        max_slots=20
    )   
    db.session.add_all([lot1, lot2, lot3])
    db.session.flush()  # ensures lot1.id is available

    lot4 = ParkingLot(
        name="Community Hall",
        prefix="CH",    
        address="456 Side Street",
        pin_code="600002",
        price=40,
        max_slots=15
    )
    db.session.add(lot4)
    db.session.flush()
    db.session.commit()

    # lots = [lot1, lot2, lot3, lot4]

    # for lot in lots:
    #     for i in range(1, lot.max_slots + 1):
    #         spot = ParkingSpot(
    #             lot_id=lot.id,
    #             label=f"{lot.name[-1]}-{i}",
    #         status="A")
    #         db.session.add(spot)
        
    #     db.session.commit()
# Create reservations
    res1 = Reservation(
        user_id=user1.id,
        spot_id=lot1.spots[0].id,
        vehicle_number="TN01AB1234",
        start_time=datetime.now(UTC) - timedelta(hours=1),
        end_time=None,  
        driver_contact="9876543210",
        driver_name="Ram",
    )
    lot1.spots[0].status = "O"
    res2 = Reservation(
        user_id=user2.id,
        spot_id=lot1.spots[1].id,
        vehicle_number="TN01XY9999",
        start_time=datetime.now(UTC) - timedelta(hours=3),
        end_time=datetime.now(UTC) - timedelta(hours=1), 
        driver_contact="8765432109",
        driver_name="Murugan"
    )
    res3= Reservation(
        user_id=user3.id,
        spot_id=lot2.spots[0].id,
        vehicle_number="TN01ZZ8888",
        start_time=datetime.now(UTC) - timedelta(hours=2),
        end_time= None ,
        driver_contact="9876543210",
        driver_name="Ram"
    )
    lot2.spots[0].status = "O"
    res4 = Reservation(
        user_id=user4.id,
        spot_id=lot3.spots[0].id,
        vehicle_number="TN01CC7777",
        start_time=datetime.now(UTC) - timedelta(hours=4),
        end_time=datetime.now(UTC) - timedelta(hours=2) , 
        driver_contact="765242325",
        driver_name="Kumar"
    )
    res5 = Reservation(
        user_id=user5.id,
        spot_id=lot4.spots[0].id,
        vehicle_number="TN01DD6666",
        start_time=datetime.now(UTC) - timedelta(hours=1, minutes=30),
        end_time=None , 
        driver_contact="765242325",
        driver_name="Kumar"
    )
    lot4.spots[0].status = "O"
    res6 = Reservation(
        user_id=user1.id,
        spot_id=lot4.spots[1].id,
        vehicle_number="TN01EE5555",
        start_time=datetime.now(UTC) - timedelta(hours=5),
        end_time=None,
        driver_contact="1254698725",
        driver_name="Ramu"
    )
    # Mark spot 0 occupied   
    lot4.spots[1].status = "O"

    db.session.add_all([res1, res2, res3, res4, res5, res6])
    db.session.commit()
    print("Database initialized with dummy data!")
