from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import json
import os
import uuid
from datetime import datetime
from database import load_state, save_state, StorageConfigurationError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or ('local-hotel77-secret' if os.environ.get('FLASK_ENV') != 'production' else None)
if not app.secret_key:
    raise RuntimeError('SECRET_KEY must be set in production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60 * 60 * 24 * 30
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('VERCEL') or os.environ.get('FLASK_ENV') == 'production')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ==================== DATA LAYER ====================
def get_data():
    data = load_state(get_default_data)
    # Add fields introduced by later versions without replacing administrator edits.
    defaults = get_default_data()
    for key, value in defaults.get('settings', {}).items():
        data.setdefault('settings', {}).setdefault(key, value)
    for key in ('gallery', 'testimonials', 'pages', 'rooms', 'messages', 'menu'):
        data.setdefault(key, defaults.get(key, []))
    for image in data['gallery']:
        image.setdefault('visible', True)
        image.setdefault('featured', False)
    return data

def save_data(data):
    save_state(data)

def get_default_data():
    configured_admin_password = os.environ.get('ADMIN_PASSWORD')
    if os.environ.get('FLASK_ENV') == 'production' and not configured_admin_password:
        raise RuntimeError('ADMIN_PASSWORD must be set before the first production seed')
    return {
        "settings": {
            "hotel_name": "Hotel 77",
            "tagline": "Comfort, Hospitality & Convenience in Shreegaun, Jakhera, Lamahi",
            "logo_url": "/static/uploads/logo.png",
            "hero_image_url": "/static/uploads/exterior-1.png",
            "primary_phone": "9847871687",
            "secondary_phone": "9857841687",
            "whatsapp_number": "9847871687",
            "whatsapp_prefilled_text": "Hello, I am interested in booking a stay at Hotel 77.",
            "email_address": "hotel77@gmail.com",
            "address": "Shreegaun, Jakhera, Lamahi, Dang, Nepal",
            "google_maps_embed_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3527.2722631552697!2d82.5657133753295!3d27.862905676093725!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3997a36fb3930c71%3A0x49ac19d8da197d81!2sHotel%2077!5e0!3m2!1sen!2snp!4v1781294849874!5m2!1sen!2snp",
            "seo_title": "Hotel 77 | Hotel in Lamahi, Dang, Nepal",
            "seo_description": "Hotel 77 is a comfortable hotel in Lamahi, Dang, Nepal, offering clean rooms, suites, Wi-Fi, room service, and friendly hospitality.",
            "footer_content": "© 2026 Hotel 77. Shreegaun, Jakhera, Lamahi, Dang, Nepal.",
            "amenities": [
                {"icon": "clock", "title": "24/7 Room Service", "desc": "Round-the-clock room service for your comfort."},
                {"icon": "wifi", "title": "Good WiFi", "desc": "High-speed wireless internet throughout the property."},
                {"icon": "home", "title": "Peaceful Environment", "desc": "Tranquil atmosphere for a relaxing stay."},
                {"icon": "utensils", "title": "Good Food", "desc": "Quality meals and dining options available."}
            ],
            "homepage_gallery_ids": None,
            "homepage_room_ids": None,
            "homepage_gallery_layout": "masonry",
            "maintenance_mode": False
        },
        "rooms": [
            {"id": "room-110", "name": "Suite - Room 110", "short_description": "Spacious family suite for comfort and relaxation.", "full_description": "Room 110 offers generous space for families with one double and one single bed.", "capacity_guests": 3, "capacity_beds": 2, "amenities": ["Air Conditioning", "Free Wi-Fi", "Double Bed", "Single Bed", "Room Service", "Attached Bathroom", "Hot & Cold Shower"], "images": ["/static/uploads/110.png"], "featured": True, "enabled": True, "category": "Suite"},
            {"id": "room-107", "name": "Suite - Room 107", "short_description": "Spacious suite with cozy seating area.", "full_description": "Room 107 features a double and single bed with seating area, dining table, and chairs.", "capacity_guests": 3, "capacity_beds": 2, "amenities": ["Air Conditioning", "Free Wi-Fi", "Double Bed", "Single Bed", "Seating Area", "Room Service"], "images": ["/static/uploads/107.png"], "featured": True, "enabled": True, "category": "Suite"},
            {"id": "room-105", "name": "Deluxe Room - Room 105", "short_description": "Comfortable deluxe room with king-size bed.", "full_description": "Room 105 features a king-size bed, seating area with table and chairs.", "capacity_guests": 2, "capacity_beds": 1, "amenities": ["Air Conditioning", "Free Wi-Fi", "King Bed", "Seating Area", "Room Service"], "images": ["/static/uploads/105.png"], "featured": True, "enabled": True, "category": "Deluxe Room"},
            {"id": "room-101", "name": "Deluxe Room - Room 101", "short_description": "Modern deluxe room offering comfort.", "full_description": "Room 101 has a king-size bed, AC, Wi-Fi, and quality furnishings.", "capacity_guests": 2, "capacity_beds": 1, "amenities": ["Air Conditioning", "Free Wi-Fi", "King Bed", "Room Service"], "images": ["/static/uploads/101.png"], "featured": False, "enabled": True, "category": "Deluxe Room"},
            {"id": "room-104", "name": "Standard Room - Room 104", "short_description": "Affordable comfort for a pleasant stay.", "full_description": "Room 104 features a king-size bed, ceiling fan, Wi-Fi, and clean bathroom.", "capacity_guests": 2, "capacity_beds": 1, "amenities": ["Free Wi-Fi", "King Bed", "Ceiling Fan", "Room Service"], "images": ["/static/uploads/104.png"], "featured": False, "enabled": True, "category": "Standard Room"},
            {"id": "room-103", "name": "Standard Room - Room 103", "short_description": "Simple, clean, and comfortable.", "full_description": "Room 103 offers a king-size bed, Wi-Fi, and ceiling fan.", "capacity_guests": 2, "capacity_beds": 1, "amenities": ["Free Wi-Fi", "King Bed", "Ceiling Fan", "Room Service"], "images": ["/static/uploads/103.png"], "featured": False, "enabled": True, "category": "Standard Room"},
            {"id": "room-102", "name": "Standard Room - Room 102", "short_description": "Budget-friendly comfort.", "full_description": "Room 102 provides a king-size bed, Wi-Fi, ceiling fan, and clean bathroom.", "capacity_guests": 2, "capacity_beds": 1, "amenities": ["Free Wi-Fi", "King Bed", "Ceiling Fan", "Room Service"], "images": ["/static/uploads/102.png"], "featured": False, "enabled": True, "category": "Standard Room"}
        ],
        "gallery": [
            {"id": "g-ext-1", "url": "/static/uploads/exterior-1.png", "category": "Exterior", "caption": "Hotel 77 Front View"},
            {"id": "g-ext-2", "url": "/static/uploads/exterior-2.png", "category": "Exterior", "caption": "Hotel 77 Entrance & Surroundings"},
            {"id": "g-int-1", "url": "/static/uploads/interior-1.png", "category": "Interior", "caption": "Reception & Lounge Area"},
            {"id": "g-int-2", "url": "/static/uploads/interior-2.png", "category": "Interior", "caption": "Interior Hallway"},
            {"id": "g-int-3", "url": "/static/uploads/interior-3.png", "category": "Interior", "caption": "Common Area"},
            {"id": "g-int-4", "url": "/static/uploads/interior-4.png", "category": "Interior", "caption": "Hotel Interior Design"},
            {"id": "g-room-110", "url": "/static/uploads/110.png", "category": "Rooms", "caption": "Suite 110 - Family Suite"},
            {"id": "g-room-107", "url": "/static/uploads/107.png", "category": "Rooms", "caption": "Suite 107"},
            {"id": "g-room-105", "url": "/static/uploads/105.png", "category": "Rooms", "caption": "Deluxe Room 105"},
            {"id": "g-room-101", "url": "/static/uploads/101.png", "category": "Rooms", "caption": "Deluxe Room 101"},
            {"id": "g-room-102", "url": "/static/uploads/102.png", "category": "Rooms", "caption": "Standard Room 102"},
            {"id": "g-room-103", "url": "/static/uploads/103.png", "category": "Rooms", "caption": "Standard Room 103"},
            {"id": "g-room-104", "url": "/static/uploads/104.png", "category": "Rooms", "caption": "Standard Room 104"}
        ],
        "testimonials": [
            {"id": "t1", "author_name": "Sita Sharma", "rating": 5, "content": "Hotel 77 is the best place to stay in Lamahi. Clean rooms, friendly staff, and great food.", "source": "Google Review", "featured": True},
            {"id": "t2", "author_name": "Rajesh Hamal", "rating": 5, "content": "Excellent service and very comfortable rooms. Perfect location for travelers.", "source": "Direct Guest", "featured": True},
            {"id": "t3", "author_name": "Anita Gurung", "rating": 4, "content": "Very clean and well-maintained. Great value for money.", "source": "Booking.com", "featured": True}
        ],
        "messages": [],
        "menu": [
            {"id": "mn1", "label": "Home", "path": "/", "order": 1},
            {"id": "mn2", "label": "Rooms & Suites", "path": "/rooms", "order": 2},
            {"id": "mn3", "label": "Gallery", "path": "/gallery", "order": 3},
            {"id": "mn4", "label": "About", "path": "/page/about", "order": 4},
            {"id": "mn5", "label": "Contact", "path": "/contact", "order": 5}
        ],
        "pages": [
            {"id": "about", "slug": "about", "title": "The Story of Hotel 77", "content": "### Comfort & Hospitality in Shreegaun, Jakhera, Lamahi\n\nLocated in the peaceful surroundings of Shreegaun, Jakhera, Lamahi, Dang, Nepal, **Hotel 77** offers a comfortable and welcoming stay for travelers, families, and business guests.\n\n### Our Philosophy\nWe believe great hospitality begins with genuine care. We provide clean, comfortable accommodations and friendly service.\n\n### Why Choose Hotel 77?\n* Comfortable Standard, Deluxe, and Family Suite rooms\n* Free High-Speed Wi-Fi\n* Daily housekeeping\n* Peaceful environment\n* Ample parking\n* Excellent value for money", "last_updated": "2026-07-18"}
        ],
        "admin_password": generate_password_hash(configured_admin_password or 'admin77')
    }

