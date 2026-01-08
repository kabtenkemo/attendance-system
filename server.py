from flask import Flask, request, jsonify
import pyodbc
from datetime import date, datetime
import threading
import time
import schedule

app = Flask(__name__)

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=(localdb)\\ahmedEide;"
        "DATABASE=ElsewedySchoolSysDB_DEV;"
        "UID=attendance_app;"
        "PWD=123;"
    )

def AbsenceRecords():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.fast_executemany= True
    select_abs = """exec select_absence"""
    cursor.execute(select_abs)
    records = cursor.fetchall()
    
    data=[]
    for student in records:
        account_id = student[0]
        class_id = student[1]
        for seccion in range(1,8):
          data.append((account_id,class_id,seccion,date.today()))
          
    insert_abs = """INSERT INTO AbsenceRecords (studentid, classid ,SessionID, DateOfAbsence) VALUES (?, ?, ?, ?)"""
    cursor.executemany(insert_abs, data)
    conn.commit()
    cursor.close()
    conn.close()

def run_timer():
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule.every().day.at("09:00").do(AbsenceRecords)


thread=threading.Thread(target=run_timer)
thread.daemon = True
thread.start()


@app.route("/auto_attendance", methods=["POST"])
def auto_attendance():
    data = request.json
    mac_address = data.get("Mac_address")

    if not mac_address:
        return jsonify({"status": "error", "message": "MAC address missing"}), 400

    today = date.today()
    conn = get_connection()
    cursor = conn.cursor()
    current_time=datetime.now().hour

    if current_time> 9:
         return jsonify({"status": "error", "message": "No one is allowed to come after 9 AM"}), 400


    check_ext_query = """
    exec mac_check @macaddress= ?;
    """
    cursor.execute(check_ext_query, mac_address)
    ext_row = cursor.fetchone()

    if not ext_row:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "MAC not registered in StudentExtension"}), 400

    account_id = ext_row.AccountId

    check_att_query = """
    exec check_attendance @macaddress = ?;
    """
    cursor.execute(check_att_query, mac_address)
    att_row = cursor.fetchone()

    if att_row:
        cursor.execute("SELECT FullNameEN FROM account WHERE id = ?", account_id)
        student = cursor.fetchone()
        full_name = student.FullNameEN if student else "Student"
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": f"Welcome {full_name}"})

    insert_query = """
    INSERT INTO Auto_attendance (Mac_address, Account_id, attendance_date)
    VALUES (?, ?, ?)
    """
    cursor.execute(insert_query, mac_address, account_id, today)
    conn.commit()

    cursor.execute("SELECT FullNameEN FROM account WHERE id = ?", account_id)
    student = cursor.fetchone()
    full_name = student.FullNameEN if student else "Student"

    cursor.close()
    conn.close()

    return jsonify({"status": "success", "message": f"Welcome {full_name}"})

@app.route("/Days_of_absence", methods=["POST"])
def absence_counter():
    data = request.json
    mac_address = data.get("Mac_address")

    if not mac_address:
        return jsonify({"status": "error", "message": "MAC address missing"}), 400
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT AccountId FROM StudentExtension WHERE MACAddress = ?", mac_address)
        ext_row = cursor.fetchone()
        
        if not ext_row:
            return jsonify({"status": "error", "message": "MAC not registered"}), 404

        account_id = ext_row.AccountId

        count_days_query = """ 
            SELECT COUNT(*) as FullAbsenceCount
            FROM (
                SELECT DateOfAbsence
                FROM AbsenceRecords
                WHERE StudentId = ? 
                GROUP BY DateOfAbsence
                HAVING COUNT(SessionID) = 8
            ) AS StudentFullDays;
        """
        cursor.execute(count_days_query, account_id)
        row = cursor.fetchone()
        days = row.FullAbsenceCount if row else 0

        return jsonify({"status": "success", "total_absent_days": days})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn:
            conn.close()
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# this is comment line