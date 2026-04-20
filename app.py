from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime, timedelta
import random
from functools import wraps
import math

app = Flask(__name__)
app.secret_key = 'bus_booking_secret_key'

# In-memory storage for Users and Bookings
USERS = {
    'testuser': {'password': 'password123', 'email': 'testuser@example.com'},
    'admin': {'password': 'admin123', 'email': 'admin@example.com'}
}
BOOKINGS = {
    'testuser': [],
    'admin': []
}

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


CITIES = ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata',
          'Jaipur', 'Goa', 'Udaipur', 'Agra', 'Kochi', 'Varanasi', 'Shimla', 'Manali',
          'Ahmedabad', 'Lucknow', 'Chandigarh']

AIRLINES = ['IndiGo', 'Air India', 'SpiceJet', 'Vistara', 'GoFirst', 'AirAsia India', 'Akasa Air']
FLIGHT_CLASSES = ['Economy', 'Premium Economy', 'Business', 'First Class']

HOTEL_NAMES = ['The Grand Palace', 'Hotel Radiance', 'Sunset Residency', 'Royal Orchid',
               'The Leela', 'Taj Gateway', 'ITC Fortune', 'Hyatt Regency',
               'Marriott Suites', 'Oberoi Towers', 'Park Inn', 'Sterling Holidays',
               'Lemon Tree', 'Treebo Trend', 'FabHotel Express']
HOTEL_AMENITIES_POOL = ['Swimming Pool', 'Gym', 'Free WiFi', 'Restaurant', 'Spa',
                        'Room Service', 'Parking', 'Bar/Lounge', 'Business Center',
                        'Laundry', 'Airport Shuttle', 'Pet Friendly', 'EV Charging']
ROOM_TYPES = ['Standard Room', 'Deluxe Room', 'Premium Suite', 'Executive Suite', 'Presidential Suite']

CAB_TYPES = ['Hatchback', 'Sedan', 'SUV', 'Luxury', 'Electric']
CAB_PROVIDERS = ['NexusCabs', 'RideSwift', 'UrbanGo', 'DriveEasy', 'EliteDrive', 'ZoomRide']

BUS_NAMES = ['Express Travels', 'Super Deluxe', 'Sleeper Comfort', 'Royal Cruiser',
             'Night Rider', 'City Connect', 'Pink City Travels', 'Green Line', 'Shree Travels']
BUS_TYPES = ['Volvo AC', 'Scania AC', 'Sleeper AC', 'Volvo AC Semi-Sleeper', 'Electric AC',
             'Non-AC Seater', 'Non-AC Sleeper']

TRAIN_NAMES = ['Vande Bharat Express', 'Rajdhani Express', 'Shatabdi Express',
               'Duronto Express', 'Superfast Express', 'Intercity Link', 'Garib Rath']
TRAIN_CLASSES = ['AC Chair Car', '1A AC First Class', 'Executive Chair Car',
                 '3A AC Three Tier', '2S Second Seating', 'Sleeper']

OFFERS = [
    {'id': 1, 'title': 'Flat 20% OFF on Bus Tickets', 'code': 'BUS20', 'desc': 'Use code BUS20 on all AC Volvo buses. Min booking ₹500.', 'type': 'bus', 'color': '#0ea5e9'},
    {'id': 2, 'title': 'Hotels at ₹999/night', 'code': 'STAY999', 'desc': 'Premium hotels starting at ₹999. Limited period deal!', 'type': 'hotel', 'color': '#8b5cf6'},
    {'id': 3, 'title': 'Flights from ₹1499', 'code': 'FLY1499', 'desc': 'Domestic flights starting at just ₹1499. Book now!', 'type': 'flight', 'color': '#f59e0b'},
    {'id': 4, 'title': 'Free Cab Upgrade', 'code': 'CABUP', 'desc': 'Book a Sedan and get upgraded to SUV for free!', 'type': 'cab', 'color': '#10b981'},
    {'id': 5, 'title': '₹500 Cashback on Trains', 'code': 'TRAIN500', 'desc': 'Get ₹500 cashback on AC class train bookings.', 'type': 'train', 'color': '#ef4444'},
    {'id': 6, 'title': 'Weekend Getaway Deals', 'code': 'WEEKEND', 'desc': 'Combo deals on hotels + cabs for weekend trips.', 'type': 'hotel', 'color': '#ec4899'},
]

