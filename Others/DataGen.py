import random
import datetime
import json

# -----------------------------
# Configurable parameters
# -----------------------------
NUM_DRIVERS = 15
NUM_CARS = 25
NUM_SLOTS = 75
NUM_DAYS = 3
START_HOUR = 8
END_HOUR = 20

# -----------------------------
# Sample data
# ----------------------------- 
driver_names = [
    "Amit Sharma", "Priya Singh", "Ravi Kumar", "Neha Patel",
    "Suresh Reddy", "Anita Verma", "Arjun Nair", "Kavita Iyer",
    "Vikram Chauhan", "Meena Joshi", "Rahul Desai", "Pooja Bhatia",
    "Manish Gupta", "Sneha Kapoor", "Deepak Malhotra"
]

phone_numbers = [
    "9876543210", "9123456780", "9988776655", "9112233445",
    "9345678901", "9765432109", "9898989898", "9001122334",
    "9222333444", "9334455667", "9445566778", "9556677889",
    "9667788990", "9778899001", "9889900112"
]

car_numbers = [f"MH01AB{1000+i}" for i in range(NUM_CARS)]

# -----------------------------
# Generate reservations
# -----------------------------
reservations = []
user_ids = list(range(1, 9))  # user_no < 8

start_date = datetime.date.today()

# Schedules
car_schedule = {car: [] for car in car_numbers}
spot_schedule = {spot: [] for spot in range(1, NUM_SLOTS+1)}

for day in range(NUM_DAYS):
    current_date = start_date + datetime.timedelta(days=day)

    for hour in range(START_HOUR, END_HOUR):
        num_reservations = random.randint(3, 10)

        for _ in range(num_reservations):
            driver_idx = random.randint(0, NUM_DRIVERS - 1)
            driver = driver_names[driver_idx]
            phone = phone_numbers[driver_idx]

            start_time = datetime.datetime.combine(current_date, datetime.time(hour, 0, 0))

            # --- Find free cars ---
            available_cars = []
            for car, bookings in car_schedule.items():
                conflict = False
                for s, e in bookings:
                    if e is None or (s <= start_time < e):
                        conflict = True
                        break
                if not conflict:
                    available_cars.append(car)

            if not available_cars:
                continue  # no free cars

            car = random.choice(available_cars)

            # --- Find free spots ---
            available_spots = []
            for spot, bookings in spot_schedule.items():
                conflict = False
                for s, e in bookings:
                    if e is None or (s <= start_time < e):
                        conflict = True
                        break
                if not conflict:
                    available_spots.append(spot)

            if not available_spots:
                continue  # no free spots

            spot_no = random.choice(available_spots)

            # Random duration
            duration_hours = random.choice([1, 2, 3, 4, 5, 6])
            if random.random() < 0.2:  # 20% chance overnight
                end_time = None
            else:
                end_time = start_time + datetime.timedelta(hours=duration_hours)
                if end_time.hour > END_HOUR:
                    end_time = None

            # --- Record in schedules ---
            car_schedule[car].append((start_time, end_time))
            spot_schedule[spot_no].append((start_time, end_time))

            reservations.append({
                "user_no": random.choice(user_ids),
                "spot_no": spot_no,
                "car_reg_no": car,
                "telephone": phone,
                "driver_name": driver,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else None
            })

# -----------------------------
# Save to JSON file
# -----------------------------
with open("reservations.json", "w") as f:
    json.dump(reservations, f, indent=4)

print(f"Generated {len(reservations)} reservations. Saved to reservations.json")
