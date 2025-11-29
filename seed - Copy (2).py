import os
from backend.models import db, User, ParkingLot, ParkingSpot, Reservation
from datetime import datetime, timedelta, UTC
from werkzeug.security import generate_password_hash
from backend.app import create_app, db
from backend.models import User
import random
from seed_data import *
from dotenv import load_dotenv

load_dotenv()

default_google_chat_webhook = os.getenv("DEFAULT_GOOGLE_CHAT_WEBHOOK", "https://chat.googleapis.com/v1/spaces/AAQAwtQ63ag/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=5MYSUrPN6reLnOlxNcejvgkOJ35PtxS2QRY6c_FTM7c")

size = int(os.getenv("DATA_SIZE", 0))

no_users = 5 if size == 0 else 25 if size ==1 else 50
no_lots = 5 if size == 0 else 10 if size ==1 else 20
no_drivers = 5 if size == 0 else 50 if size ==1 else 100
no_cars = 5 if size == 0 else 50 if size ==1 else 100
no_of_back_days= 30 if size == 0 else 60 if size ==1 else 90
no_of_back_days *= 2


app = create_app(False,size)

with app.app_context():
    db.drop_all()
    db.create_all()



    admin = User(
        name="Admin",
        email="admin@example.com",
        password=generate_password_hash("123"),
        role="admin",
        is_admin=True,
        mobile="123454321",
        address="44, Lalbagh Road, Lucknow"
    )
    db.session.add(admin)
    admin2 = User(
        name="Baskaran",
        email="24f2008200@ds.study.iitm.ac.in",
        password=generate_password_hash("123"),
        role="user",
        is_admin=False,
        mobile="123454321",
        address="44, Lalbagh Road, Lucknow",
        receive_reminders = True,
        reminder_time = "18:00",
        google_chat_webhook = default_google_chat_webhook
    )
    db.session.add(admin2)
    admin3 = User(
        name="Madhavi",
        email="dad@makshi.in",
        password=generate_password_hash("123"),
        role="user",
        is_admin=False,
        mobile="123454321",
        address="44, Lalbagh Road, Lucknow",
        receive_reminders = True,
        reminder_time = "18:10",
        google_chat_webhook = default_google_chat_webhook
    )
    db.session.add(admin3)
    users = []
    for i in range(no_users):
        name = names[i]
        email = f"{name.lower()}@example.com"
        # pwd = f"{name[:3].lower()}123"
        pwd = "123"
        password = generate_password_hash(pwd)
        mobile = "".join([str(random.randint(6, 9))] + [str(random.randint(0, 9)) for _ in range(9)])
        address = str(random.randint(6, 9)) +"," + random.choice(streets) \
            +","  +  random.choice(locations) \
            +"," + random.choice(cities)
        user = User(
            name = name,
            email= email,
            password = password,
            is_admin= False,
            mobile = mobile,
            role = "user",
            address = address,
            receive_reminders = False,
            reminder_time = "18:00",
            google_chat_webhook = None
        )
        db.session.add(user)
        db.session.flush()
        db.session.commit()


    lots = lots[:no_lots]
    for lot in lots:
        db.session.add(lot)
        # db.session.flush()
    db.session.commit()

    s =0
    for l in lots:
        s += l.max_slots
    import random
    import datetime
    import string

    NUM_SLOTS = s
    

    NUM_CARS = no_cars
    drivers = drivers[:no_drivers]
    NUM_DRIVERS = len(drivers)
    car_numbers = []

    for _ in range(NUM_CARS):
        state = random.choice(state_codes)                       # 2-letter state
        district = f"{random.randint(1, 99):02d}"               # 2-digit district
        series = random.choice(string.ascii_uppercase)           # 1 letter
        number = f"{random.randint(1, 9999):04d}"               # 4-digit number
        car_number = f"{state} {district}{series} {number}"
        car_numbers.append(car_number)
    drivers_dict = {entry["name"]: entry["mobile"] for entry in drivers}
    driver_names = list(drivers_dict.keys())
    # Spot weight levels
    spot_weights = []
    for i in range(1, NUM_SLOTS+1):
        if 1 <= i <= 5:       # VIP
            spot_weights.append(10)
        elif 6 <= i <= 15:    # Premium
            spot_weights.append(5)
        else:                 # Normal
            spot_weights.append(1)

    # Time dependency (hour → weight for demand)
    time_weights = {
        # Morning
        8: 0.3, 9: 0.5, 10: 0.6, 11: 0.7,
        # Midday peak
        12: 1.0, 13: 1.0, 14: 0.9, 15: 0.8,
        # Evening
        16: 0.7, 17: 0.8, 18: 0.6, 19: 0.5, 20: 0.4
    }



    def generate_reservations(history_days=7):
        reservations = []
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=history_days-1)

        # Track when each car is next available
        car_next_free = {
            car: datetime.datetime.combine(start_date, datetime.time(8))
            for car in car_numbers
        }

        for day_offset in range(history_days):
            date = start_date + datetime.timedelta(days=day_offset)
            weekday = date.weekday()  # Monday=0, Sunday=6

            weekend_boost = 1.5 if weekday >= 5 else 1.0

            for hour in range(8, 21):  # 8 AM – 8 PM
                now = datetime.datetime.combine(date, datetime.time(hour))

                available_cars = [
                    car for car, free_time in car_next_free.items()
                    if now >= free_time
                ]
                available_drivers = driver_names[:]
                available_spots = list(range(1, NUM_SLOTS+1))

                base_min, base_max = int(NUM_SLOTS*.1), int(NUM_SLOTS*.9)
                weight = time_weights.get(hour, 0.5) * weekend_boost
                num_reservations = random.randint(
                    int(base_min * weight),
                    max(int(base_max * weight), 1)
                )

                for _ in range(num_reservations):
                    if not available_cars or not available_drivers or not available_spots:
                        break

                    car = random.choice(available_cars)
                    available_cars.remove(car)

                    driver = random.choice(available_drivers)
                    driver_mobile = drivers_dict[driver]
                    available_drivers.remove(driver)

                    weights = [spot_weights[s-1] for s in available_spots]
                    spot_no = random.choices(available_spots, weights=weights, k=1)[0]
                    available_spots.remove(spot_no)

                    duration = random.randint(1,48)
                    start_time = now
                    end_time = start_time + datetime.timedelta(hours=duration)

                    # If past 8 PM, leave it as ongoing (overnight)
                    if end_time.hour > 20:
                        end_time = None

                    # Update car availability
                    if end_time:
                        car_next_free[car] = end_time
                    else:
                        car_next_free[car] = datetime.datetime.combine(
                            date + datetime.timedelta(days=1),
                            datetime.time(8)
                        )

                    reservations.append({
                        "date": str(date),
                        "hour": hour,
                        "spot": spot_no,
                        "car": car,
                        "driver": driver,
                        "driver_mobile": driver_mobile,
                        "start_time": (start_time),
                        "end_time": (end_time) if end_time else None
                    })

        return reservations

    reservations = generate_reservations(no_of_back_days)
    #no_users = len(names)
    for r in reservations:
        res = Reservation(
        user_id= random.randint(1, no_users),
        spot_id=r["spot"],
        vehicle_number=r["car"],
        start_time=r["start_time"],
        end_time= r["end_time"] ,
        driver_contact=r["driver_mobile"],
        driver_name=r["driver"]
        )
        slot = db.session.get(ParkingSpot, res.spot_id)
        if res.end_time is None:
            slot.status = "O"
            res.parking_fee = None
        else:
            slot.status = "A"
            delta = res.end_time - res.start_time
            hours = delta.total_seconds() / 3600
            fee = round(hours * 10, 2)  # Assuming a rate of 10 per hour
            res.parking_fee = fee
        db.session.add(res)
        db.session.flush()
        db.session.commit()

    print("Job Done")

            




    #         start_time=datetime.strptime(r["start_time"], "%Y-%m-%d %H:%M:%S"),
    #         end_time= datetime.strptime(r["end_time"], "%Y-%m-%d %H:%M:%S") if r["end_time"] else None,
    #         driver_contact=f"{r['telephone']}",
    #         driver_name= r["name"],

    #     )
    #     if reservation.end_time is None:
    #         spot.status = "O"
    #         reservation.parking_fee = None
    #     else:
    #         delta = reservation.end_time - reservation.start_time
    #         hours = delta.total_seconds() / 3600
    #         fee = round(hours * 10, 2)  # Assuming a rate of 10 per hour
    #         reservation.parking_fee = fee
    #     db.session.add(reservation)

    # db.session.commit()
    # print("✅ Database initialized with dummy data!")
