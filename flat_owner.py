from flask import Blueprint, jsonify, session, request
import mysql.connector
from mysql.connector import Error

flat_owner_bp = Blueprint('flat_owner', __name__, url_prefix='/flat_owner')

db_config = {
    'host': 'localhost',
    'database': 'project',
    'user': 'root',
    'password': 'root',
    'port': '3306'  # Verify this matches your MySQL setup
}

@flat_owner_bp.route('/get_owner_profile', methods=['GET'])
def get_owner_profile():
    print("Session:", session)
    connection = None
    cursor = None
    try:
        if 'email' not in session or session.get('role') != 'flat_owner':
            print("Unauthorized access attempt")
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, flat_number, email, whatsapp
            FROM flat_owner
            WHERE email = %s
        """, (session['email'],))
        owner = cursor.fetchone()
        print("Owner query result:", owner)
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404
        profile = {
            'id': owner['id'],
            'name': owner['name'],
            'flat_number': owner['flat_number'],
            'email': owner['email'],
            'whatsapp': owner['whatsapp']
        }
        return jsonify({"success": True, "profile": profile})
    except Error as e:
        print("Database error:", str(e))
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            
# Fetch Flat Owner Dashboard Stats
@flat_owner_bp.route('/flat_owner_dashboard_stats', methods=['GET'])
def get_flat_owner_dashboard_stats():
    connection = None
    cursor = None
    try:
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()

        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']

        cursor.execute("SELECT COUNT(*) AS total_family FROM family_members WHERE owner_id = %s", (owner_id,))
        family_count = cursor.fetchone()
        family_count = family_count['total_family'] if family_count else 0

        cursor.execute("""
            SELECT COUNT(*) AS todays_visitors 
            FROM visitors 
            WHERE owner_id = %s AND DATE(entry_time) = CURDATE()
        """, (owner_id,))
        today_visitors = cursor.fetchone()
        today_visitors = today_visitors['todays_visitors'] if today_visitors else 0

        cursor.execute("""
            SELECT COUNT(*) AS pre_approved_visitors 
            FROM visitors 
            WHERE owner_id = %s AND status = 'pre-approved'
        """, (owner_id,))
        preapproved_visitors = cursor.fetchone()
        preapproved_visitors = preapproved_visitors['pre_approved_visitors'] if preapproved_visitors else 0

        cursor.execute("""
            SELECT COUNT(*) AS pending_visitors 
            FROM visitors 
            WHERE owner_id = %s AND status = 'pending'
        """, (owner_id,))
        pending_visitors = cursor.fetchone()
        pending_visitors = pending_visitors['pending_visitors'] if pending_visitors else 0

        return jsonify({
            "success": True,
            "family_members": family_count,
            "todays_visitors": today_visitors,
            "preapproved_visitors": preapproved_visitors,
            "pending_visitors": pending_visitors
        })

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Add Family Member API
@flat_owner_bp.route('/add_family_member', methods=['POST'])
def add_family_member():
    try:
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404
        owner_id = owner['id']

        name = request.form.get('name')
        relationship = request.form.get('relationship')
        contact = request.form.get('contact')
        email = request.form.get('email')
        id_type = request.form.get('id_type')
        id_number = request.form.get('id_number')
        photo = request.form.get('photo')
        id_proof = request.form.get('id_proof')

        if not name or name.strip() == "":
            return jsonify({"success": False, "message": "Name cannot be empty!"}), 400
        if not relationship or relationship.strip() == "":
            return jsonify({"success": False, "message": "Relationship is required!"}), 400
        if not id_type or id_type.strip() == "":
            return jsonify({"success": False, "message": "ID Type is required!"}), 400
        if not id_number or id_number.strip() == "":
            return jsonify({"success": False, "message": "ID Number is required!"}), 400

        print(f"""INSERT INTO family_members (owner_id, name, relationship, contact, email, id_type, id_number, photo, id_proof) 
                  VALUES ({owner_id}, '{name}', '{relationship}', '{contact}', '{email}', '{id_type}', '{id_number}', '{photo}', '{id_proof}')""")

        query = """INSERT INTO family_members (owner_id, name, relationship, contact, email, id_type, id_number, photo, id_proof) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (owner_id, name, relationship, contact, email, id_type, id_number, photo, id_proof)

        cursor.execute(query, values)
        connection.commit()

        return jsonify({"success": True, "message": "Family member added successfully!"}), 200

    except Error as e:
        print("Database Error:", str(e))
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@flat_owner_bp.route('/get_family_members', methods=['GET'])
def get_family_members():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        email = session.get('email')
        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']
        cursor.execute("SELECT id, name, relationship, contact FROM family_members WHERE owner_id = %s", (owner_id,))
        members = cursor.fetchall()

        return jsonify({"success": True, "members": members})

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# Fetch Visitor Records
@flat_owner_bp.route('/visitor_records', methods=['GET'])
def get_visitor_records():
    connection = None
    cursor = None
    try:
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']
        filter_type = request.args.get('filter', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search_query = request.args.get('search', '')

        query = """
            SELECT visitor_name, contact_number, purpose, entry_time, exit_time, status
            FROM visitors
            WHERE owner_id = %s
        """
        params = [owner_id]

        if filter_type == 'today':
            query += " AND DATE(entry_time) = CURDATE()"
        elif filter_type == 'week':
            query += " AND entry_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif filter_type == 'month':
            query += " AND entry_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        elif filter_type == 'custom' and start_date and end_date:
            query += " AND DATE(entry_time) BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        if search_query:
            query += " AND visitor_name LIKE %s"
            params.append(f"%{search_query}%")

        query += " ORDER BY entry_time DESC"

        cursor.execute(query, params)
        visitor_records = cursor.fetchall()

        for record in visitor_records:
            if record['entry_time']:
                record['entry_time'] = record['entry_time'].strftime('%Y-%m-%d %H:%M:%S')
            if record['exit_time']:
                record['exit_time'] = record['exit_time'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(visitor_records)

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Fetch Pre-approved Visitor Records
@flat_owner_bp.route('/get_pre_approved_visitors', methods=['GET'])
def get_pre_approved_visitors():
    if 'email' not in session or session.get('role') != 'flat_owner':
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (session['email'],))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404

        owner_id = owner['id']

        cursor.execute("""
            SELECT visitor_name, contact_number, purpose, expected_date, status
            FROM visitors
            WHERE owner_id = %s AND status = 'pre-approved'
            ORDER BY expected_date ASC
        """, (owner_id,))

        records = cursor.fetchall()

        return jsonify({"success": True, "pre_approved_visitors": records})

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@flat_owner_bp.route('/pre_approve', methods=['POST'])
def pre_approve_visitor():
    connection = None
    cursor = None
    try:
        email = session.get('email')
        if not email or session.get('role') != 'flat_owner':
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id FROM flat_owner WHERE email = %s", (email,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({"success": False, "message": "Owner not found"}), 404
        owner_id = owner['id']

        data = request.get_json()
        visitor_name = data.get('visitor_name')
        contact = data.get('contact_number')
        purpose = data.get('purpose')
        expected_date = data.get('expected_date')
        additional_notes = data.get('additional_notes')

        if not all([visitor_name, contact, purpose, expected_date]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        expected_date = expected_date.split(" ")[0]

        query = """
            INSERT INTO visitors (owner_id, visitor_name, contact_number, purpose, expected_date, status)
            VALUES (%s, %s, %s, %s, %s, 'pre-approved')
        """
        values = (owner_id, visitor_name, contact, purpose, expected_date)
        cursor.execute(query, values)
        connection.commit()

        return jsonify({"success": True, "message": "Visitor pre-approved successfully"}), 200

    except Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()