# ==================== AUTH ====================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ==================== STATIC FILES SETUP ====================
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== PUBLIC ROUTES ====================
@app.route('/')
def home():
    data = get_data()
    settings = data['settings']
    gallery = data['gallery']
    rooms = [room for room in data['rooms'] if room.get('enabled', True)]
    gallery_ids = settings.get('homepage_gallery_ids')
    room_ids = settings.get('homepage_room_ids')
    gallery = [item for item in gallery if item.get('visible', True)]
    featured_gallery = [item for item in gallery if item.get('featured')]
    if featured_gallery:
        by_id = {item['id']: item for item in featured_gallery}
        gallery = ([by_id[item_id] for item_id in gallery_ids if item_id in by_id]
                   if gallery_ids else featured_gallery)
    elif gallery_ids is not None:
        by_id = {item['id']: item for item in gallery}
        gallery = [by_id[item_id] for item_id in gallery_ids if item_id in by_id]
    else:
        gallery = gallery
    if room_ids is not None:
        by_id = {room['id']: room for room in rooms}
        rooms = [by_id[item_id] for item_id in room_ids if item_id in by_id]
    else:
        rooms = [room for room in rooms if room.get('featured')]
    return render_template('index.html', data=data, homepage_gallery=gallery, homepage_rooms=rooms)

