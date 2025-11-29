# seed.py
import os
import random
import string
import datetime
from datetime import datetime as dt, timedelta, time, date

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Import your app and models
from backend.app import create_app, db
from backend.models import User, ParkingLot, ParkingSpot, Reservation

# Your seed lists (lots, names, drivers, streets, state_codes, locations, cities, etc.)
# This file is expected to exist and provide required lists exactly as your prior setup.
from seed_data import lots as seed_lots, names, drivers, streets, state_codes, locations, cities

load_dotenv()

# Environment-driven size logic (same as your previous code)
size = int(os.getenv("DATA_SIZE", 0))

no_users = 5 if size == 0 else 25 if size == 1 else 50
no_lots = 5 if size == 0 else 10 if size == 1 else 20
no_drivers = 5 if size == 0 else 50 if size == 1 else 100
no_cars = 5 if size == 0 else 50 if size == 1 else 100
no_of_back_days = 30 if size == 0 else 60 if size == 1 else 90
no_of_back_days *= 2   # preserve your original doubling behavior

# Optional default webhook
default_google_chat_webhook = os.getenv(
    "DEFAULT_GOOGLE_CHAT_WEBHOOK",
    "https://example.invalid/webhook"  # placeholder if not provided
)

app = create_app()

with app.app_context():

    # Reset DB
    db.drop_all()
    db.create_all()

    # --------------- Create Admin and demo users ------------------
    admin = User(
        name="Admin",
        email="admin@example.com",
        password=generate_password_hash("123"),
        role="admin",
        is_admin=True,
        mobile="123454321",
        address="44, Lalbagh Road, Lucknow",
    )
    db.session.add(admin)

    demo1 = User(
        name="Baskaran",
        email="24f2008200@ds.study.iitm.ac.in",
        password=generate_password_hash("123"),
        role="user",
        is_admin=False,
        mobile="123454321",
        address="44, Lalbagh Road, Lucknow",
        receive_reminders=True,
        reminder_time="18:00",
        google_chat_webhook=default_google_chat_webhook,
    )
    db.session.add(demo1)

    demo2 = User(
        name="Madhavi",
        email="dad@makshi.in",
        password=generate_password_hash("123"),
        role="user",
        is_admin=False,
        mobile="123454321",
        address="44, Lalbagh Road, Lucknow",
        receive_reminders=True,
        reminder_time="18:10",
        google_chat_webhook=default_google_chat_webhook,
    )
    db.session.add(demo2)

    db.session.commit()

    # --------------- Create additional random users ------------------
    users = []
    for i in range(no_users):
        nm = names[i % len(names)]
        email = f"{nm.lower()}@example.com"
        password = generate_password_hash("123")
        mobile = "".join([str(random.randint(6, 9))] + [str(random.randint(0, 9)) for _ in range(9)])
        address = (
            str(random.randint(1, 999)) + ", " +
            random.choice(streets) + ", " +
            random.choice(locations) + ", " +
            random.choice(cities)
        )

        user = User(
            name=nm,
            email=email,
            password=password,
            is_admin=False,
            mobile=mobile,
            role="user",
            address=address,
            receive_reminders=False,
            reminder_time="18:00",
            google_chat_webhook=None,
        )
        db.session.add(user)
        users.append(user)

    db.session.commit()

    # Collect non-admin user ids for reservation assignment (exclude admin)
    regular_users = User.query.filter(User.role == "user").all()
    regular_user_ids = [u.id for u in regular_users]

    # --------------- Insert lots (uses your seed_lots) ------------------
    seed_lots = seed_lots[:no_lots]  # truncate list as per size
    for lot in seed_lots:
        # `lot` items from seed_data might already be ParkingLot objects or dicts; handle both
        if isinstance(lot, ParkingLot):
            db.session.add(lot)
        elif isinstance(lot, dict):
            db.session.add(ParkingLot(**lot))
        else:
            # assume dataclass-like / object with attributes
            db.session.add(ParkingLot(**lot.__dict__))

    db.session.commit()  # Important: triggers after_insert handler to create spots

    # --------------- Load real ParkingSpot rows and group by lot ------------------
    all_spots = ParkingSpot.query.order_by(ParkingSpot.id).all()
    if not all_spots:
        raise RuntimeError("No ParkingSpot rows were created. Ensure ParkingLot.after_insert listener works.")

    spots_by_lot = {}
    for spot in all_spots:
        spots_by_lot.setdefault(spot.lot_id, []).append(spot.id)

    # Build a mapping lot_id -> lot object (for price)
    lots_db = {lot.id: lot for lot in ParkingLot.query.all()}

    # --------------- Build car numbers and drivers ------------------
    # Generate random car registration numbers (same algorithm you used)
    car_numbers = []
    for _ in range(no_cars):
        state = random.choice(state_codes)
        district = f"{random.randint(1, 99):02d}"
        series = random.choice(string.ascii_uppercase)
        number = f"{random.randint(1, 9999):04d}"
        car_number = f"{state} {district}{series} {number}"
        car_numbers.append(car_number)

    # Drivers dict from seed `drivers` list (expecting list of dicts with 'name' and 'mobile')
    drivers_dict = {entry["name"]: entry["mobile"] for entry in drivers[:no_drivers]}
    driver_names = list(drivers_dict.keys())

    # --------------- Availability trackers: per car and per spot ------------------
    # car_next_free: maps car_number -> datetime or None (None means free)
    car_next_free = {car: None for car in car_numbers}

    # spot_next_free: maps spot_id -> datetime or None
    spot_next_free = {spot.id: None for spot in all_spots}

    # --------------- Time weighting / optional demand shaping ------------------
    time_weights = {
        8: 0.3, 9: 0.5, 10: 0.6, 11: 0.7,
        12: 1.0, 13: 1.0, 14: 0.9, 15: 0.8,
        16: 0.7, 17: 0.8, 18: 0.6, 19: 0.5, 20: 0.4
    }

    # --------------- Reservation generation ------------------
    def generate_reservations_fixed(history_days):
        reservations = []

        today_date = date.today()
        start_date = today_date - timedelta(days=history_days - 1)

        # Flatten lot list for selection
        lots_list = list(lots_db.values())

        for day_offset in range(history_days):
            the_date = start_date + timedelta(days=day_offset)
            weekday = the_date.weekday()
            weekend_boost = 1.5 if weekday >= 5 else 1.0

            for hour in range(8, 21):  # 8 AM – 8 PM inclusive
                now = datetime.datetime.combine(the_date, time(hour))

                # Compute demand weight
                weight = time_weights.get(hour, 0.5) * weekend_boost

                # For each hour we select a random subset of lots to host reservations
                # This simulates activity across lots
                lots_sample = random.sample(lots_list, k=min(len(lots_list), max(1, int(len(lots_list) * 0.5))))
                for lot in lots_sample:
                    lot_spot_ids = spots_by_lot.get(lot.id, [])
                    if not lot_spot_ids:
                        continue

                    # free spots in this lot at 'now'
                    free_spots = [
                        sp for sp in lot_spot_ids
                        if spot_next_free.get(sp) is None or spot_next_free.get(sp) <= now
                    ]

                    # free cars at 'now'
                    free_cars = [
                        car for car, free_at in car_next_free.items()
                        if free_at is None or free_at <= now
                    ]

                    if not free_spots or not free_cars:
                        continue

                    # Determine how many reservations to attempt for this lot & hour
                    base_min = max(1, int(len(free_spots) * 0.02))
                    base_max = max(1, int(len(free_spots) * 0.15))
                    num_reservations = random.randint(base_min, min(base_max, len(free_spots)))
                    num_reservations = max(1, int(num_reservations * weight))

                    # Cap by available resources
                    num_reservations = min(num_reservations, len(free_spots), len(free_cars))

                    random.shuffle(free_spots)
                    random.shuffle(free_cars)

                    for _ in range(num_reservations):
                        if not free_spots or not free_cars:
                            break

                        car = free_cars.pop()
                        spot_id = free_spots.pop()
                        driver = random.choice(driver_names) if driver_names else None
                        driver_mobile = drivers_dict.get(driver) if driver else None

                        duration_hours = random.randint(1, 6)
                        end_time = now + timedelta(hours=duration_hours)

                        # small chance it's ongoing (end_time = None)
                        if random.random() < 0.20:
                            end_time = None

                        # Register reservation entry
                        reservations.append({
                            "car": car,
                            "lot_id": lot.id,
                            "spot_id": spot_id,
                            "driver": driver,
                            "driver_mobile": driver_mobile,
                            "start_time": now,
                            "end_time": end_time
                        })

                        # update availability trackers
                        car_next_free[car] = end_time
                        spot_next_free[spot_id] = end_time

        return reservations

    # Generate reservations using environment-driven days
    reservations = generate_reservations_fixed(no_of_back_days)

    # --------------- Insert reservations into DB ------------------
    created_count = 0
    for r in reservations:
        # Protect: skip if spot or car is in inconsistent state in DB (very unlikely)
        spot = db.session.get(ParkingSpot, r["spot_id"])
        lot = lots_db.get(r["lot_id"])

        if not spot or not lot:
            continue

        # Create reservation row
        reservation = Reservation(
            user_id=random.choice(regular_user_ids) if regular_user_ids else None,
            spot_id=spot.id,
            vehicle_number=r["car"],
            driver_contact=r["driver_mobile"],
            driver_name=r["driver"],
            start_time=r["start_time"],
            end_time=r["end_time"]
        )

        # Compute fee if ended
        if r["end_time"] is None:
            spot.status = "O"
            reservation.parking_fee = None
        else:
            spot.status = "A"
            delta = r["end_time"] - r["start_time"]
            hours = delta.total_seconds() / 3600.0
            # Fee uses the lot's price (as requested)
            rate = lot.price if lot and getattr(lot, "price", None) is not None else 10.0
            reservation.parking_fee = round(hours * rate, 2)

        db.session.add(reservation)
        # No immediate commit — commit in bulk after loop
        created_count += 1

    db.session.commit()
    print(f"Seeding complete — inserted {created_count} reservations.")
