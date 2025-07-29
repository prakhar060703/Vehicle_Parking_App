from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from .. import db
from ..models.models import User, ParkingLot, ParkingSpot, Reservation  # Make sure these models exist

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.welcome'))

@auth_bp.route('/welcome')
def welcome():
    return render_template('welcome.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pwd = request.form['password']

        user = User.query.filter_by(email=email, password=pwd).first()

        if user:
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('auth.admin_dashboard'))
            else:
                return redirect(url_for('auth.home'))
        else:
            flash("Invalid email or password", "danger")
    
    return render_template('login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        pin_code = request.form['pin_code']
        address = request.form['address']

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('auth.signup'))

        new_user = User(
            name=name,
            email=email,
            password=password,
            pin_code=pin_code,
            address=address
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


@auth_bp.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    user_reservations = Reservation.query.filter_by(user_id=user_id).all()

    return render_template(
        'home.html',
        name=user.name,  # using updated 'name' field
        email=user.email,
        reservations=user_reservations
    )




@auth_bp.route('/view_reservation/<int:reservation_id>')
def view_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)

    # Authorization check
    if reservation.user_id != session.get('user_id') and session.get('role') != 'admin':
        flash("Access denied.")
        return redirect(url_for('auth.home'))

    # Calculate reserved hours
    

    return render_template(
        'view_reservation.html',
        reservation=reservation,
        
    )


@auth_bp.route('/delete_reservation/<int:reservation_id>')
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)

    # Authorization check
    if reservation.user_id != session.get('user_id') and session.get('role') != 'admin':
        flash("Not authorized to complete this reservation.")
        return redirect(url_for('auth.home'))

    # Prevent re-completing
    if reservation.actual_leaving_timestamp:
        flash("Reservation already marked as completed.")
        if session.get('role') == 'admin':
            return redirect(url_for('auth.admin_dashboard'))
        return redirect(url_for('auth.home'))

    # Mark actual leaving time
    reservation.actual_leaving_timestamp = datetime.utcnow()

    # Make the spot available again
    reservation.spot.status = 'A'

    db.session.commit()
    flash("Reservation completed and spot marked available.")
    
    # Redirect based on role
    if session.get('role') == 'admin':
        return redirect(url_for('auth.admin_dashboard'))
    return redirect(url_for('auth.home'))







@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))




# --- Admin Dashboard ---
@auth_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    lots = ParkingLot.query.filter_by(is_deleted=False).all()
    users = User.query.filter_by(role='user').all()
    reservations = Reservation.query.all()

    

    lot_data = []
    for lot in lots:
        total = len(lot.spots)
        occupied = sum(1 for spot in lot.spots if spot.status == 'O')
        available = total - occupied
        lot_data.append({
            "name": lot.prime_location_name,
            "available": available,
            "occupied": occupied
        })

    return render_template("admin_dashboard.html", lots=lots, users=users, reservations=reservations, lot_data=lot_data)

    
    


@auth_bp.route('/create_lot', methods=['GET', 'POST'])
def create_lot():
    if 'role' not in session or session['role'] != 'admin':
        flash("Admin access required.")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        address = request.form['address']
        pin_code = request.form['pin_code']
        max_spots = int(request.form['max_spots'])

        # Create the parking lot
        lot = ParkingLot(
            prime_location_name=name,
            price=price,
            address=address,
            pin_code=pin_code,
            max_spots=max_spots
        )
        db.session.add(lot)
        db.session.commit()  # Commit once to get the lot.id for spots

        # Create parking spots
        for _ in range(max_spots):
            spot = ParkingSpot(lot_id=lot.id, status='A')
            db.session.add(spot)

        db.session.commit()
        flash(" Parking lot and spots created successfully!")
        return redirect(url_for('auth.admin_dashboard'))

    return render_template('create_lot.html')