@app.route('/rooms')
def rooms_page():
    data = get_data()
    return render_template('rooms.html', data=data)

@app.route('/gallery')
def gallery_page():
    data = get_data()
    data['gallery'] = [item for item in data['gallery'] if item.get('visible', True)]
    return render_template('gallery.html', data=data)

@app.route('/contact')
def contact_page():
    data = get_data()
    return render_template('contact.html', data=data)

@app.route('/robots.txt')
def robots_txt():
    return ("User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\n\n"
            "Sitemap: https://www.hotel77.com.np/sitemap.xml\n", 200,
            {'Content-Type': 'text/plain; charset=utf-8'})

@app.route('/sitemap.xml')
def sitemap_xml():
    data = get_data()
    urls = ['/', '/rooms', '/gallery', '/contact']
    urls.extend('/page/' + page['slug'] for page in data['pages'])
    body = '\n'.join(f'  <url><loc>https://www.hotel77.com.np{url}</loc></url>' for url in urls)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>',
            200, {'Content-Type': 'application/xml; charset=utf-8'})

@app.route('/page/<slug>')
def page_view(slug):
    data = get_data()
    page = next((p for p in data['pages'] if p['slug'] == slug), None)
    if not page:
        return render_template('404.html', data=data), 404
    return render_template('page.html', data=data, page=page)

