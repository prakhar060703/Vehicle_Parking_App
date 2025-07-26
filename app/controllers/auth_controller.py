from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from .. import db
from ..models.models import User, ParkingLot, ParkingSpot, Reservation  # Make sure these models exist

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname, password=pwd).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('auth.admin_dashboard'))
            else:
                return redirect(url_for('auth.home'))
        flash("Invalid credentials")
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if User.query.filter_by(username=uname).first():
            flash('Username already exists!')
            return redirect(url_for('auth.signup'))
        new_user = User(username=uname, password=pwd)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user_reservations = Reservation.query.filter_by(user_id=user_id).all()

    return render_template('home.html',
                           username=session.get('username'),
                           reservations=user_reservations)



@auth_bp.route('/view_reservation/<int:reservation_id>')
def view_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != session.get('user_id') and session.get('role') != 'admin':
        flash("Access denied.")
        return redirect(url_for('auth.home'))
    return render_template('view_reservation.html', reservation=reservation)

@auth_bp.route('/delete_reservation/<int:reservation_id>')
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != session.get('user_id') and session.get('role') != 'admin':
        flash("Not authorized to delete this reservation.")
        return redirect(url_for('auth.home'))

    spot = reservation.spot
    spot.status = 'A'  # Mark spot as available again
    db.session.delete(reservation)
    db.session.commit()
    flash("Reservation deleted successfully.")
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

    lots = ParkingLot.query.all()
    users = User.query.filter_by(role='user').all()
    reservations = Reservation.query.all()

    return render_template(
        'admin_dashboard.html',
        lots=lots,
        users=users,
        reservations=reservations
    )


@auth_bp.route('/create_lot', methods=['GET', 'POST'])
def create_lot():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        address = request.form['address']
        pin_code = request.form['pin_code']
        max_spots = int(request.form['max_spots'])

        lot = ParkingLot(
            prime_location_name=name,
            price=price,
            address=address,
            pin_code=pin_code,
            max_spots=max_spots
        )
        db.session.add(lot)
        db.session.commit()

        for _ in range(max_spots):
            spot = ParkingSpot(lot_id=lot.id, status='A')
            db.session.add(spot)

        db.session.commit()
        flash("Parking lot created successfully!")
        return redirect(url_for('auth.admin_dashboard'))

    return render_template('create_lot.html')


@auth_bp.route('/lot/<int:lot_id>/spots')
def view_spots(lot_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    return render_template('view_spots.html', lot=lot, spots=spots)

@auth_bp.route('/reserve/<int:spot_id>', methods=['GET', 'POST'])
def reserve_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    user_role = session.get('role')

    # If spot is already booked
    if spot.status == 'O':
        reservation = Reservation.query.filter_by(spot_id=spot.id).first()

        if user_role == 'admin':
            return render_template('view_reservation_admin.html', reservation=reservation, spot=spot)
        else:
            flash("This spot is already reserved.")
            return redirect(url_for('auth.view_spots', lot_id=spot.lot_id))

    # If available, show reservation form
    if request.method == 'POST':
        user_id = int(request.form['user_id'])  # Admin chooses user or current session user
        hours = float(request.form['hours'])
        leaving = datetime.utcnow() + timedelta(hours=hours)
        
        reservation = Reservation(
            spot_id=spot.id,
            user_id=user_id,
            cost_per_hour=spot.lot.price,
            leaving_timestamp=leaving
        )
        spot.status = 'O'
        db.session.add(reservation)
        db.session.commit()
        flash("Spot reserved.")
        return redirect(url_for('auth.view_spots', lot_id=spot.lot_id))

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
            reservation.leaving_timestamp = reservation.parking_timestamp + timedelta(hours=hours)
            db.session.commit()
            flash('Reservation updated successfully!', 'success')
            return redirect(url_for('auth.view_spots', lot_id=spot.lot_id))
        except Exception as e:
            flash(f"Error updating reservation: {e}", 'danger')

    return render_template('edit_reservation.html', reservation=reservation, spot=spot, user=user)


@auth_bp.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

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
        all_lots = ParkingLot.query.all()
        for lot in all_lots:
            if query in lot.prime_location_name.lower():
                available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
                results.append({
                    'id': lot.id,
                    'location': lot.prime_location_name,
                    'address': lot.address,
                    'available': available_spots
                })
    return render_template('search_results.html', results=results, username=session.get('username'))
