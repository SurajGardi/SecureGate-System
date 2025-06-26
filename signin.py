import mysql.connector
from mysql.connector import Error
from flask import jsonify, session, request
from mail import send_otp_email
import random
from datetime import datetime

# Database Configuration
db_config = {
    'host': 'localhost',
    'database': 'project',
    'user': 'root',
    'password': 'root',
    'port': '3306'  # Verify this matches your MySQL setup
}

# OTP storage with expiration
otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_and_store_otp(email):
    otp = generate_otp()
    otp_store[email] = {'otp': otp, 'expires_at': datetime.now() + datetime.timedelta(minutes=5)}
    print(f"Storing OTP for {email}: {otp}")
    return send_otp_email(email, otp)

def verify_otp(email, provided_otp):
    if email in otp_store:
        stored_otp = otp_store[email]['otp']
        expires_at = otp_store[email]['expires_at']
        if datetime.now() < expires_at and provided_otp == stored_otp:
            del otp_store[email]
            return True
    return False

def check_user_credentials(role, email, password, admin_key=None):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        role_table = {
            'admin': 'admin',
            'guard': 'guard',
            'flat_owner': 'flat_owner'
        }
        table_name = role_table.get(role)

        if not table_name:
            return False, None, None

        if role == 'admin':
            query = f"SELECT id, admin_key FROM {table_name} WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()
            if user and user['admin_key'] == admin_key:
                return True, role, user['id']
        else:
            query = f"SELECT id FROM {table_name} WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()
            if user:
                return True, role, user['id']
        
        return False, None, None

    except Error as e:
        print(f"Database Error: {str(e)}")
        return False, None, None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def handle_signin(request):
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('role', 'email', 'password')):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        role = data['role'].strip().lower()
        email = data['email'].strip()
        password = data['password'].strip()

        if role == 'admin':
            admin_key = data.get('admin_key', '').strip()
            
            if not admin_key:
                return jsonify({'success': False, 'message': 'Admin key is required'}), 400
            
            is_valid, user_role, user_id = check_user_credentials(role, email, password, admin_key)
        else:
            is_valid, user_role, user_id = check_user_credentials(role, email, password)

        if is_valid:
            session['logged_in'] = True
            session['role'] = user_role
            session['email'] = email
            session['user_id'] = user_id
            redirect_url = f"/{user_role}"
            return jsonify({'success': True, 'role': user_role, 'redirect_url': redirect_url}), 200

        # If not valid, check role and provide specific message
        if role == 'admin':
            return jsonify({'success': False, 'message': 'Admin not found'}), 401
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    except Exception as e:
        print(f"Exception in handle_signin: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal Server Error'}), 500