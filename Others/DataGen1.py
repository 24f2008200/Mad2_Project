import random
import datetime
import string

NUM_SLOTS = 75
NUM_CARS = 200
NUM_DRIVERS = 100

drivers = [
    {"name": "Aarav Sharma", "mobile": "9876543210"},
    {"name": "Vivaan Gupta", "mobile": "9123456780"},
    {"name": "Aditya Verma", "mobile": "9812345678"},
    {"name": "Vihaan Mehta", "mobile": "9867543210"},
    {"name": "Arjun Iyer", "mobile": "9823456789"},
    {"name": "Sai Reddy", "mobile": "9845671234"},
    {"name": "Reyansh Nair", "mobile": "9765432189"},
    {"name": "Krishna Das", "mobile": "9912345670"},
    {"name": "Ishaan Kulkarni", "mobile": "9876501234"},
    {"name": "Kabir Choudhury", "mobile": "9798123456"},
    {"name": "Rohan Mishra", "mobile": "9876123450"},
    {"name": "Aryan Saxena", "mobile": "9811122233"},
    {"name": "Manav Joshi", "mobile": "9822211334"},
    {"name": "Omkar Patil", "mobile": "9899988776"},
    {"name": "Hrithik Desai", "mobile": "9933445566"},
    {"name": "Dev Malhotra", "mobile": "9944556677"},
    {"name": "Nikhil Bhatia", "mobile": "9988776655"},
    {"name": "Kunal Kapoor", "mobile": "9877001122"},
    {"name": "Siddharth Jain", "mobile": "9766001122"},
    {"name": "Yash Agarwal", "mobile": "9911223344"},
    {"name": "Ayaan Khan", "mobile": "9922334455"},
    {"name": "Aniket Roy", "mobile": "9933441122"},
    {"name": "Piyush Ghosh", "mobile": "9877665544"},
    {"name": "Pranav Banerjee", "mobile": "9765443322"},
    {"name": "Lakshay Mukherjee", "mobile": "9911887766"},
    {"name": "Atharv Chatterjee", "mobile": "9812233445"},
    {"name": "Rudra Bhattacharya", "mobile": "9899112233"},
    {"name": "Anshul Dey", "mobile": "9944001122"},
    {"name": "Kartik Sen", "mobile": "9877554411"},
    {"name": "Mihir Paul", "mobile": "9766778899"},
    {"name": "Shivansh Bose", "mobile": "9922003344"},
    {"name": "Tanishq Nath", "mobile": "9877889900"},
    {"name": "Rajat Ghoshal", "mobile": "9811002233"},
    {"name": "Samarth Mondal", "mobile": "9844556677"},
    {"name": "Varun Saha", "mobile": "9877009988"},
    {"name": "Harshad Basu", "mobile": "9766554433"},
    {"name": "Chirag Lahiri", "mobile": "9933447788"},
    {"name": "Saurav Panicker", "mobile": "9822334455"},
    {"name": "Jayant Pillai", "mobile": "9811334455"},
    {"name": "Deepak Menon", "mobile": "9911224455"},
    {"name": "Akhil Kurup", "mobile": "9922331100"},
    {"name": "Anirudh Nambiar", "mobile": "9876003344"},
    {"name": "Roshan Warrier", "mobile": "9988771122"},
    {"name": "Abhay Shetty", "mobile": "9911998877"},
    {"name": "Vikram Naidu", "mobile": "9877445566"},
    {"name": "Gaurav Raju", "mobile": "9822113344"},
    {"name": "Rakesh Rao", "mobile": "9766553322"},
    {"name": "Tarun Ramesh", "mobile": "9911882200"},
    {"name": "Sanjay Mohan", "mobile": "9877664411"},
    {"name": "Naveen Shankar", "mobile": "9922441133"},
    {"name": "Ashwin Prasad", "mobile": "9811445566"},
    {"name": "Rajesh Krishnan", "mobile": "9877001122"},
    {"name": "Suraj Pillai", "mobile": "9933224455"},
    {"name": "Ajay Kannan", "mobile": "9822445566"},
    {"name": "Praveen Subramanian", "mobile": "9811667788"},
    {"name": "Karthik Muralidharan", "mobile": "9911002233"},
    {"name": "Balaji Swaminathan", "mobile": "9877556677"},
    {"name": "Vinod Sekar", "mobile": "9944002233"},
    {"name": "Srinivas Venkatesh", "mobile": "9877991122"},
    {"name": "Arvind Jayaraman", "mobile": "9922330099"},
    {"name": "Lokesh Sundar", "mobile": "9877112233"},
    {"name": "Mahesh Narayanan", "mobile": "9811223344"},
    {"name": "Ravindra Manohar", "mobile": "9766557788"},
    {"name": "Anupam Dev", "mobile": "9944332211"},
    {"name": "Hemant Barua", "mobile": "9877332211"},
    {"name": "Sudhir Phukan", "mobile": "9811778899"},
    {"name": "Nitin Gogoi", "mobile": "9822447788"},
    {"name": "Sandeep Bora", "mobile": "9922558899"},
    {"name": "Alok Kalita", "mobile": "9877558899"},
    {"name": "Rajat Medhi", "mobile": "9811993344"},
    {"name": "Vivek Bhuyan", "mobile": "9944112233"},
    {"name": "Dipankar Dasgupta", "mobile": "9911335577"},
    {"name": "Debashish Senapati", "mobile": "9877662233"},
    {"name": "Santosh Pattnaik", "mobile": "9811009988"},
    {"name": "Prakash Mohanty", "mobile": "9933442211"},
    {"name": "Harish Swain", "mobile": "9822331199"},
    {"name": "Shankar Behera", "mobile": "9911228899"},
    {"name": "Sunil Sethi", "mobile": "9877552211"},
    {"name": "Ajith Panda", "mobile": "9811772233"},
    {"name": "Keshav Tripathi", "mobile": "9766009988"},
    {"name": "Mohan Tiwari", "mobile": "9911442233"},
    {"name": "Ashutosh Shukla", "mobile": "9877223344"},
    {"name": "Ravishankar Dwivedi", "mobile": "9811998877"},
    {"name": "Gopal Upadhyay", "mobile": "9933441199"},
    {"name": "Santosh Pandey", "mobile": "9922337788"},
    {"name": "Anil Chaturvedi", "mobile": "9877002233"},
    {"name": "Brijesh Dubey", "mobile": "9822556677"},
    {"name": "Naresh Jha", "mobile": "9811224455"},
    {"name": "Lalit Thakur", "mobile": "9877556677"},
    {"name": "Dinesh Rawat", "mobile": "9911004455"},
    {"name": "Rajiv Negi", "mobile": "9922003344"},
    {"name": "Prem Nautiyal", "mobile": "9811771122"},
    {"name": "Anup Kandpal", "mobile": "9877443322"},
    {"name": "Devendra Bisht", "mobile": "9933221100"},
    {"name": "Manoj Joshi", "mobile": "9811667788"},
    {"name": "Keshar Singh", "mobile": "9877554433"},
    {"name": "Surendra Chauhan", "mobile": "9922445566"},
    {"name": "Harinder Rana", "mobile": "9911992233"},
    {"name": "Gurpreet Singh", "mobile": "9877004455"},
    {"name": "Balvinder Kaur", "mobile": "9811221133"},
    {"name": "Jaspreet Gill", "mobile": "9877552211"},
    {"name": "Amarjeet Sandhu", "mobile": "9933445566"},
    {"name": "Parminder Sidhu", "mobile": "9877112233"},
    {"name": "Harpal Dhillon", "mobile": "9811994455"},
    {"name": "Ravinder Brar", "mobile": "9766551122"}
]

