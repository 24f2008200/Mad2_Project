# Right now you have many:

# /search/users

# /search/bookings

# /search/lots

# /search/bquery

# Instead, we can unify them into a single endpoint:

# GET /api/admin/search?type=users&search_by=name&value=Arun
# GET /api/admin/search?type=bookings&search_by=vehicle_number&value=TN10
# GET /api/admin/search?type=lots&search_by=pin_code&value=600001
# GET /api/admin/search?type=bquery&search_by=driver&value=Meena


class SearchResource(Resource):
    method_decorators = [admin_required]

    def get(self):
        search_type = request.args.get("type")
        search_by = request.args.get("search_by", "").strip()
        value = request.args.get("value", "").strip()

        if not search_type:
            return {"error": "Missing ?type= parameter"}, 400
        if not value:
            return []

        # -------- USERS --------
        if search_type == "users":
            query = User.query
            if search_by == "name":
                query = query.filter(User.name.ilike(f"%{value}%"))
            elif search_by == "mobile":
                query = query.filter(User.mobile.ilike(f"%{value}%"))
            elif search_by == "email":
                query = query.filter(User.email.ilike(f"%{value}%"))
            elif search_by == "address":
                query = query.filter(User.address.ilike(f"%{value}%"))
            elif search_by == "vehicle":
                query = query.join(Reservation).filter(Reservation.vehicle_number.ilike(f"%{value}%"))
            elif search_by == "driver":
                query = query.join(Reservation).filter(Reservation.driver_name.ilike(f"%{value}%"))
            elif search_by == "parking_lot":
                query = query.join(Reservation).join(ParkingSpot).join(ParkingLot).filter(ParkingLot.name.ilike(f"%{value}%"))
            return [u.to_dict() for u in query.all()]

        # -------- BOOKINGS --------
        elif search_type == "bookings":
            query = Reservation.query.join(User)
            if search_by == "name":
                query = query.filter(User.name.ilike(f"%{value}%"))
            elif search_by == "mobile":
                query = query.filter(User.mobile.ilike(f"%{value}%"))
            elif search_by == "address":
                query = query.filter(User.address.ilike(f"%{value}%"))
            elif search_by == "vehicle_number":
                query = query.filter(Reservation.vehicle_number.ilike(f"%{value}%"))
            elif search_by == "driver":
                query = query.filter(Reservation.driver_name.ilike(f"%{value}%"))
            elif search_by == "parking_lot":
                query = query.join(ParkingSpot).join(ParkingLot).filter(ParkingLot.name.ilike(f"%{value}%"))
            return [r.get_details for r in query.all()]

        # -------- LOTS --------
        elif search_type == "lots":
            # Reuse existing service
            return get_all_lots(), 200

        # -------- BROAD QUERY (bquery) --------
        elif search_type == "bquery":
            results = search_all(search_by)
            return results, 200

        else:
            return {"error": f"Unsupported search type: {search_type}"}, 400


# api.add_resource(SearchResource, "/search")


# GET /api/admin/search?type=users&search_by=email&value=gmail.com
# GET /api/admin/search?type=bookings&search_by=vehicle_number&value=TN10
# GET /api/admin/search?type=lots
# GET /api/admin/search?type=bquery&search_by=driver&value=Meena
