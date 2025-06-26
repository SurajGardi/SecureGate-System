import mysql.connector
from mysql.connector import Error, pooling
from flask import jsonify
import random
import logging
from mail import send_otp_email

logging.basicConfig(level=logging.INFO)

db_config = {
    'host': 'localhost',
    'database': 'project',
    'user': 'root',
    'password': 'root',
    'port': '3306'  # Verify this matches your MySQL setup
}

connection_pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                            pool_size=5,
                                            **db_config)

otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email):
    otp = generate_otp()
    otp_store[email] = otp
    print(f"Storing OTP for {email}: {otp}")
    return otp

def create_user(data):
    email = data.get('email')
    role = data.get('role')
    
    if not email or not role:
        return jsonify({"success": False, "message": "Email and role are required"}), 400

    otp = send_otp(email)
    if send_otp_email(email, otp):
        return jsonify({"success": True, "message": "OTP sent successfully"}), 200
    return jsonify({"success": False, "message": "Failed to send OTP"}), 500

def verify_otp(data):
    email = data.get('email')
    entered_otp = data.get('otp')

    stored_otp = otp_store.get(email)

    if stored_otp and stored_otp == entered_otp:
        del otp_store[email]
        return insert_user(data)  # <- This might be failing!
    return jsonify({"success": False, "message": "Invalid OTP"}), 401


def insert_user(data):
    try:
        connection = connection_pool.get_connection()
        cursor = connection.cursor()

        role = data.get('role')
        name = data.get('name')
        email = data.get('email')
        whatsapp = data.get('whatsapp')
        password = data.get('password')

        query = None  # Initialize query variable
        values = None  # Initialize values variable

        if role == 'guard':
            user_id = generate_user_id('G', 'guard', cursor)
            query = """INSERT INTO guard (id, name, email, whatsapp, password) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (user_id, name, email, whatsapp, password)

        elif role == 'flat_owner':
            flat_number = data.get('flatNumber')
            if not flat_number:
                return jsonify({"success": False, "message": "Flat number is required"}), 400
            user_id = generate_user_id('F', 'flat_owner', cursor)
            query = """INSERT INTO flat_owner (id, name, email, whatsapp, password, flat_number) 
                       VALUES (%s, %s, %s, %s, %s, %s)"""
            values = (user_id, name, email, whatsapp, password, flat_number)

        elif role == 'admin':
            admin_key = data.get('adminKey')
            if admin_key != "7777":
                return jsonify({"success": False, "message": "Invalid Admin Key"}), 401
            user_id = generate_user_id('A', 'admin', cursor)
            query = """INSERT INTO admin (id, name, email, whatsapp, password, admin_key) 
                       VALUES (%s, %s, %s, %s, %s, %s)"""
            values = (user_id, name, email, whatsapp, password, admin_key)

        else:
            return jsonify({"success": False, "message": "Invalid role"}), 400

        if query is None or values is None:
            return jsonify({"success": False, "message": "Query or values not set"}), 500

        cursor.execute(query, values)
        connection.commit()

        return jsonify({"success": True, "message": "User created successfully", "user_id": user_id}), 200

    except Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def generate_user_id(prefix, table_name, cursor):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0] + 1
    return f"{prefix}{count:02d}"