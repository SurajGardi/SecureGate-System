import mysql.connector
from mysql.connector import Error
from flask import Blueprint, jsonify, request, session
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

# Database Configuration
db_config = {
    'host': 'localhost',
    'database': 'project',
    'user': 'root',
    'password': 'root',
    'port': '3306'  # Verify this matches your MySQL setup
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def check_admin_session():
    if 'logged_in' not in session or session.get('role') != 'admin':
        print("Session check failed: User not logged in or not an admin")
        return jsonify({'success': False, 'message': 'Unauthorized - Please log in'}), 401
    return None

# Admin Profile
@admin_bp.route('/profile', methods=['GET'])
def get_admin_profile():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    email = session.get('email')
    if not email:
        print("No email found in session")
        return jsonify({'success': False, 'message': 'Email not found in session'}), 401

    connection = get_db_connection()
    if not connection:
        print("Database connection failed")
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, name, email, whatsapp FROM admin WHERE email = %s"
        cursor.execute(query, (email,))
        admin = cursor.fetchone()
        if admin:
            print(f"Admin profile fetched: Email={admin['email']}, Name={admin['name']}")
            return jsonify({'success': True, 'admin': admin})
        else:
            print(f"No admin found with email: {email}")
            return jsonify({'success': False, 'message': 'Admin not found'}), 404
    except Error as e:
        print(f"Error fetching admin profile: {e}")
        return jsonify({'success': False, 'message': f'Error fetching admin profile: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Dashboard Stats
@admin_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        stats = {}
        cursor.execute("SELECT COUNT(*) as count FROM visitors WHERE DATE(entry_time) = CURDATE()")
        stats['todayVisitors'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM visitors WHERE entry_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
        stats['monthlyVisitors'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM guard")
        stats['activeGuards'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM flat_owner")
        stats['totalFlats'] = cursor.fetchone()['count']
        print(f"Stats fetched: {stats}")
        return jsonify({'success': True, 'stats': stats})
    except Error as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'success': False, 'message': f'Error fetching stats: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Visitor Records
@admin_bp.route('/visitor-records', methods=['GET'])
def get_visitor_records():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    time_filter = request.args.get('timeFilter', 'all')
    search = request.args.get('search', '')
    print(f"Received timeFilter: {time_filter}, search: {search}")  # Debugging
    if time_filter not in ['today', 'week', 'month', 'all']:
        print(f"Invalid timeFilter value: {time_filter}")
        return jsonify({'success': False, 'message': 'Invalid filter value'}), 400

    connection = get_db_connection()
    if not connection:
        print("Database connection failed for visitor records")
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT v.id, v.visitor_name, v.owner_id AS flat_number, v.purpose, 
                   v.entry_time, v.exit_time, v.status
            FROM visitors v
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND v.visitor_name LIKE %s"
            params.append(f"%{search}%")
        if time_filter == 'today':
            query += " AND DATE(v.entry_time) = CURDATE()"
        elif time_filter == 'week':
            query += " AND v.entry_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time_filter == 'month':
            query += " AND v.entry_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        cursor.execute(query, params)
        visitors = cursor.fetchall()
        for visitor in visitors:
            visitor['entry_time'] = visitor['entry_time'].strftime('%H:%M %p') if visitor['entry_time'] else '-'
            visitor['exit_time'] = visitor['exit_time'].strftime('%H:%M %p') if visitor['exit_time'] else '-'
        print(f"Visitor records fetched: {len(visitors)} records")
        return jsonify({'success': True, 'visitors': visitors})
    except Error as e:
        print(f"Error fetching visitor records: {e}")
        return jsonify({'success': False, 'message': f'Error fetching visitor records: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Guard Records
@admin_bp.route('/guard-records', methods=['GET'])
def get_guard_records():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    guard_id = request.args.get('id')
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, name, whatsapp AS contact, 'Morning' AS shift, 'On Duty' AS status FROM guard WHERE 1=1"
        params = []
        if guard_id:
            query += " AND id = %s"
            params.append(guard_id)
        cursor.execute(query, params)
        guards = cursor.fetchall()
        print(f"Guard records fetched: {len(guards)} records")
        return jsonify({'success': True, 'guards': guards})
    except Error as e:
        print(f"Error fetching guard records: {e}")
        return jsonify({'success': False, 'message': f'Error fetching guard records: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Flat Owners
@admin_bp.route('/flat-owners', methods=['GET'])
def get_flat_owners():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    flat_number = request.args.get('flat_number')
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT fo.flat_number, fo.name, fo.whatsapp AS contact, 
                   COUNT(fm.id) AS members, 'Resident' AS status
            FROM flat_owner fo
            LEFT JOIN family_members fm ON fo.id = fm.owner_id
            WHERE 1=1
        """
        params = []
        if flat_number:
            query += " AND fo.flat_number = %s"
            params.append(flat_number)
        query += " GROUP BY fo.id, fo.flat_number, fo.name, fo.whatsapp"
        cursor.execute(query, params)
        owners = cursor.fetchall()
        print(f"Flat owners fetched: {len(owners)} records")
        return jsonify({'success': True, 'owners': owners})
    except Error as e:
        print(f"Error fetching flat owners: {e}")
        return jsonify({'success': False, 'message': f'Error fetching flat owners: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Analytics
@admin_bp.route('/analytics', methods=['GET'])
def get_analytics():
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT DATE(entry_time) AS date, COUNT(*) AS count
            FROM visitors
            WHERE entry_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(entry_time)
            ORDER BY date ASC
        """
        cursor.execute(query)
        db_data = cursor.fetchall()
        today = datetime.now().date()
        date_range = [today - timedelta(days=x) for x in range(30)]
        date_range.reverse()
        analytics = []
        db_dict = {row['date']: row['count'] for row in db_data}
        for date in date_range:
            formatted_date = date.strftime('%Y-%m-%d')
            count = db_dict.get(date, 0)
            analytics.append({'date': formatted_date, 'count': count})
        print(f"Analytics data fetched: {len(analytics)} records")
        return jsonify({'success': True, 'analytics': analytics})
    except Error as e:
        print(f"Error fetching analytics: {e}")
        return jsonify({'success': False, 'message': f'Error fetching analytics: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Delete Visitor
@admin_bp.route('/delete-visitor/<int:visitor_id>', methods=['POST'])
def delete_visitor(visitor_id):
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM visitors WHERE id = %s", (visitor_id,))
        connection.commit()
        print(f"Visitor {visitor_id} deleted successfully")
        return jsonify({'success': True, 'message': 'Visitor deleted successfully'})
    except Error as e:
        print(f"Error deleting visitor: {e}")
        return jsonify({'success': False, 'message': f'Error deleting visitor: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Delete Guard
@admin_bp.route('/delete-guard/<guard_id>', methods=['POST'])
def delete_guard(guard_id):
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM guard WHERE id = %s", (guard_id,))
        connection.commit()
        print(f"Guard {guard_id} deleted successfully")
        return jsonify({'success': True, 'message': 'Guard deleted successfully'})
    except Error as e:
        print(f"Error deleting guard: {e}")
        return jsonify({'success': False, 'message': f'Error deleting guard: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Delete Owner
@admin_bp.route('/delete-owner/<flat_number>', methods=['POST'])
def delete_owner(flat_number):
    auth_check = check_admin_session()
    if auth_check:
        return auth_check
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM flat_owner WHERE flat_number = %s", (flat_number,))
        connection.commit()
        print(f"Flat owner {flat_number} deleted successfully")
        return jsonify({'success': True, 'message': 'Flat owner deleted successfully'})
    except Error as e:
        print(f"Error deleting flat owner: {e}")
        return jsonify({'success': False, 'message': f'Error deleting flat owner: {str(e)}'}), 500
    finally:
        cursor.close()
        connection.close()

# Logout
@admin_bp.route('/logout', methods=['GET'])
def logout_admin():
    session.clear()
    print("Admin logged out successfully")
    return jsonify({'success': True, 'message': 'Logged out successfully'})