# API - public data
@app.route('/api/public/data')
def api_public_data():
    data = get_data()
    return jsonify({
        'settings': data['settings'],
        'rooms': [r for r in data['rooms'] if r['enabled']],
        'gallery': [item for item in data['gallery'] if item.get('visible', True)],
        'testimonials': data['testimonials'],
        'pages': data['pages'],
        'menu': sorted(data['menu'], key=lambda x: x['order'])
    })

@app.route('/api/public/contact', methods=['POST'])
def api_contact():
    body = request.json
    if not body or not body.get('name') or not body.get('email') or not body.get('message'):
        return jsonify({'error': 'Name, email, and message are required.'}), 400
    data = get_data()
    msg = {
        'id': 'msg-' + str(uuid.uuid4()),
        'name': body['name'],
        'email': body['email'],
        'phone': body.get('phone', ''),
        'message': body['message'],
        'created_at': datetime.now().isoformat(),
        'read': False,
        'notes': ''
    }
    data['messages'].insert(0, msg)
    save_data(data)
    return jsonify({'success': True, 'message': 'Thank you! Your message has been received.'})

# ==================== ADMIN ROUTES ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        data = get_data()
        if check_password_hash(data.get('admin_password', ''), password):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error='Invalid password')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
def admin_change_password():
    error = None
    success = None
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        data = get_data()
        if not check_password_hash(data.get('admin_password', ''), current):
            error = 'Current password is incorrect.'
        elif len(new_password) < 10:
            error = 'New password must be at least 10 characters.'
        elif new_password != confirm:
            error = 'New passwords do not match.'
        else:
            data['admin_password'] = generate_password_hash(new_password)
            save_data(data)
            success = 'Password changed successfully.'
    return render_template('admin_change_password.html', data=get_data(), error=error, success=success)

@app.route('/admin')
@login_required
def admin_dashboard():
    data = get_data()
    return render_template('admin_dashboard.html', data=data)

@app.route('/admin/settings')
@login_required
def admin_settings():
    return render_template('admin_settings.html', data=get_data())

@app.route('/admin/homepage')
@login_required
def admin_homepage():
    return render_template('admin_homepage.html', data=get_data())

@app.route('/admin/homepage/update', methods=['POST'])
@login_required
def admin_update_homepage():
    data = get_data()

    def ordered_ids(items, prefix):
        positions = []
        for item in items:
            value = request.form.get(f'{prefix}{item["id"]}', '').strip()
            if value.isdigit() and int(value) > 0:
                positions.append((int(value), item['id']))
        return [item_id for _, item_id in sorted(positions, key=lambda pair: (pair[0], pair[1]))]

    data['settings']['homepage_gallery_ids'] = ordered_ids(data['gallery'], 'gallery_position_')
    data['settings']['homepage_room_ids'] = ordered_ids(data['rooms'], 'room_position_')
    data['settings']['homepage_gallery_layout'] = request.form.get('gallery_layout', 'masonry')
    save_data(data)
    return redirect(url_for('admin_homepage'))

@app.route('/admin/pages')
@login_required
def admin_pages():
    return render_template('admin_pages.html', data=get_data())

@app.route('/admin/pages/edit/<page_id>')
@login_required
def admin_edit_page(page_id):
    data = get_data(); page = next((p for p in data['pages'] if p['id'] == page_id), None)
    return render_template('admin_page_edit.html', data=data, page=page) if page else redirect(url_for('admin_pages'))

@app.route('/admin/rooms')
@login_required
def admin_rooms():
    return render_template('admin_rooms.html', data=get_data())

@app.route('/admin/rooms/edit/<room_id>')
@login_required
def admin_edit_room(room_id):
    data = get_data()
    room = next((item for item in data['rooms'] if item['id'] == room_id), None)
    if not room:
        return redirect(url_for('admin_rooms'))
    return render_template('admin_room_edit.html', data=data, room=room)

@app.route('/admin/gallery')
@login_required
def admin_gallery():
    return render_template('admin_gallery.html', data=get_data())

@app.route('/admin/gallery/edit/<image_id>')
@login_required
def admin_edit_gallery(image_id):
    data = get_data(); image = next((item for item in data['gallery'] if item['id'] == image_id), None)
    return render_template('admin_gallery_edit.html', data=data, item=image) if image else redirect(url_for('admin_gallery'))

@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    return render_template('admin_testimonials.html', data=get_data())

