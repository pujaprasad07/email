import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG

def send_email(to_email, subject, body, html_body=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email_address']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['email_address'], EMAIL_CONFIG['email_password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_attendance_report(parent_email, student_name, report_data, period='daily'):
    subject = f"Attendance Report for {student_name} ({period.capitalize()})"
    
    # Plain text version
    body = f"""
    Attendance Report for {student_name}
    Period: {period.capitalize()}
    
    Total Days: {report_data['total_days']}
    Present: {report_data['present_days']}
    Absent: {report_data['absent_days']}
    Attendance Percentage: {report_data['percentage']}%
    """
    
    # HTML version
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">Attendance Report for {student_name}</h2>
            <p><strong>Period:</strong> {period.capitalize()}</p>
            
            <table border="1" cellpadding="5" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <tr style="background-color: #f2f2f2;">
                    <th>Total Days</th>
                    <th>Present</th>
                    <th>Absent</th>
                    <th>Percentage</th>
                </tr>
                <tr>
                    <td>{report_data['total_days']}</td>
                    <td>{report_data['present_days']}</td>
                    <td>{report_data['absent_days']}</td>
                    <td>{report_data['percentage']}%</td>
                </tr>
            </table>
            
            <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
                <p>Please contact the school if you have any questions or concerns about this report.</p>
            </div>
            
            <p style="margin-top: 20px; font-size: 12px; color: #7f8c8d;">
                This is an automated message. Please do not reply directly to this email.
            </p>
        </body>
    </html>
    """
    
    return send_email(parent_email, subject, body, html_body)