from flask import Blueprint, jsonify, request, session
import mysql.connector
from datetime import datetime
import os
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from threading import Thread
import secrets  # For generating secure tokens


guard_bp = Blueprint('guard', __name__, url_prefix='/guard')

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'abc@gmail.com'  # Replace with your email
EMAIL_PASSWORD = 'XXXX XXXX XXXX XXXX'  # Replace with your app-specific password

UPLOAD_FOLDER = 'static/uploads/visitor_photos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'project',
    'port': '3306'  # Verify this matches your MySQL setup
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        print("Database connected successfully")
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection failed: {str(e)}")
        raise Exception(f"Database connection failed: {str(e)}")

def send_email_async(msg):
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=30) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {str(e)}")

@guard_bp.route('/profile', methods=['GET'])
def get_guard_profile():
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    guard_id = session.get('user_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, email, whatsapp 
            FROM guard 
            WHERE id = %s
        """, (guard_id,))
        guard = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if guard:
            return jsonify({
                'success': True,
                'guard': {
                    'id': guard['id'],
                    'name': guard['name'],
                    'email': guard['email'],
                    'whatsapp': guard['whatsapp'],
                    'shift': 'Day Shift'
                }
            })
        return jsonify({'success': False, 'message': 'Guard not found'}), 404
    except Exception as e:
        print(f"Error in get_guard_profile: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/stats', methods=['GET'])
def get_guard_stats():
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE status = 'approved' AND exit_time IS NULL")
        active_visitors = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE DATE(entry_time) = CURDATE()")
        today_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE status = 'pre-approved'")
        pre_approved = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM visitors WHERE status = 'pending'")
        pending_approvals = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'activeVisitors': active_visitors,
                'todayEntries': today_entries,
                'preApproved': pre_approved,
                'pendingApprovals': pending_approvals
            }
        })
    except Exception as e:
        print(f"Error in get_guard_stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/active-visitors', methods=['GET'])
def get_active_visitors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.id, v.visitor_name AS name, v.contact_number AS phone, v.purpose, 
                   fo.flat_number AS flatNumber, v.entry_time AS entryTime, v.status
            FROM visitors v
            JOIN flat_owner fo ON v.owner_id = fo.id
            WHERE v.status IN ('approved', 'pending') AND v.exit_time IS NULL
        """)
        visitors = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for visitor in visitors:
            if visitor['entryTime']:
                visitor['entryTime'] = visitor['entryTime'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'visitors': visitors
        })
    except Exception as e:
        print(f"Error in get_active_visitors: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/pre-approved', methods=['GET'])
def get_pre_approved():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.id, v.visitor_name AS name, fo.flat_number AS flatNumber, 
                   v.expected_date AS expectedTime, v.purpose
            FROM visitors v
            JOIN flat_owner fo ON v.owner_id = fo.id
            WHERE v.status = 'pre-approved'
        """)
        visitors = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for visitor in visitors:
            if visitor['expectedTime']:
                visitor['expectedTime'] = visitor['expectedTime'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'visitors': visitors
        })
    except Exception as e:
        print(f"Error in get_pre_approved: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/visitor-records', methods=['GET'])
def get_visitor_records():
    time_filter = request.args.get('filter', 'today')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT v.visitor_name AS visitorName, fo.flat_number AS flatNumber, v.purpose,
                   v.entry_time AS entryTime, v.exit_time AS exitTime, v.status
            FROM visitors v
            JOIN flat_owner fo ON v.owner_id = fo.id
        """
        
        if time_filter == 'today':
            query += " WHERE DATE(v.entry_time) = CURDATE()"
        elif time_filter == 'week':
            query += " WHERE v.entry_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time_filter == 'month':
            query += " WHERE v.entry_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for record in records:
            record['entryTime'] = record['entryTime'].strftime('%Y-%m-%d %H:%M:%S') if record['entryTime'] else '-'
            record['exitTime'] = record['exitTime'].strftime('%Y-%m-%d %H:%M:%S') if record['exitTime'] else '-'
            record['visitorName'] = record['visitorName'] or '-'
            record['flatNumber'] = record['flatNumber'] or '-'
            record['purpose'] = record['purpose'] or '-'
            record['status'] = record['status'] or 'Unknown'
        
        return jsonify({
            'success': True,
            'records': records
        })
    except Exception as e:
        print(f"Error in get_visitor_records: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/flat-numbers', methods=['GET'])
def get_flat_numbers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT flat_number, name FROM flat_owner")
        flats = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'flats': flats})
    except Exception as e:
        print(f"Error in get_flat_numbers: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@guard_bp.route('/add-visitor', methods=['POST'])
def add_visitor():
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        visitor_name = request.form['visitorName']
        contact_number = request.form['contactNumber']
        flat_number = request.form['flatNumber']
        purpose = request.form['purpose']
        live_photo = request.form.get('livePhoto')
        vehicle_number = request.form.get('vehicleNumber', '')
        id_proof_number = request.form['idProofNumber']

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, name FROM flat_owner WHERE flat_number = %s", (flat_number,))
        owner = cursor.fetchone()
        if not owner:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Flat number not found'}), 404
        
        owner_id, owner_email, owner_name = owner
        
        photo_path = None
        if live_photo:
            photo_data = base64.b64decode(live_photo.split(',')[1])
            photo_filename = f"visitor_{visitor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            with open(photo_path, 'wb') as f:
                f.write(photo_data)
            photo_path = f"/{photo_path}"

        # Generate a unique token
        token = secrets.token_urlsafe(16)

        cursor.execute("""
            INSERT INTO visitors (owner_id, visitor_name, contact_number, purpose, 
                                status, visitor_photo, vehicle_number, id_proof_number, token)
            VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s, %s)
        """, (owner_id, visitor_name, contact_number, purpose, photo_path, vehicle_number, id_proof_number, token))
        
        visitor_id = cursor.lastrowid
        conn.commit()
        
        # Include token in the approval/deny links
        approval_link = f"http://192.168.152.206:5000/guard/approve-visitor/{visitor_id}?token={token}"
        deny_link = f"http://192.168.152.206:5000/guard/deny-visitor/{visitor_id}?token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = owner_email
        msg['Subject'] = f"New Visitor Approval Request for {flat_number}"
        
        body = f"""
        New Visitor Request:
        Visitor Name: {visitor_name}
        Contact: {contact_number}
        Purpose: {purpose}
        
        Please review the attached photo and choose an action:
        Approve: {approval_link}
        Deny: {deny_link}
        """
        msg.attach(MIMEText(body, 'plain'))
        
        if live_photo:
            img_data = base64.b64decode(live_photo.split(',')[1])
            img = MIMEImage(img_data, name="visitor_photo.png")
            msg.attach(img)
        
        Thread(target=send_email_async, args=(msg,)).start()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Visitor added and email sent'})
    except Exception as e:
        print(f"Error in add_visitor: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
      
@guard_bp.route('/mark-exit/<visitor_id>', methods=['POST'])
def mark_exit(visitor_id):
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET exit_time = NOW(), status = 'approved'
            WHERE id = %s AND exit_time IS NULL
        """, (visitor_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Exit marked'})
        return jsonify({'success': False, 'message': 'Visitor not found or already exited'}), 404
    except Exception as e:
        print(f"Error in mark_exit: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/mark-entry/<request_id>', methods=['POST'])
def mark_entry(request_id):
    if 'logged_in' not in session or session.get('role') != 'guard':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET entry_time = NOW(), status = 'approved'
            WHERE id = %s AND status = 'pre-approved'
        """, (request_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Entry marked'})
        return jsonify({'success': False, 'message': 'Visitor not found or not pre-approved'}), 404
    except Exception as e:
        print(f"Error in mark_entry: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/deny-visitor/<visitor_id>', methods=['GET'])
def deny_visitor(visitor_id):
    token = request.args.get('token')
    if not token:
        return jsonify({'success': False, 'message': 'Token required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET status = 'denied'
            WHERE id = %s AND status IN ('pending', 'approved') AND token = %s
        """, (visitor_id, token))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Visitor denied'})
        return jsonify({'success': False, 'message': 'Visitor not found, already denied, or invalid token'}), 404
    except Exception as e:
        print(f"Error in deny_visitor: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/approve-visitor/<visitor_id>', methods=['GET'])
def approve_visitor(visitor_id):
    token = request.args.get('token')
    if not token:
        return jsonify({'success': False, 'message': 'Token required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visitors 
            SET status = 'approved', entry_time = NOW()
            WHERE id = %s AND status = 'pending' AND token = %s
        """, (visitor_id, token))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'success': True, 'message': 'Visitor approved'})
        return jsonify({'success': False, 'message': 'Visitor not found, not pending, or invalid token'}), 404
    except Exception as e:
        print(f"Error in approve_visitor: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@guard_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('role', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})