@auth_bp.route('/lot/<int:lot_id>/spots')
def view_spots(lot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    lot = ParkingLot.query.filter_by(id=lot_id, is_deleted=False).first_or_404()

    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    return render_template('view_spots.html', lot=lot, spots=spots)

@auth_bp.route('/reserve/<int:spot_id>', methods=['GET', 'POST'])
def reserve_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    user_role = session.get('role')

    # If spot is already booked
    if spot.status == 'O':
        reservation = Reservation.query.filter_by(spot_id=spot.id, is_deleted=False).first()
        if user_role == 'admin':
            return render_template('view_reservation_admin.html', reservation=reservation, spot=spot)
        else:
            flash("This spot is already reserved.")
            return redirect(url_for('auth.view_spots', lot_id=spot.lot_id))

    if request.method == 'POST':
        # Admin can reserve for another user
        if user_role == 'admin':
            user_id = int(request.form['user_id'])
        else:
            user_id = session.get('user_id')

        try:
            booking_time_str = request.form['booking_time']  # e.g., "2025-07-29T14:00"
            booking_timestamp = datetime.strptime(booking_time_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date/time format.")
            return redirect(request.url)

        duration_hours = float(request.form['duration'])
        leaving_timestamp = booking_timestamp + timedelta(hours=duration_hours)
        vehicle_number = request.form['vehicle_number']

        reservation = Reservation(
            spot_id=spot.id,
            user_id=user_id,
            parking_timestamp=booking_timestamp,
            expected_leaving_timestamp=leaving_timestamp,
            cost_per_hour=spot.lot.price,
            vehicle_number=vehicle_number,
            is_deleted=False
        )

        spot.status = 'O'

        db.session.add(reservation)
        db.session.commit()

        flash("Spot reserved successfully.")
        return redirect(url_for('auth.view_spots', lot_id=spot.lot_id))

    # Admin can select users, regular users don’t need to
    users = User.query.all() if user_role == 'admin' else []

    return render_template('reserve_form.html', spot=spot, users=users)


@auth_bp.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    spot = reservation.spot
    user = reservation.user

    if request.method == 'POST':
        try:
            hours = float(request.form['hours'])
            reservation.expected_leaving_timestamp = reservation.parking_timestamp + timedelta(hours=hours)
            db.session.commit()
            flash('Reservation updated successfully!', 'success')
            return redirect(url_for('auth.view_spots', lot_id=spot.lot_id))
        except Exception as e:
            flash(f"Error updating reservation: {e}", 'danger')

    return render_template('edit_reservation.html', reservation=reservation, spot=spot, user=user)


@auth_bp.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.filter_by(id=lot_id, is_deleted=False).first_or_404()


    if request.method == 'POST':
        lot.prime_location_name = request.form['prime_location_name']
        lot.address = request.form['address']
        lot.pin_code = request.form['pin_code']
        lot.price = float(request.form['price'])
        lot.max_spots = int(request.form['max_spots'])

        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('auth.admin_dashboard'))

    return render_template('edit_lot.html', lot=lot)


@auth_bp.route('/search', methods=['GET', 'POST'])
def search_lots():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    results = []
    if request.method == 'POST':
        query = request.form['search'].strip().lower()
        all_lots = ParkingLot.query.filter_by(is_deleted=False).all()
        for lot in all_lots:
            if (query in lot.prime_location_name.lower() or query in lot.address.lower() or query in lot.pin_code):
                available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
                results.append({
                    'id': lot.id,
                    'location': lot.prime_location_name,
                    'address': lot.address,
                    'pin_code':lot.pin_code,
                    'available': available_spots,
                    'price':lot.price
                })
    return render_template('search_results.html', results=results, username=session.get('username'))


@auth_bp.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    lot = ParkingLot.query.filter_by(id=lot_id, is_deleted=False).first_or_404()

    # Check if any spot in the lot is currently occupied (has active reservation)
    occupied = (
        db.session.query(Reservation)
        .join(ParkingSpot)
        .filter(
            ParkingSpot.lot_id == lot_id,
            Reservation.is_deleted == False,
            Reservation.actual_leaving_timestamp.is_(None)
        )
        .first()
    )

    if occupied:
        flash('❌ Cannot delete: One or more spots in this lot are currently occupied.', 'danger')
        return redirect(url_for('auth.admin_dashboard'))

    # Soft-delete the lot
    lot.is_deleted = True

    db.session.commit()
    flash('✅ Parking lot marked as deleted.', 'success')
    return redirect(url_for('auth.admin_dashboard'))

@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # Get form inputs
        name = request.form.get('name')
        email = request.form.get('email')
        pin_code = request.form.get('pin_code')
        address = request.form.get('address')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validate required fields
        if not all([name, email, pin_code, address, current_password]):
            flash('All profile fields and current password are required.', 'error')
            return render_template('edit_profile.html', user=user)

        # Validate current password
        if user.password != current_password:
            flash('Current password is incorrect.', 'error')
            return render_template('edit_profile.html', user=user)

        # If new password is given, check confirmation
        if new_password or confirm_password:
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('edit_profile.html', user=user)
            user.password = new_password  # Update password

        # Update other fields
        user.name = name
        user.email = email
        user.pin_code = pin_code
        user.address = address

        db.session.commit()
        flash('Profile updated successfully!', 'success')

        session.clear()  # logout for security
        return redirect(url_for('auth.login'))

    return render_template('edit_profile.html', user=user)