@app.route('/admin/testimonials/edit/<testimonial_id>')
@login_required
def admin_edit_testimonial(testimonial_id):
    data = get_data(); item = next((x for x in data['testimonials'] if x['id'] == testimonial_id), None)
    return render_template('admin_testimonial_edit.html', data=data, item=item) if item else redirect(url_for('admin_testimonials'))

@app.route('/admin/testimonials/add', methods=['GET', 'POST'])
@login_required
def admin_add_testimonial():
    if request.method == 'POST':
        data = get_data()
        try:
            rating = max(1, min(5, int(request.form.get('rating', 5))))
        except ValueError:
            rating = 5
        data['testimonials'].append({
            'id': 't-' + str(uuid.uuid4())[:8],
            'author_name': request.form.get('author_name', '').strip(),
            'content': request.form.get('content', '').strip(),
            'source': request.form.get('source', '').strip(),
            'rating': rating,
            'featured': request.form.get('featured') == 'on'
        })
        save_data(data)
        return redirect(url_for('admin_testimonials'))
    return render_template('admin_testimonial_edit.html', data=get_data(), item=None)

@app.route('/admin/update-settings', methods=['POST'])
@login_required
def admin_update_settings():
    data = get_data()
    for key in request.form:
        if key in data['settings']:
            if key == 'amenities':
                try:
                    parsed = json.loads(request.form[key])
                    if isinstance(parsed, list):
                        data['settings'][key] = parsed
                except json.JSONDecodeError:
                    pass
            else:
                data['settings'][key] = request.form[key]
    if request.form.get('maintenance_mode'):
        data['settings']['maintenance_mode'] = True
    else:
        data['settings']['maintenance_mode'] = False
    save_data(data)
    return redirect(url_for('admin_settings'))

@app.route('/admin/pages/update/<page_id>', methods=['POST'])
@login_required
def admin_update_page(page_id):
    data = get_data()
    page = next((p for p in data['pages'] if p['id'] == page_id), None)
    if page:
        page['title'] = request.form.get('title', '').strip()
        page['slug'] = request.form.get('slug', '').strip().lower().replace(' ', '-')
        page['content'] = request.form.get('content', '')
        page['last_updated'] = datetime.now().date().isoformat()
        save_data(data)
    return redirect(url_for('admin_pages'))

@app.route('/admin/gallery/update/<image_id>', methods=['POST'])
@login_required
def admin_update_gallery(image_id):
    data = get_data()
    image = next((item for item in data['gallery'] if item['id'] == image_id), None)
    if image:
        image_url = request.form.get('image_url', '').strip()
        if image_url:
            image['url'] = image_url
        image['caption'] = request.form.get('caption', '')
        image['title'] = request.form.get('title', image.get('title', image.get('caption', '')))
        image['alt_text'] = request.form.get('alt_text', image.get('alt_text', image.get('caption', 'Hotel 77')))
        image['category'] = request.form.get('category', 'Other')
        image['visible'] = request.form.get('visible') == 'on'
        image['featured'] = request.form.get('featured') == 'on'
        save_data(data)
    return redirect(url_for('admin_gallery'))

@app.route('/admin/gallery/delete/<image_id>', methods=['POST'])
@login_required
def admin_delete_gallery(image_id):
    data = get_data()
    data['gallery'] = [item for item in data['gallery'] if item['id'] != image_id]
    save_data(data)
    return redirect(url_for('admin_gallery'))

@app.route('/admin/testimonials/update/<testimonial_id>', methods=['POST'])
@login_required
def admin_update_testimonial(testimonial_id):
    data = get_data()
    testimonial = next((item for item in data['testimonials'] if item['id'] == testimonial_id), None)
    if testimonial:
        testimonial['author_name'] = request.form.get('author_name', '')
        testimonial['content'] = request.form.get('content', '')
        testimonial['source'] = request.form.get('source', '')
        try:
            testimonial['rating'] = max(1, min(5, int(request.form.get('rating', 5))))
        except ValueError:
            testimonial['rating'] = 5
        testimonial['featured'] = request.form.get('featured') == 'on'
        save_data(data)
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/testimonials/delete/<testimonial_id>', methods=['POST'])
@login_required
def admin_delete_testimonial(testimonial_id):
    data = get_data()
    data['testimonials'] = [item for item in data['testimonials'] if item['id'] != testimonial_id]
    save_data(data)
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/rooms/update/<room_id>', methods=['POST'])
@login_required
def admin_update_room(room_id):
    data = get_data()
    room = next((item for item in data['rooms'] if item['id'] == room_id), None)
    if room:
        room['name'] = request.form.get('name', room['name'])
        room['category'] = request.form.get('category', room['category'])
        room['short_description'] = request.form.get('short_description', '')
        room['full_description'] = request.form.get('full_description', '')
        try:
            room['capacity_guests'] = max(1, int(request.form.get('capacity_guests', 2)))
            room['capacity_beds'] = max(1, int(request.form.get('capacity_beds', 1)))
        except ValueError:
            room['capacity_guests'], room['capacity_beds'] = 2, 1
        room['amenities'] = [a.strip() for a in request.form.get('amenities', '').split(',') if a.strip()]
        image_url = request.form.get('image_url', '').strip()
        if image_url:
            room['images'] = [image_url]
        room['featured'] = request.form.get('featured') == 'on'
        room['enabled'] = request.form.get('enabled') == 'on'
        save_data(data)
    return redirect(url_for('admin_rooms'))