TRENDING_DESTINATIONS = [
    {'city': 'Goa', 'tagline': 'Beaches & Nightlife', 'price_from': 1499, 'icon': 'fa-umbrella-beach'},
    {'city': 'Jaipur', 'tagline': 'The Pink City', 'price_from': 899, 'icon': 'fa-landmark'},
    {'city': 'Shimla', 'tagline': 'Hill Station Paradise', 'price_from': 1299, 'icon': 'fa-mountain'},
    {'city': 'Udaipur', 'tagline': 'City of Lakes', 'price_from': 1199, 'icon': 'fa-water'},
    {'city': 'Varanasi', 'tagline': 'Spiritual Capital', 'price_from': 999, 'icon': 'fa-om'},
    {'city': 'Kochi', 'tagline': 'Queen of the Sea', 'price_from': 1599, 'icon': 'fa-ship'},
]


# ─── Helper Functions ──────────────────────────────
def random_time(start_hour=0, end_hour=23):
    h = random.randint(start_hour, end_hour)
    m = random.choice([0, 15, 30, 45])
    return f"{h:02d}:{m:02d}"

def calculate_duration(dep_time, arr_time):
    dt1 = datetime.strptime(dep_time, "%H:%M")
    dt2 = datetime.strptime(arr_time, "%H:%M")
    if dt2 < dt1:
        dt2 += timedelta(days=1)
    duration_delta = dt2 - dt1
    hours, remainder = divmod(duration_delta.seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h {minutes}m"

def apply_filters(options, args):
    """Apply query-param filters + sorting to a list of options."""
    # AC filter
    ac_filter = args.get('ac')
    if ac_filter == 'ac':
        options = [o for o in options if 'AC' in o.get('type', '').upper() or 'ac' in o.get('type', '').lower()]
    elif ac_filter == 'nonac':
        options = [o for o in options if 'AC' not in o.get('type', '').upper()]

    # Price range
    price_min = args.get('price_min', type=int)
    price_max = args.get('price_max', type=int)
    if price_min is not None:
        options = [o for o in options if o['price'] >= price_min]
    if price_max is not None:
        options = [o for o in options if o['price'] <= price_max]

    # Rating
    rating_min = args.get('rating_min', type=float)
    if rating_min is not None:
        options = [o for o in options if o.get('rating', 0) >= rating_min]

    # Departure time slot
    dep_slot = args.get('dep_slot')
    if dep_slot and 'departure' in (options[0] if options else {}):
        slot_ranges = {
            'early_morning': (0, 6),
            'morning': (6, 12),
            'afternoon': (12, 18),
            'night': (18, 24)
        }
        if dep_slot in slot_ranges:
            lo, hi = slot_ranges[dep_slot]
            options = [o for o in options if lo <= int(o['departure'].split(':')[0]) < hi]

    # Sorting
    sort_by = args.get('sort', 'departure')
    if sort_by == 'price_low':
        options.sort(key=lambda x: x['price'])
    elif sort_by == 'price_high':
        options.sort(key=lambda x: x['price'], reverse=True)
    elif sort_by == 'duration':
        options.sort(key=lambda x: x.get('duration', ''))
    elif sort_by == 'rating':
        options.sort(key=lambda x: x.get('rating', 0), reverse=True)
    else:
        if options and 'departure' in options[0]:
            options.sort(key=lambda x: datetime.strptime(x['departure'], "%H:%M"))

    return options


# ─── Auth Routes ──────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if username in USERS:
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('register'))

        USERS[username] = {'email': email, 'password': password}
        BOOKINGS[username] = []

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in USERS and USERS[username]['password'] == password:
            session['user'] = username
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── Home ──────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', cities=CITIES, offers=OFFERS,
                           trending=TRENDING_DESTINATIONS)


# ─── API: Offers ──────────────────────────────
@app.route('/api/offers')
def api_offers():
    return jsonify(OFFERS)


