from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import mysql.connector
from config import DB_CONFIG
from email_service import send_attendance_report
import pandas as pd
from io import BytesIO
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_attendance_report', methods=['POST'])
def get_attendance_report():
    data = request.json
    report_type = data.get('report_type', 'daily')
    class_filter = data.get('class_filter', 'all')
    date_filter = data.get('date_filter', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Determine date range
    if report_type == 'daily':
        start_date = end_date = date_filter
    elif report_type == 'weekly':
        date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
        start_date = (date_obj - timedelta(days=date_obj.weekday())).strftime('%Y-%m-%d')
        end_date = (date_obj + timedelta(days=6-date_obj.weekday())).strftime('%Y-%m-%d')
    elif report_type == 'monthly':
        date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
        start_date = date_obj.replace(day=1).strftime('%Y-%m-%d')
        end_date = (date_obj.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
    
    # Get attendance data
    query = """
    SELECT s.student_id, s.student_name, s.roll_number, s.class, s.email, 
           a.date, a.status
    FROM students s
    LEFT JOIN attendance a ON s.student_id = a.student_id 
        AND a.date BETWEEN %s AND %s
    """
    
    params = [start_date, end_date]
    
    if class_filter != 'all':
        query += " WHERE s.class = %s"
        params.append(class_filter)
    
    cursor.execute(query, params)
    attendance_data = cursor.fetchall()
    
    # Process data for report
    students = {}
    for record in attendance_data:
        student_id = record['student_id']
        if student_id not in students:
            students[student_id] = {
                'student_name': record['student_name'],
                'roll_number': record['roll_number'],
                'class': record['class'],
                'email': record['email'],
                'attendance': []
            }
        if record['date']:
            students[student_id]['attendance'].append({
                'date': record['date'].strftime('%Y-%m-%d'),
                'status': record['status']
            })
    
    # Calculate statistics
    report = []
    for student_id, student_data in students.items():
        total_days = len(student_data['attendance'])
        present_days = len([a for a in student_data['attendance'] if a['status'] == 'Present'])
        absent_days = total_days - present_days
        percentage = round((present_days / total_days) * 100, 2) if total_days > 0 else 0
        
        report.append({
            'student_id': student_id,
            'student_name': student_data['student_name'],
            'roll_number': student_data['roll_number'],
            'class': student_data['class'],
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'percentage': percentage,
            'email': student_data['email']
        })
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'report': report,
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date
    })

@app.route('/export_excel', methods=['POST'])
def export_excel():
    data = request.json
    report = data.get('report', [])
    
    # Create DataFrame
    df = pd.DataFrame(report)
    
    # Create Excel file in memory
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Attendance Report', index=False)
    
    # Format Excel file
    workbook = writer.book
    worksheet = writer.sheets['Attendance Report']
    
    # Add percentage formatting
    percent_format = workbook.add_format({'num_format': '0.00%'})
    worksheet.set_column('H:H', 15, percent_format)
    
    # Add conditional formatting
    green_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
    yellow_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
    red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    
    worksheet.conditional_format('H2:H100', {
        'type': 'cell',
        'criteria': '>=',
        'value': 75,
        'format': green_format
    })
    
    worksheet.conditional_format('H2:H100', {
        'type': 'cell',
        'criteria': 'between',
        'minimum': 50,
        'maximum': 74,
        'format': yellow_format
    })
    
    worksheet.conditional_format('H2:H100', {
        'type': 'cell',
        'criteria': '<',
        'value': 50,
        'format': red_format
    })
    
    writer.close()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'attendance_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/send_notifications', methods=['POST'])
def send_notifications():
    data = request.json
    report = data.get('report', [])
    report_type = data.get('report_type', 'daily')
    
    results = []
    for student in report:
        if student['email']:
            report_data = {
                'total_days': student['total_days'],
                'present_days': student['present_days'],
                'absent_days': student['absent_days'],
                'percentage': student['percentage']
            }
            
            success = send_attendance_report(
                student['email'],
                student['student_name'],
                report_data,
                report_type
            )
            
            results.append({
                'student_id': student['student_id'],
                'student_name': student['student_name'],
                'email': student['email'],
                'success': success
            })
    
    return jsonify({
        'success': True,
        'results': results
    })

if __name__ == '__main__':
    app.run(debug=True)
