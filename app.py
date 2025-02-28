from datetime import datetime
from flask import Flask, request, jsonify,session, redirect, url_for, render_template
import mysql.connector
from flask_cors import CORS, cross_origin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='../templates')
CORS(app, origins=["http://127.0.0.1:5500", "http://localhost:5500"]) # Example
app.secret_key = 'your_secret_key'

# Database configuration (REPLACE with your credentials)
mydb = mysql.connector.connect(
  host="localhost",  # e.g., localhost
  user="root",
  password="1234",
  database="attendance_data"
)

if mydb.is_connected():
    print("Database connection established successfully")


@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        user_type = request.form['userType']
        username = request.form['username']
        password = request.form['password']

        mycursor = mydb.cursor()
        sql = "SELECT * FROM users WHERE ID = %s"  # Assuming your table is named 'users'
        val = (username,)
        mycursor.execute(sql, val)
        result = mycursor.fetchone()

        if result:
            stored_password = result[1]  # Assuming password is the third column (index 2)
            stored_role ="" # Assuming role is the fourth column (index 3)
            if stored_password == password: # Comparing entered password with hashed password
                if stored_role == "":
                    session['ID'] = username
 #                   session['role'] = user_type
                    return render_template('homer.html')
                else:
                    error_message = "Incorrect User Type"
            else:
                error_message = "Invalid password"
        else:
            error_message = "Invalid username"

        mycursor.close()  # Close the cursor after use

    return render_template('login.html', error_message=error_message)


@app.route('/api/reports', methods=['GET'])
@cross_origin()  # Allow all domains to access this API

def get_reports():
    report_type = request.args.get('reportType')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    try:
        mycursor = mydb.cursor()
        query = ""

        if report_type == 'daily':
            if not start_date_str:
                return jsonify({"error": "Start date is required for daily report"}), 400

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format for startDate (YYYY-MM-DD)"}), 400  # More specific error message

            query = "SELECT StudentID,CONCAT(date, ' ', time) as DateTime, status FROM ex_data WHERE date = %s"  # Assuming 'date' column is of DATE type
            mycursor.execute(query, (start_date,))

        elif report_type in ('weekly', 'monthly', 'custom'):
            if not start_date_str or not end_date_str:
                return jsonify({"error": "Start and end dates are required"}), 400

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format for dates (YYYY-MM-DD)"}), 400  # More specific

            query = "SELECT StudentID, CONCAT(date, ' ', time) as DateTime ,status FROM ex_data WHERE date BETWEEN %s AND %s" # Assuming 'date' column is of DATE type
            mycursor.execute(query, (start_date, end_date))

        else:
            return jsonify({"error": "Invalid report type"}), 400

        results = mycursor.fetchall()
        mycursor.close()

        report_data = []
        print(results)
        for row in results:
            report_data.append({
                "student_id": row[0],
                "date": row[1],
                "status": row[2]
            })

        return jsonify(report_data), 200

    except Exception as e:
        print(f"Error fetching reports: {e}") # Keep this for debugging in your logs
        return jsonify({"error": "Error fetching reports"}), 500  # Generic message for the user

@app.route('/api/attendance', methods=['POST'])  # Example to save attendance
def save_attendance():
    data = request.get_json()  # Get JSON data from the request body
    if not data:
        return jsonify({'error': 'No data received'}), 400 # Check for missing data

    student_id = data.get('StudentID')
    status = data.get('status')

    try:
        mycursor = mydb.cursor()
        sql = "INSERT INTO ex_data (StudentID, status) VALUES (%s, %s)"
        val = (student_id, status)  
        mycursor.execute(sql, val)
        mydb.commit()
        return jsonify({"message": "Attendance saved successfully"}), 201  # 201 Created

    except mysql.connector.Error as err:
        print(f"Error saving attendance: {err}") # Print the full error for debugging
        mydb.rollback() # Very important to rollback on error!
        return jsonify({"error": str(err)}), 500  # Send a more informative error message

    finally:
        mycursor.close() # Close the cursor in a finally block to ensure it is always closed

if __name__ == '__main__':
    app.run(debug=True)  # debug=True for development (auto-reloads)




