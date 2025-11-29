from backend.extensions import cache
from flask import jsonify
from backend.models import ParkingLot

@cache.cached(timeout=30, key_prefix="all_lots")
def get_all_lots():
    lots = ParkingLot.query.all()
    return [
        {
            "id": lot.id,
            "name": lot.name,
            "prefix": lot.prefix,
            "address": lot.address,
            "pin_code": lot.pin_code,
            "price": lot.price,
            "number_of_spots": lot.number_of_spots,
            "available_spots": sum(1 for s in lot.spots if s.status == "A"),
            "occupied_spots": sum(1 for s in lot.spots if s.status == "O"),
            "spots": [
                spot.get_details
                for spot in lot.spots
            ]
        }
        for lot in lots
    ]

