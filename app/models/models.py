from .. import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)  # formerly username
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(200),nullable=False)
    role = db.Column(db.String(50), default='user')  # 'admin' or 'user'

    reservations = db.relationship('Reservation', backref='user', lazy=True)

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)  # hourly price
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))
    max_spots = db.Column(db.Integer, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # 'A' for Available, 'O' for Occupied

    reservations = db.relationship('Reservation', backref='spot', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    expected_leaving_timestamp = db.Column(db.DateTime, nullable=False)
    actual_leaving_timestamp = db.Column(db.DateTime, nullable=True)
    vehicle_number = db.Column(db.String(20),nullable=False)
    cost_per_hour = db.Column(db.Float, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

    @property
    def total_hours(self):
        """Calculate duration between parking and actual leaving (or now if still active)."""
        end_time = self.actual_leaving_timestamp or datetime.utcnow()
        duration = end_time - self.parking_timestamp
        return round(duration.total_seconds() / 3600, 2)

    @property
    def total_cost(self):
        """Total cost based on duration and hourly rate."""
        return round(self.total_hours * self.cost_per_hour, 2)

    def assign_rate_from_lot(self):
        """Assigns rate from the associated parking lot."""
        self.cost_per_hour = self.spot.lot.price
