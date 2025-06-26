from flask import Flask, render_template, session, redirect, request, jsonify
from flask_cors import CORS
from admin import admin_bp  # Import admin blueprint
from guard import guard_bp  # Import guard blueprint
from flat_owner import get_flat_owner_dashboard_stats, add_family_member, get_family_members, get_visitor_records, \
    get_pre_approved_visitors, pre_approve_visitor,flat_owner_bp

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 's3cr3t_k3y_123!@#'
CORS(app, supports_credentials=True)

# Register Blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(flat_owner_bp, url_prefix='/flat_owner')  # Modified: Added flat_owner_bp registration
app.register_blueprint(guard_bp, url_prefix='/guard')

# ----------------------------------**** General Routes ****-----------------------------------
@app.route('/')
def index():
    return render_template('signup.html')

@app.route('/signin', methods=['POST'])
def signin():
    from signin import handle_signin
    return handle_signin(request)

@app.route('/request-otp', methods=['POST'])
def request_otp():
    from signin import send_and_store_otp
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    if not email or not role:
        return jsonify({'success': False, 'message': 'Email and role are required'}), 400
    if role != 'admin':
        return jsonify({'success': False, 'message': 'OTP is only required for admin'}), 400
    if send_and_store_otp(email):
        return jsonify({'success': True, 'message': 'OTP sent to email'}), 200
    return jsonify({'success': False, 'message': 'Failed to send OTP'}), 500

from signup import create_user, verify_otp

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    return create_user(data)

@app.route('/verify-otp', methods=['POST'])
def verify_otp_route():
    data = request.get_json()
    return verify_otp(data)

# Dashboard Routes
@app.route('/admin')
def admin_dashboard():
    if 'logged_in' in session and session.get('role') == 'admin':
        return render_template('Admin1.html')
    return redirect('/')

@app.route('/guard')
def guard_dashboard():
    if 'logged_in' in session and session.get('role') == 'guard':
        return render_template('Guard.html')
    return redirect('/')

@app.route('/flat_owner')
def flat_owner_dashboard():
    if 'logged_in' in session and session.get('role') == 'flat_owner':
        return render_template('Flat-Owner.html')
    return redirect('/')

# ----------------------------------**** Flat Owner Routes ****-----------------------------------
@app.route('/flat_owner_dashboard_stats', methods=['GET'])
def fetch_dashboard_stats():
    return get_flat_owner_dashboard_stats()

@app.route('/add_family_member', methods=['POST'])
def add_member():
    return add_family_member()

@app.route('/get_family_members', methods=['GET'])
def family_members():
    return get_family_members()

@app.route('/get_pre_approved_visitors', methods=['GET'])
def handle_pre_approve():
    return get_pre_approved_visitors()

@app.route('/pre_approve', methods=['POST'])
def pre_approve():
    return pre_approve_visitor()

@app.route('/visitor_records', methods=['GET'])
def flat_owner_visitor_records():
    return get_visitor_records()

# ----------------------------------**** Guard Routes ****-----------------------------------
# Guard routes are handled in guard_bp (guard.py), e.g., /guard/profile, /guard/stats, etc.

# ----------------------------------**** Admin Routes ****-----------------------------------
# Admin routes are handled in admin_bp (admin.py), e.g., /admin/stats, /admin/today-visitors, etc.

# ----------------------------------**** Logout Route ****-----------------------------------
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/signin')

# ----------------------------------**** Run Application ****-----------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)