# ─── Bus / Train Search ──────────────────────────────
@app.route('/search', methods=['POST'])
def search():
    from_city = request.form.get('from')
    to_city = request.form.get('to')
    date = request.form.get('date')
    transport_type = request.form.get('transport_type', 'bus')

    available_options = []
    num_results = random.randint(6, 12)

    for i in range(num_results):
        dep = random_time(5, 22)
        journey_hours = random.randint(2, 14)
        arr_dt = datetime.strptime(dep, "%H:%M") + timedelta(hours=journey_hours, minutes=random.choice([0, 15, 30]))
        arr = arr_dt.strftime("%H:%M")
        duration = calculate_duration(dep, arr)

        if transport_type == 'train':
            option = {
                'id': int(f"{random.randint(100, 999)}{i}"),
                'name': random.choice(TRAIN_NAMES),
                'type': random.choice(TRAIN_CLASSES),
                'from': from_city, 'to': to_city,
                'departure': dep, 'arrival': arr, 'duration': duration,
                'price': random.randint(500, 3500),
                'seats_available': random.randint(5, 150),
                'total_seats': random.randint(100, 500),
                'rating': round(random.uniform(3.8, 5.0), 1),
                'amenities': random.sample(['Food Included', 'WiFi', 'Charging Point', 'Clean Washrooms', 'Bedding', 'Pantry Car'], random.randint(2, 4))
            }
        elif transport_type == 'flight':
            base_price = random.randint(2000, 8000)
            option = {
                'id': int(f"{random.randint(100, 999)}{i}"),
                'name': random.choice(AIRLINES),
                'type': random.choice(FLIGHT_CLASSES[:2]),  # mostly economy/premium
                'flight_number': f"6E-{random.randint(100,999)}",
                'from': from_city, 'to': to_city,
                'departure': random_time(5, 22),
                'arrival': '',
                'duration': f"{random.randint(1,4)}h {random.choice([0,15,30,45])}m",
                'price': base_price,
                'seats_available': random.randint(5, 80),
                'total_seats': random.randint(150, 300),
                'rating': round(random.uniform(3.5, 4.9), 1),
                'amenities': random.sample(['Meal Included', 'WiFi', 'USB Charging', 'Entertainment', 'Extra Legroom', 'Priority Boarding'], random.randint(2, 4))
            }
            # calculate arrival from duration
            dep_dt = datetime.strptime(option['departure'], "%H:%M")
            dur_parts = option['duration'].replace('h', '').replace('m', '').split()
            arr_dt2 = dep_dt + timedelta(hours=int(dur_parts[0]), minutes=int(dur_parts[1]))
            option['arrival'] = arr_dt2.strftime("%H:%M")
        else:
            option = {
                'id': int(f"{random.randint(10, 99)}{i}"),
                'name': random.choice(BUS_NAMES),
                'type': random.choice(BUS_TYPES),
                'from': from_city, 'to': to_city,
                'departure': dep, 'arrival': arr, 'duration': duration,
                'price': random.randint(400, 2500),
                'seats_available': random.randint(2, 35),
                'total_seats': random.randint(30, 45),
                'rating': round(random.uniform(3.2, 4.9), 1),
                'amenities': random.sample(['WiFi', 'Charging Point', 'Water Bottle', 'Blanket', 'Snacks', 'Entertainment', 'Reading Light'], random.randint(2, 5))
            }
        available_options.append(option)

    # Apply filters
    available_options = apply_filters(available_options, request.args)

    session['dynamic_routes'] = {str(opt['id']): opt for opt in available_options}

    return render_template('search_results.html',
                           options=available_options,
                           from_city=from_city, to_city=to_city,
                           date=date, transport_type=transport_type)


# ─── Hotel Search ──────────────────────────────
@app.route('/search_hotels', methods=['POST'])
def search_hotels():
    destination = request.form.get('destination')
    checkin = request.form.get('checkin')
    checkout = request.form.get('checkout')
    rooms = request.form.get('rooms', 1, type=int)
    guests = request.form.get('guests', 2, type=int)

    hotels = []
    num_results = random.randint(6, 12)

    for i in range(num_results):
        stars = random.choice([3, 3, 4, 4, 4, 5, 5])
        base_price = {3: random.randint(1200, 3000), 4: random.randint(3000, 7000), 5: random.randint(6000, 15000)}[stars]
        hotel = {
            'id': random.randint(1000, 9999),
            'name': random.choice(HOTEL_NAMES),
            'stars': stars,
            'destination': destination,
            'price_per_night': base_price,
            'total_price': base_price * max(1, rooms),
            'rating': round(random.uniform(max(3.0, stars - 0.5), min(5.0, stars + 0.3)), 1),
            'reviews_count': random.randint(50, 2000),
            'distance_km': round(random.uniform(0.5, 15.0), 1),
            'amenities': random.sample(HOTEL_AMENITIES_POOL, random.randint(4, 8)),
            'room_types': random.sample(ROOM_TYPES, random.randint(2, 4)),
            'checkin': checkin,
            'checkout': checkout,
            'rooms': rooms,
            'guests': guests,
            'image_index': random.randint(1, 6),
            'cancellation': random.choice(['Free cancellation', 'Non-refundable', 'Partial refund']),
            'breakfast': random.choice([True, False]),
        }
        hotels.append(hotel)

    # Sort by rating default
    hotels.sort(key=lambda x: x['rating'], reverse=True)

    session['hotels_data'] = {str(h['id']): h for h in hotels}

    return render_template('hotels_results.html',
                           hotels=hotels, destination=destination,
                           checkin=checkin, checkout=checkout,
                           rooms=rooms, guests=guests)