@app.route('/admin/upload', methods=['POST'])
@login_required
def admin_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': 'Invalid file type'}), 400
    filename = 'upload-' + str(uuid.uuid4()) + '.' + ext
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    original_name = secure_filename(file.filename).lower()
    room_numbers = {'101', '102', '103', '104', '105', '107', '110'}
    suggested_room = next((number for number in room_numbers if number in original_name), None)
    suggested_category = 'Rooms' if suggested_room else ('Interior' if 'interior' in original_name else 'Exterior' if 'exterior' in original_name else 'Other')
    return jsonify({
        'success': True,
        'url': '/static/uploads/' + filename,
        'review_required': True,
        'suggested_room': suggested_room,
        'suggested_category': suggested_category,
        'message': 'Review the suggested association before saving it to the gallery.'
    })

@app.route('/admin/rooms/add', methods=['POST'])
@login_required
def admin_add_room():
    data = get_data()
    room = {
        'id': 'room-' + str(uuid.uuid4())[:8],
        'name': request.form['name'],
        'short_description': request.form.get('short_description', ''),
        'full_description': request.form.get('full_description', ''),
        'capacity_guests': int(request.form.get('capacity_guests', 2)),
        'capacity_beds': int(request.form.get('capacity_beds', 1)),
        'amenities': [a.strip() for a in request.form.get('amenities', '').split(',') if a.strip()],
        'images': [request.form.get('image_url', '/static/uploads/logo.png')],
        'featured': 'featured' in request.form,
        'enabled': True,
        'category': request.form.get('category', 'Standard Room')
    }
    data['rooms'].append(room)
    save_data(data)
    return redirect(url_for('admin_rooms'))

@app.route('/admin/rooms/delete/<room_id>', methods=['POST'])
@login_required
def admin_delete_room(room_id):
    data = get_data()
    data['rooms'] = [r for r in data['rooms'] if r['id'] != room_id]
    save_data(data)
    return redirect(url_for('admin_rooms'))

@app.route('/admin/messages')
@login_required
def admin_messages():
    data = get_data()
    return render_template('admin_messages.html', data=data)

@app.route('/admin/messages/delete/<msg_id>', methods=['POST'])
@login_required
def admin_delete_message(msg_id):
    data = get_data()
    data['messages'] = [m for m in data['messages'] if m['id'] != msg_id]
    save_data(data)
    return redirect(url_for('admin_messages'))

# ==================== ERROR HANDLER ====================
@app.errorhandler(404)
def not_found(e):
    data = get_data()
    return render_template('404.html', data=data), 404

@app.errorhandler(StorageConfigurationError)
def storage_configuration_error(error):
    return (
        '<!doctype html><html><head><title>Storage setup required</title>'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<style>body{font-family:system-ui;max-width:680px;margin:12vh auto;padding:24px;color:#172033}code{background:#f1f5f9;padding:3px 6px;border-radius:5px}a{color:#a16207}</style></head>'
        '<body><h1>Admin storage setup required</h1>'
        '<p>This Vercel deployment has no persistent database configured, so the change was not saved.</p>'
        '<p>Add <code>DATABASE_URL</code> or <code>POSTGRES_URL</code> in Vercel Project Settings → Environment Variables, then redeploy.</p>'
        '<p><a href="/admin">Return to admin</a></p></body></html>', 503
    )

# ==================== RUN ====================
if __name__ == '__main__':
    app.run(debug=True)
