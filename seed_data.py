from backend.models import db, User, ParkingLot, ParkingSpot, Reservation

names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Shaurya",
    "Ananya", "Diya", "Aadhya", "Pari", "Avni", "Anika", "Navya", "Myra", "Ira", "Kiara",
    "Lakshmi", "Priya", "Rani", "Kavya", "Pooja", "Sneha", "Nisha", "Radha", "Divya", "Meera",
    "Rahul", "Amit", "Suresh", "Ramesh", "Vijay", "Karthik", "Sanjay", "Deepak", "Manoj", "Arvind",
    "Sunita", "Geeta", "Seema", "Lata", "Rekha", "Neha", "Shreya", "Aarti", "Payal", "Jyoti"
    "Ram","Murugan","Chandran","Devika"
    ]
    # Sample addresses in Indian cities 
streets = [
    "5th Cross Road", "MG Road", "Park Street", "Anna Salai", "Connaught Place",
    "Sector 18", "Baner Road", "Banjara Hills", "Civil Lines", "Lalbagh Road",
    "Brigade Road", "Linking Road", "Camac Street", "Cathedral Road", "Karol Bagh Main Road",
    "Golf Course Road", "FC Road", "Hitech City Road", "MI Road", "Hazratganj Road",
    "Nungambakkam High Road", "Russel Street", "Colaba Causeway", "Commercial Street", "Connaught Lane"
]

locations = [
    "Goregaon West", "Indiranagar", "Park Circus", "Teynampet", "Connaught Circle",
    "Atta Market", "Aundh", "Jubilee Hills", "C-Scheme", "Hazratganj",
    "Ashok Nagar", "Bandra West", "Elgin", "Gopalapuram", "Karol Bagh",
    "DLF Phase 1", "Deccan Gymkhana", "Madhapur", "Civil Lines", "Kaiserbagh",
    "Adyar", "Shakespeare Sarani", "Fort", "Shivaji Nagar", "Janpath"
]

cities = [
    "Mumbai", "Bangalore", "Kolkata", "Chennai", "New Delhi",
    "Noida", "Pune", "Hyderabad", "Jaipur", "Lucknow",
    "Mysore", "Thane", "Chandigarh", "Coimbatore", "Bhopal",
    "Gurgaon", "Nagpur", "Visakhapatnam", "Udaipur", "Kanpur",
    "Madurai", "Patna", "Ahmedabad", "Mangalore", "Ranchi"
]

    
    # --- Add Parking Lots with Spots ---
lots = [
    ParkingLot(
        name="Railway Station",
        prefix="RS",
        address="123 Station Road, Egmore, Chennai",
        pin_code="600001",
        price=50,
        max_slots=25
    ),
    ParkingLot(
        name="Mall Parking Lot",
        prefix="MPL",
        address="456 Phoenix Market Road, Velachery, Chennai",
        pin_code="600042",
        price=40,
        max_slots=75
    ),
    ParkingLot(
        name="City Center",
        prefix="CC",
        address="789 Brigade Road, MG Road, Bangalore",
        pin_code="560001",
        price=30,
        max_slots=50
    ),
    ParkingLot(
        name="Airport Parking",
        prefix="AP",
        address="Near Terminal 1, IGI Airport, New Delhi",
        pin_code="110037",
        price=100,
        max_slots=100
    ),
    ParkingLot(
        name="Bus Stand Parking",
        prefix="BSP",
        address="Majestic Bus Stand, Kempegowda, Bangalore",
        pin_code="560009",
        price=25,
        max_slots=25
    ),
    ParkingLot(
        name="Tech Park Parking",
        prefix="TPP",
        address="Outer Ring Road, Whitefield, Bangalore",
        pin_code="560066",
        price=35,
        max_slots=50
    ),
    ParkingLot(
        name="Old City Market",
        prefix="OCM",
        address="Charminar Market Road, Hyderabad",
        pin_code="500002",
        price=20,
        max_slots=40
    ),
    ParkingLot(
        name="Beachside Parking",
        prefix="BSPC",
        address="Marina Beach Road, Chennai",
        pin_code="600005",
        price=30,
        max_slots=75
    ),
    ParkingLot(
        name="Shopping Complex",
        prefix="SC",
        address="MG Road, Pune",
        pin_code="411001",
        price=40,
        max_slots=40
    ),
    ParkingLot(
        name="Sports Stadium Parking",
        prefix="SSP",
        address="Eden Gardens Stadium, Kolkata",
        pin_code="700021",
        price=60,
        max_slots=50
    ),
    ParkingLot(
        name="College Campus",
        prefix="CCP",
        address="Delhi University North Campus, Delhi",
        pin_code="110007",
        price=15,
        max_slots=10
    ),
    ParkingLot(
        name="Hospital Parking",
        prefix="HP",
        address="AIIMS Main Road, Ansari Nagar, Delhi",
        pin_code="110029",
        price=25,
        max_slots=40
    ),
    ParkingLot(
        name="Zoo Parking",
        prefix="ZP",
        address="Nehru Zoological Park, Bahadurpura, Hyderabad",
        pin_code="500064",
        price=20,
        max_slots=10
    ),
    ParkingLot(
        name="IT Hub Parking",
        prefix="ITH",
        address="Hitech City, Madhapur, Hyderabad",
        pin_code="500081",
        price=35,
        max_slots=40
    ),
    ParkingLot(
        name="Fort Parking",
        prefix="FP",
        address="Red Fort Road, Chandni Chowk, Delhi",
        pin_code="110006",
        price=30,
        max_slots=25
    ),
    ParkingLot(
        name="Cinema Hall Parking",
        prefix="CHP",
        address="INOX Theatre, Law College Road, Pune",
        pin_code="411004",
        price=20,
        max_slots=20
    ),
    ParkingLot(
        name="Temple Parking",
        prefix="TP",
        address="Meenakshi Amman Temple, Madurai",
        pin_code="625001",
        price=15,
        max_slots=10
    ),
    ParkingLot(
        name="Exhibition Ground",
        prefix="EG",
        address="Pragati Maidan, Mathura Road, Delhi",
        pin_code="110001",
        price=50,
        max_slots=40
    ),
    ParkingLot(
        name="Seaside Promenade",
        prefix="SP",
        address="Promenade Beach Road, Puducherry",
        pin_code="605001",
        price=25,
        max_slots=10
    ),
    ParkingLot(
        name="Hill Station Parking",
        prefix="HSP",
        address="Mall Road, Shimla",
        pin_code="171001",
        price=30,
        max_slots=10
    )
    ]
    

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