# ─── Hotel Booking ──────────────────────────────
@app.route('/book_hotel/<int:hotel_id>')
@login_required
def book_hotel(hotel_id):
    hotel = session.get('hotels_data', {}).get(str(hotel_id))
    if not hotel:
        flash('Hotel not found. Please search again.', 'warning')
        return redirect(url_for('index'))

    room_type = request.args.get('room_type', hotel['room_types'][0])
    return render_template('hotel_booking.html', hotel=hotel, room_type=room_type)


@app.route('/confirm_hotel', methods=['POST'])
@login_required
def confirm_hotel():
    hotel_id = request.form.get('hotel_id')
    room_type = request.form.get('room_type')
    guest_name = request.form.get('guest_name', session.get('user'))
    payment_method = request.form.get('payment_method', 'UPI')

    hotel = session.get('hotels_data', {}).get(str(hotel_id))
    if not hotel:
        return redirect(url_for('index'))

    booking = {
        'booking_id': f"HT{random.randint(100000, 999999)}",
        'booking_type': 'hotel',
        'hotel': hotel,
        'room_type': room_type,
        'guest_name': guest_name,
        'total_price': hotel['total_price'],
        'payment_method': payment_method,
        'status': 'Confirmed',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    username = session.get('user')
    if username and username in BOOKINGS:
        BOOKINGS[username].append(booking)

    return render_template('payment_success.html', booking=booking, payment_method=payment_method)


# ─── Cab Search ──────────────────────────────
@app.route('/search_cabs', methods=['POST'])
def search_cabs():
    pickup = request.form.get('pickup')
    dropoff = request.form.get('dropoff')
    date = request.form.get('date')
    cab_type_filter = request.form.get('cab_type', 'all')

    cabs = []
    num_results = random.randint(5, 10)

    for i in range(num_results):
        cab_type = random.choice(CAB_TYPES) if cab_type_filter == 'all' else cab_type_filter
        distance = round(random.uniform(5, 300), 1)
        rate_per_km = {'Hatchback': 8, 'Sedan': 12, 'SUV': 16, 'Luxury': 25, 'Electric': 14}[cab_type]
        base_fare = max(150, int(distance * rate_per_km))

        cab = {
            'id': random.randint(1000, 9999),
            'provider': random.choice(CAB_PROVIDERS),
            'cab_type': cab_type,
            'pickup': pickup,
            'dropoff': dropoff,
            'distance_km': distance,
            'estimated_time': f"{int(distance / random.randint(30, 60))}h {random.choice([0, 15, 30, 45])}m",
            'fare': base_fare,
            'rating': round(random.uniform(3.8, 4.9), 1),
            'driver_name': random.choice(['Rajesh K.', 'Suresh M.', 'Amit P.', 'Vikram S.', 'Deepak R.', 'Arjun N.']),
            'car_model': {
                'Hatchback': random.choice(['Maruti Swift', 'Hyundai i20', 'Tata Altroz']),
                'Sedan': random.choice(['Honda City', 'Maruti Ciaz', 'Hyundai Verna']),
                'SUV': random.choice(['Toyota Innova', 'Mahindra XUV700', 'Tata Harrier']),
                'Luxury': random.choice(['Mercedes E-Class', 'BMW 5 Series', 'Audi A6']),
                'Electric': random.choice(['Tata Nexon EV', 'MG ZS EV', 'Hyundai Kona EV'])
            }[cab_type],
            'amenities': random.sample(['AC', 'Music System', 'Phone Charger', 'Water Bottle', 'GPS Tracking', 'Child Seat'], random.randint(2, 4)),
            'date': date
        }
        cabs.append(cab)

    cabs.sort(key=lambda x: x['fare'])
    session['cabs_data'] = {str(c['id']): c for c in cabs}

    return render_template('cabs_results.html', cabs=cabs, pickup=pickup, dropoff=dropoff, date=date)


# ─── Cab Booking ──────────────────────────────
@app.route('/book_cab/<int:cab_id>')
@login_required
def book_cab(cab_id):
    cab = session.get('cabs_data', {}).get(str(cab_id))
    if not cab:
        flash('Cab not found. Please search again.', 'warning')
        return redirect(url_for('index'))
    return render_template('booking_confirmation.html',
                           transport=cab, seats=[], total_price=cab['fare'],
                           transport_type='cab', booking_type='cab')


@app.route('/confirm_cab', methods=['POST'])
@login_required
def confirm_cab():
    cab_id = request.form.get('cab_id')
    payment_method = request.form.get('payment_method', 'UPI')

    cab = session.get('cabs_data', {}).get(str(cab_id))
    if not cab:
        return redirect(url_for('index'))

    booking = {
        'booking_id': f"CB{random.randint(100000, 999999)}",
        'booking_type': 'cab',
        'transport': cab,
        'transport_type': 'cab',
        'total_price': cab['fare'],
        'payment_method': payment_method,
        'status': 'Confirmed',
        'seats': [],
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    username = session.get('user')
    if username and username in BOOKINGS:
        BOOKINGS[username].append(booking)

    return render_template('payment_success.html', booking=booking, payment_method=payment_method)


# ─── Seat Selection (Bus / Train / Flight) ──────────────────────────────
@app.route('/select_seats/<transport_type>/<int:id>')
@login_required
def select_seats(transport_type, id):
    transport = session.get('dynamic_routes', {}).get(str(id))
    if not transport:
        return redirect(url_for('index'))

    seats = []

    if transport_type == 'flight':
        rows = 20
        seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
        for row in range(1, rows + 1):
            for i, letter in enumerate(seat_letters):
                seat_id = f'{row}{letter}'
                is_booked = random.choice([True, False, False, False])
                price_mult = 1.0
                if row <= 3:
                    price_mult = 2.5  # First class
                elif row <= 8:
                    price_mult = 1.5  # Business
                seats.append({
                    'id': seat_id, 'row': row, 'number': i + 1,
                    'is_booked': is_booked,
                    'price': int(transport['price'] * price_mult),
                    'seat_class': 'First' if row <= 3 else ('Business' if row <= 8 else 'Economy')
                })
    elif transport_type == 'train':
        rows = 12
        seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
        for row in range(1, rows + 1):
            for i, letter in enumerate(seat_letters):
                seat_id = f'{row}{letter}'
                is_booked = random.choice([True, False, False])
                seats.append({
                    'id': seat_id, 'row': row, 'number': i + 1,
                    'is_booked': is_booked,
                    'price': transport['price']
                })
    else:
        rows = 10
        seat_letters = ['A', 'B', 'C', 'D']
        for row in range(1, rows + 1):
            for i, letter in enumerate(seat_letters):
                seat_id = f'{row}{letter}'
                is_booked = random.choice([True, False, False, False])
                seats.append({
                    'id': seat_id, 'row': row, 'number': i + 1,
                    'is_booked': is_booked,
                    'price': transport['price']
                })

    return render_template('seat_selection.html', transport=transport, seats=seats, transport_type=transport_type)


# ─── Booking Confirmation ──────────────────────────────
@app.route('/booking', methods=['POST'])
@login_required
def booking():
    transport_id = request.form.get('transport_id')
    transport_type = request.form.get('transport_type', 'bus')
    selected_seats = request.form.getlist('seats')

    transport = session.get('dynamic_routes', {}).get(str(transport_id))
    if not transport or not selected_seats:
        return redirect(url_for('index'))

    total_price = len(selected_seats) * transport['price']

    session['booking'] = {
        'transport': transport,
        'transport_type': transport_type,
        'booking_type': transport_type,
        'seats': selected_seats,
        'total_price': total_price,
        'booking_id': f'{"FL" if transport_type == "flight" else "TR" if transport_type == "train" else "RB"}{random.randint(100000, 999999)}',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return render_template('booking_confirmation.html',
                           transport=transport,
                           seats=selected_seats,
                           total_price=total_price,
                           transport_type=transport_type)


# ─── Payment ──────────────────────────────
@app.route('/payment', methods=['POST'])
@login_required
def payment():
    if 'booking' not in session:
        return redirect(url_for('index'))

    booking = session['booking']
    payment_method = request.form.get('payment_method')

    username = session.get('user')
    if username and username in BOOKINGS:
        history_entry = dict(booking)
        history_entry['payment_method'] = payment_method
        history_entry['status'] = 'Confirmed'
        BOOKINGS[username].append(history_entry)

    session.pop('booking', None)
    return render_template('payment_success.html', booking=booking, payment_method=payment_method)


# ─── History ──────────────────────────────
@app.route('/history')
@login_required
def history():
    username = session.get('user')
    user_bookings = list(BOOKINGS.get(username, []))
    user_bookings.reverse()
    return render_template('history.html', bookings=user_bookings)


if __name__ == '__main__':
    app.run(debug=True)
