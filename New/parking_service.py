from backend.extensions import db
from backend.models import ParkingLot, ParkingSpot

class ParkingService:
    @staticmethod
    def list_all_lots():
        return [lot.to_dict() for lot in ParkingLot.query.all()]

    @staticmethod
    def create_lot(data):
        lot = ParkingLot(
            name=data["name"],
            prefix=data.get("prefix"),
            price=data.get("price", 0),
            address=data.get("address"),
            pin_code=data.get("pin_code"),
            max_slots=data.get("number_of_spots", 0),
        )
        db.session.add(lot)
        db.session.commit()
        return {"message": "Parking lot created", "id": lot.id}

    @staticmethod
    def get_lot(lot_id):
        return ParkingLot.query.get(lot_id)

    @staticmethod
    def delete_lot(lot):
        db.session.delete(lot)
        db.session.commit()
        return {"message": "Lot deleted"}

parking_service = ParkingService()