# Example car/driver pools
state_codes = ["MH", "DL", "KA", "TN", "WB", "UP", "RJ", "GJ", "KL", "AP", "MP", "HR", "PB", "BR", "OD"]

NUM_CARS = 100
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

import datetime, random

def generate_reservations(history_days=7):
    reservations = []
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=history_days-1)

    # Track when each car is next available
    car_next_free = {car: start_date for car in car_numbers}

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

            base_min, base_max = 5, 30
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

                duration = random.choice([1, 2, 3, 4])
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
                    "start_time": str(start_time),
                    "end_time": str(end_time) if end_time else None
                })

    return reservations

# Example usage
if __name__ == "__main__":
    data = generate_reservations(5)  # 5 days
    for r in data[:40]:  # show first 40
        print(r)
    print(f"\nGenerated total {len(data)} reservations.")
names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Shaurya",
    "Ananya", "Diya", "Aadhya", "Pari", "Avni", "Anika", "Navya", "Myra", "Ira", "Kiara",
    "Lakshmi", "Priya", "Rani", "Kavya", "Pooja", "Sneha", "Nisha", "Radha", "Divya", "Meera",
    "Rahul", "Amit", "Suresh", "Ramesh", "Vijay", "Karthik", "Sanjay", "Deepak", "Manoj", "Arvind",
    "Sunita", "Geeta", "Seema", "Lata", "Rekha", "Neha", "Shreya", "Aarti", "Payal", "Jyoti"
]

# Sample addresses in Indian cities
addresses = [
    "156, 5th Cross Road, Goregaon West, Mumbai",
    "22, MG Road, Indiranagar, Bangalore",
    "47, Park Street, Kolkata",
    "89, Anna Salai, Teynampet, Chennai",
    "12, Connaught Place, New Delhi",
    "78, Sector 18, Noida",
    "34, Baner Road, Pune",
    "56, Banjara Hills, Hyderabad",
    "9, Civil Lines, Jaipur",
    "44, Lalbagh Road, Lucknow"
]
