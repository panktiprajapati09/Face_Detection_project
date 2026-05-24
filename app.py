from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response,flash
import os
from datetime import datetime
from config import Config
from database import Database
import face_recognition as fr  
import json
import secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart 
import mysql.connector
import cv2
import numpy as np

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Initialize database
db = Database()
db.setup_database()

# Create a simple face recognition utility class
# ==================== IMPROVED FACE RECOGNIZER ====================
# Add this updated FaceRecognizer class to your app.py
# ==================== FACE RECOGNIZER CLASS ====================

class FaceRecognizer:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.face_timestamps = {}  # Track when faces were last recognized
        self.unknown_faces_log = []  # Log unknown faces
        self.load_known_faces()
        
    def load_known_faces(self):
        """Load known faces with quality checking"""
        users = db.execute_query("SELECT id, student_id, name, photo_path FROM users")
        
        if users:
            for user in users:
                image_path = os.path.join(Config.KNOWN_FACES_DIR, user['photo_path'])
                if os.path.exists(image_path):
                    try:
                        # Load image
                        image = cv2.imread(image_path)
                        if image is None:
                            print(f"⚠️ Could not load image: {image_path}")
                            continue
                        
                        # Convert to RGB for face_recognition
                        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        
                        # Check face quality if enabled
                        if Config.ENABLE_FACE_QUALITY_CHECK:
                            quality_result, quality_message = self.check_face_quality(image)
                            if not quality_result:
                                print(f"⚠️ Low quality face for {user['name']}: {quality_message}")
                                # Continue anyway, but log warning
                        
                        # Find face locations
                        face_locations = fr.face_locations(
                            rgb_image, 
                            model=Config.FACE_DETECTION_MODEL
                        )
                        
                        if not face_locations:
                            print(f"⚠️ No face found in image for {user['name']}")
                            continue
                        
                        # Use only the first face found
                        face_location = face_locations[0]
                        
                        # Check face size
                        top, right, bottom, left = face_location
                        face_width = right - left
                        face_height = bottom - top
                        
                        if (face_width < Config.MIN_FACE_SIZE or face_height < Config.MIN_FACE_SIZE or
                            face_width > Config.MAX_FACE_SIZE or face_height > Config.MAX_FACE_SIZE):
                            print(f"⚠️ Face size out of range for {user['name']}: {face_width}x{face_height}")
                            continue
                        
                        # Get face encoding
                        encodings = fr.face_encodings(rgb_image, [face_location])
                        
                        if encodings:
                            self.known_face_encodings.append(encodings[0])
                            self.known_face_names.append(user['name'])
                            self.known_face_ids.append(user['id'])
                            print(f"✅ Loaded face: {user['name']} (ID: {user['id']})")
                        else:
                            print(f"⚠️ Could not get encoding for {user['name']}")
                            
                    except Exception as e:
                        print(f"❌ Error loading face for {user['name']}: {e}")
                else:
                    print(f"❌ Image not found: {image_path}")
        
        print(f"📊 Total loaded faces: {len(self.known_face_encodings)}")
    
    def check_face_quality(self, image):
        """Check face image quality"""
        try:
            # Check brightness
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            if brightness < Config.BRIGHTNESS_THRESHOLD_LOW:
                return False, f"Image too dark (brightness: {brightness:.1f})"
            if brightness > Config.BRIGHTNESS_THRESHOLD_HIGH:
                return False, f"Image too bright (brightness: {brightness:.1f})"
            
            # Check for blur
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < Config.FACE_QUALITY_THRESHOLD:
                return False, f"Image too blurry (variance: {laplacian_var:.1f})"
            
            return True, "Good quality"
        except Exception as e:
            return False, f"Quality check error: {str(e)}"
    
    def recognize_faces(self, frame, min_confidence=None):
        """
        Improved face recognition with confidence threshold and anti-spoofing
        
        Args:
            frame: Image frame to process
            min_confidence: Minimum confidence threshold (overrides config if provided)
        """
        if min_confidence is None:
            min_confidence = Config.MIN_CONFIDENCE
        
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=Config.RESIZE_FACTOR, fy=Config.RESIZE_FACTOR)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find all faces in the current frame
        face_locations = fr.face_locations(
            rgb_small_frame, 
            model=Config.FACE_DETECTION_MODEL
        )
        face_encodings = fr.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        face_ids = []
        face_confidences = []
        
        if not face_encodings:
            return face_locations, face_names, face_ids, face_confidences
        
        for face_encoding in face_encodings:
            # Calculate distances to all known faces
            face_distances = fr.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) == 0:
                # No known faces to compare with
                name = "Unknown"
                face_id = None
                confidence = 0
            else:
                # Find the best match (lowest distance)
                best_match_index = np.argmin(face_distances)
                best_distance = face_distances[best_match_index]
                
                # Convert distance to confidence (0-1 scale)
                confidence = 1 - best_distance
                
                # Apply confidence threshold and tolerance
                if (confidence >= min_confidence and 
                    best_distance <= Config.TOLERANCE and
                    self.check_anti_spoofing(frame, face_locations[0])):
                    
                    name = self.known_face_names[best_match_index]
                    face_id = self.known_face_ids[best_match_index]
                    
                    # Check cooldown period
                    current_time = datetime.now()
                    if face_id in self.face_timestamps:
                        time_diff = (current_time - self.face_timestamps[face_id]).total_seconds()
                        if time_diff < Config.ATTENDANCE_COOLDOWN:
                            # Still in cooldown period, mark as "Recent"
                            name = f"{name} (Recent)"
                            face_id = None
                    else:
                        self.face_timestamps[face_id] = current_time
                else:
                    name = "Unknown"
                    face_id = None
                
                if Config.DEBUG_FACE_RECOGNITION:
                    print(f"🎯 Face: {name}, Distance: {best_distance:.3f}, Confidence: {confidence:.3f}")
            
            face_names.append(name)
            face_ids.append(face_id)
            face_confidences.append(confidence)
        
        # Scale back up face locations
        face_locations = [(top * 4, right * 4, bottom * 4, left * 4) 
                            for (top, right, bottom, left) in face_locations]
        
        return face_locations, face_names, face_ids, face_confidences
    
    def check_anti_spoofing(self, frame, face_location):
        """Basic anti-spoofing check (simplified version)"""
        if not Config.ENABLE_ANTI_SPOOFING:
            return True
        
        try:
            top, right, bottom, left = face_location
            face_roi = frame[top:bottom, left:right]
            
            if face_roi.size == 0:
                return False
            
            # Check if face region has reasonable color variation
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            std_dev = np.std(gray_face)
            
            # Simple check: real faces should have some texture/variation
            return std_dev > 20  # Adjust threshold as needed
            
        except Exception as e:
            print(f"Anti-spoofing check error: {e}")
            return True  # Default to true if check fails
    
    def save_unknown_face(self, frame, face_location):
        """Save unknown face for later review/training"""
        if not Config.SAVE_UNKNOWN_FACES or len(self.unknown_faces_log) >= Config.MAX_UNKNOWN_FACES:
            return
        
        try:
            top, right, bottom, left = face_location
            face_roi = frame[top:bottom, left:right]
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"unknown_{timestamp}.jpg"
            filepath = os.path.join(Config.UNKNOWN_FACES_DIR, filename)
            
            cv2.imwrite(filepath, face_roi)
            self.unknown_faces_log.append({
                'timestamp': timestamp,
                'filepath': filepath,
                'location': face_location
            })
            
            print(f"📸 Saved unknown face: {filename}")
        except Exception as e:
            print(f"Error saving unknown face: {e}")
    
    def get_unknown_faces_count(self):
        """Count how many times 'Unknown' has been detected"""
        return len(self.unknown_faces_log)
    
    def mark_attendance(self, student_id, lecture_id, faculty_id):
        """Mark attendance with validation"""
        # Check if attendance already marked today
        query = """
        SELECT id FROM attendance 
        WHERE student_id = %s AND lecture_id = %s 
        AND DATE(attendance_time) = CURDATE()
        """
        existing = db.execute_query(query, (student_id, lecture_id))
        
        if not existing:
            # Mark attendance
            query = """
            INSERT INTO attendance (student_id, lecture_id, faculty_id, status) 
            VALUES (%s, %s, %s, 'Present')
            """
            result = db.execute_query(query, (student_id, lecture_id, faculty_id))
            return result is not None
        
        return False


# ==================== INITIALIZE FACE RECOGNITION ====================
# This must come AFTER the class definition
face_recognizer = FaceRecognizer()

def send_reset_email(to_email, subject, body):
    """Send password reset email"""
    try:
        # Check if email configuration is set
        if not all([app.config.get('MAIL_SERVER'), 
                    app.config.get('MAIL_USERNAME'), 
                    app.config.get('MAIL_PASSWORD')]):
            print("Email configuration missing. Using demo mode.")
            return False
        
        # Create message - ✅ CORRECT CLASS NAMES
        msg = MIMEMultipart()
        msg['From'] = app.config.get('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME'))
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email - ✅ CORRECT CLASS NAME
        msg.attach(MIMEText(body, 'plain'))
        
        # Create server connection
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        
        # Send email
        text = msg.as_string()
        server.sendmail(msg['From'], to_email, text)
        server.quit()
        
        print(f"Password reset email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        faculty_id = request.form['faculty_id'].strip()
        
        # Check if faculty exists
        query = "SELECT id, name, email FROM faculty WHERE faculty_id = %s"
        faculty = db.execute_query(query, (faculty_id,))
        
        if faculty:
            faculty_data = faculty[0]
            
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)
            
            # Clean up old tokens
            cleanup_query = "DELETE FROM password_reset_tokens WHERE faculty_id = %s OR expires_at < %s"
            db.execute_query(cleanup_query, (faculty_data['id'], datetime.now()))
            
            # Save new token to database
            insert_query = "INSERT INTO password_reset_tokens (faculty_id, token, expires_at) VALUES (%s, %s, %s)"
            db.execute_query(insert_query, (faculty_data['id'], token, expires_at))
            
            # Create reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Try to send email
            try:
                subject = "Password Reset Request - Face Attendance System"
                body = f"""
                Dear {faculty_data['name']},
                
                You have requested to reset your password for the Face Attendance System.
                
                Faculty ID: {faculty_id}
                
                Please click the following link to reset your password:
                {reset_url}
                
                This link will expire in 1 hour.
                
                If you did not request this password reset, please ignore this email.
                
                Best regards,
                Face Attendance System
                """
                
                # Send email
                if send_reset_email(faculty_data['email'], subject, body):
                    flash('Password reset instructions have been sent to your email address.', 'success')
                else:
                    # Fallback: show link if email fails
                    flash(f'Password reset link: {reset_url}', 'warning')
                    
            except Exception as e:
                print(f"Error in password reset: {e}")
                # Fallback for development
                flash(f'Password reset link: {reset_url}', 'warning')
                
        else:
            flash('Faculty ID not found. Please check your Faculty ID.', 'error')
        
        return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Validate token
    query = """
    SELECT ft.*, f.faculty_id, f.name 
    FROM password_reset_tokens ft 
    JOIN faculty f ON ft.faculty_id = f.id 
    WHERE ft.token = %s AND ft.expires_at > %s AND ft.used = FALSE
    """
    token_data = db.execute_query(query, (token, datetime.now()))
    
    if not token_data:
        flash('Invalid or expired reset token. Please request a new reset link.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(new_password) < 4:
            flash('Password must be at least 4 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Update password
        update_query = "UPDATE faculty SET password = %s WHERE id = %s"
        result = db.execute_query(update_query, (new_password, token_data[0]['faculty_id']))
        
        if result:
            # Mark token as used
            mark_used_query = "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s"
            db.execute_query(mark_used_query, (token,))
            
            flash('Password reset successfully! You can now login with your new password.', 'success')
            return redirect(url_for('faculty_login'))
        else:
            flash('Error resetting password. Please try again.', 'error')
    
    return render_template('reset_password.html', token=token)

# ==================== ENHANCED FACULTY DASHBOARD ====================

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    db = Database() 
    
    # Get filter parameters
    selected_date = request.args.get('date', '')
    selected_lecture = request.args.get('lecture_id', '')
    
    # ✅ USE ORIGINAL WORKING QUERY (no enrolled_count)
    base_query = """
    SELECT l.id, l.lecture_code, l.title, 
            (SELECT COUNT(*) FROM attendance WHERE lecture_id = l.id AND faculty_id = %s) as attendance_count
    FROM lectures l 
    JOIN lecture_faculty lf ON l.id = lf.lecture_id 
    WHERE lf.faculty_id = %s
    """
    params = [session['faculty_id'], session['faculty_id']]
    
    # Apply filters
    if selected_date:
        base_query += " AND l.id IN (SELECT DISTINCT lecture_id FROM attendance WHERE faculty_id = %s AND DATE(attendance_time) = %s)"
        params.extend([session['faculty_id'], selected_date])
    
    if selected_lecture:
        base_query += " AND l.id = %s"
        params.append(selected_lecture)
    
    lectures = db.execute_query(base_query, params)
    
    # Pre-calculate student counts and recent attendance for each lecture
    lecture_stats = []
    for lecture in lectures:
        # Get unique student count for this lecture
        student_query = "SELECT COUNT(DISTINCT student_id) as count FROM attendance WHERE lecture_id = %s"
        if selected_date:
            student_query += " AND DATE(attendance_time) = %s"
            student_result = db.execute_query(student_query, (lecture['id'], selected_date))
        else:
            student_result = db.execute_query(student_query, (lecture['id'],))
        student_count = student_result[0]['count'] if student_result else 0
        
        # Get present today count
        present_query = "SELECT COUNT(*) as count FROM attendance WHERE lecture_id = %s AND faculty_id = %s AND DATE(attendance_time) = CURDATE() AND status = 'Present'"
        present_result = db.execute_query(present_query, (lecture['id'], session['faculty_id']))
        present_today = present_result[0]['count'] if present_result else 0
        
        # Get absent today count
        absent_query = "SELECT COUNT(*) as count FROM attendance WHERE lecture_id = %s AND faculty_id = %s AND DATE(attendance_time) = CURDATE() AND status = 'Absent'"
        absent_result = db.execute_query(absent_query, (lecture['id'], session['faculty_id']))
        absent_today = absent_result[0]['count'] if absent_result else 0
        
        # Get recent attendance for this lecture
        recent_query = """
        SELECT u.name, u.student_id, a.attendance_time 
        FROM attendance a 
        JOIN users u ON a.student_id = u.id 
        WHERE a.lecture_id = %s 
        """
        recent_params = [lecture['id']]
        
        if selected_date:
            recent_query += " AND DATE(a.attendance_time) = %s"
            recent_params.append(selected_date)
        
        recent_query += " ORDER BY a.attendance_time DESC LIMIT 3"
        recent_attendance = db.execute_query(recent_query, recent_params)
        
        lecture_stats.append({
            'id': lecture['id'],
            'lecture_code': lecture['lecture_code'],
            'title': lecture['title'],
            'attendance_count': lecture['attendance_count'],
            'student_count': student_count,
            'present_today': present_today,
            'absent_today': absent_today,
            'recent_attendance': recent_attendance
        })
    
    # Calculate total students across all lectures
    total_students_query = """
    SELECT COUNT(DISTINCT student_id) as count 
    FROM attendance 
    WHERE faculty_id = %s
    """
    if selected_date:
        total_students_query += " AND DATE(attendance_time) = %s"
        total_students_result = db.execute_query(total_students_query, (session['faculty_id'], selected_date))
    else:
        total_students_result = db.execute_query(total_students_query, (session['faculty_id'],))
    total_students = total_students_result[0]['count'] if total_students_result else 0
    
    # Calculate total attendance records
    total_attendance_query = """
    SELECT COUNT(*) as count 
    FROM attendance 
    WHERE faculty_id = %s
    """
    if selected_date:
        total_attendance_query += " AND DATE(attendance_time) = %s"
        total_attendance_result = db.execute_query(total_attendance_query, (session['faculty_id'], selected_date))
    else:
        total_attendance_result = db.execute_query(total_attendance_query, (session['faculty_id'],))
    total_attendance = total_attendance_result[0]['count'] if total_attendance_result else 0
    
    # Calculate today's attendance
    today_attendance_query = """
    SELECT COUNT(*) as count 
    FROM attendance 
    WHERE faculty_id = %s AND DATE(attendance_time) = CURDATE()
    """
    today_attendance_result = db.execute_query(today_attendance_query, (session['faculty_id'],))
    today_attendance = today_attendance_result[0]['count'] if today_attendance_result else 0
    
    # Get class-wise attendance summary
    attendance_summary_query = """
    SELECT l.id as lecture_id, l.lecture_code, l.title,
            COUNT(DISTINCT a.student_id) as total_students,
            SUM(CASE WHEN DATE(a.attendance_time) = CURDATE() THEN 1 ELSE 0 END) as present_today,
            CASE 
                WHEN COUNT(DISTINCT a.student_id) > 0 THEN 
                    ROUND((SUM(CASE WHEN DATE(a.attendance_time) = CURDATE() THEN 1 ELSE 0 END) / 
                   COUNT(DISTINCT a.student_id)) * 100, 2)
                ELSE 0 
            END as attendance_percentage
    FROM lectures l
    LEFT JOIN attendance a ON l.id = a.lecture_id AND a.faculty_id = %s
    WHERE l.id IN (SELECT lecture_id FROM lecture_faculty WHERE faculty_id = %s)
    GROUP BY l.id, l.lecture_code, l.title
    """
    attendance_summary = db.execute_query(attendance_summary_query, (session['faculty_id'], session['faculty_id']))
    
    # Get all lectures for filter dropdown
    all_lectures_query = """
    SELECT l.id, l.lecture_code, l.title
    FROM lectures l
    JOIN lecture_faculty lf ON l.id = lf.lecture_id
    WHERE lf.faculty_id = %s
    ORDER BY l.lecture_code
    """
    all_lectures = db.execute_query(all_lectures_query, (session['faculty_id'],))
    
    return render_template('faculty_dashboard.html', 
                         lectures=lecture_stats, 
                         faculty_name=session['faculty_name'],
                         total_students=total_students,
                         total_attendance=total_attendance,
                         today_attendance=today_attendance,
                         attendance_summary=attendance_summary,
                         all_lectures=all_lectures,
                         selected_date=selected_date,
                         selected_lecture=selected_lecture)

# ==================== UPDATED FACULTY LOGIN WITH FLASH MESSAGES ====================
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('faculty_login'))

@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if 'faculty_id' in session:
        return redirect(url_for('faculty_dashboard'))  # user already logged in
    
    if request.method == 'POST':
        faculty_id = request.form['faculty_id']
        password = request.form['password']
        
        query = "SELECT id, name FROM faculty WHERE faculty_id = %s AND password = %s"
        faculty = db.execute_query(query, (faculty_id, password))
        
        if faculty:
            session['faculty_id'] = faculty[0]['id']
            session['faculty_name'] = faculty[0]['name']
            session['user_type'] = 'faculty'
            return redirect(url_for('faculty_dashboard'))
        else:
            flash('Invalid faculty ID or password', 'error')
    
    return render_template('faculty_login.html')



def mark_absentees_for_lecture(lecture_id, faculty_id):
    """
    PERFECT ABSENCE LOGIC: Marks ALL students as either Present or Absent
    """
    db = Database()
    
    try:
        # 1. Get ALL students from database
        all_students = db.execute_query("SELECT id, student_id, name FROM users")
        
        if not all_students:
            return "No students found in database."
        
        print(f"📋 Total students in database: {len(all_students)}")
        
        # 2. Get students marked present TODAY for this lecture
        present_students = db.execute_query("""
            SELECT DISTINCT student_id 
            FROM attendance 
            WHERE lecture_id = %s 
            AND faculty_id = %s
            AND DATE(attendance_time) = CURDATE()
            AND status = 'Present'
        """, (lecture_id, faculty_id)) or []
        
        present_ids = [p['student_id'] for p in present_students]
        print(f"✅ Present students today: {len(present_ids)}")
        print(f"✅ Present student IDs: {present_ids}")
        
        # 3. Mark ALL students who are NOT present as ABSENT
        absent_count = 0
        today = datetime.now().date()
        
        for student in all_students:
            if student['id'] not in present_ids:
                # Student was NOT recognized - mark as absent
                # Check if absent already marked today (avoid duplicates)
                existing_absent = db.execute_query("""
                    SELECT id FROM attendance 
                    WHERE student_id = %s 
                    AND lecture_id = %s 
                    AND DATE(attendance_time) = %s
                    AND status = 'Absent'
                """, (student['id'], lecture_id, today))
                
                if not existing_absent:
                    # Mark as absent
                    result = db.execute_query("""
                        INSERT INTO attendance 
                        (student_id, lecture_id, faculty_id, attendance_time, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (student['id'], lecture_id, faculty_id, datetime.now(), 'Absent'))
                    
                    if result:
                        absent_count += 1
                        print(f"❌ Marked absent: {student['name']} (ID: {student['id']})")
                else:
                    # Already marked absent
                    absent_count += 1
                    print(f"❌ Already absent: {student['name']} (ID: {student['id']})")
            else:
                print(f"✅ Already present: {student['name']} (ID: {student['id']})")
        
        total_students = len(all_students)
        present_count = len(present_ids)
        
        print(f"📊 FINAL SUMMARY: {present_count} present, {absent_count} absent out of {total_students} total students")
        
        return f"✅ Attendance completed! {present_count} present, {absent_count} absent out of {total_students} total students"
        
    except Exception as e:
        print(f"❌ Error in mark_absentees_for_lecture: {e}")
        return f"Error: {str(e)}"
             
@app.route('/debug_students')
def debug_students():
    """Debug route to see all students and their status"""
    try:
        # Get all students
        all_students = db.execute_query("SELECT id, student_id, name FROM users ORDER BY id")
        
        if not all_students:
            return jsonify({'error': 'No students found in database'})
        
        # Get today's attendance for a specific lecture (change lecture_id as needed)
        lecture_id = 1  # Change this to your actual lecture ID
        today_attendance = db.execute_query("""
            SELECT u.id, u.student_id, u.name, a.status, a.attendance_time
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            WHERE a.lecture_id = %s 
            AND DATE(a.attendance_time) = CURDATE()
            ORDER BY u.id
        """, (lecture_id,)) or []
        
        # ✅ CORRECTED: Fixed the syntax error - removed space
        attendance_map = {student['id']: 'No Record' for student in all_students}
        
        for record in today_attendance:
            attendance_map[record['id']] = record['status']
        
        return jsonify({
            'total_students': len(all_students),
            'students': all_students,
            'today_attendance': today_attendance,
            'attendance_summary': attendance_map,
            'summary': {
                'present_count': len([r for r in today_attendance if r['status'] == 'Present']),
                'absent_count': len([r for r in today_attendance if r['status'] == 'Absent']),
                'no_record_count': len([s for s in all_students if attendance_map[s['id']] == 'No Record'])
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})
    

@app.route('/check_database')
def check_database():
    """Simple route to check database content"""
    # Check students
    students = db.execute_query("SELECT COUNT(*) as count FROM users")
    # Check lectures
    lectures = db.execute_query("SELECT id, lecture_code, title FROM lectures")
    # Check today's attendance
    today_records = db.execute_query("""
        SELECT COUNT(*) as count, status 
        FROM attendance 
        WHERE DATE(attendance_time) = CURDATE() 
        GROUP BY status
    """)
    
    return jsonify({
        'total_students': students[0]['count'] if students else 0,
        'lectures': lectures,
        'today_attendance': today_records
    })

@app.route('/enroll_students/<lecture_id>', methods=['GET', 'POST'])
def enroll_students(lecture_id):
    """Manage student enrollment for a lecture"""
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    # Verify faculty access
    access = db.execute_query(
        "SELECT id FROM lecture_faculty WHERE lecture_id = %s AND faculty_id = %s",
        (lecture_id, session['faculty_id'])
    )
    if not access:
        return "Access denied", 403
    
    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        action = request.form.get('action')  # 'enroll' or 'remove'
        
        for student_id in student_ids:
            if action == 'enroll':
                db.execute_query("""
                    INSERT IGNORE INTO lecture_students (lecture_id, student_id)
                    VALUES (%s, %s)
                """, (lecture_id, student_id))
            elif action == 'remove':
                db.execute_query("""
                    DELETE FROM lecture_students 
                    WHERE lecture_id = %s AND student_id = %s
                """, (lecture_id, student_id))
        
        flash(f'Students {action}ed successfully!', 'success')
        return redirect(url_for('enroll_students', lecture_id=lecture_id))
    
    # Get lecture details
    lecture = db.execute_query(
        "SELECT lecture_code, title FROM lectures WHERE id = %s", 
        (lecture_id,)
    )[0]
    
    # Get all students
    all_students = db.execute_query(
        "SELECT id, student_id, name FROM users ORDER BY name"
    )
    
    # Get enrolled students
    enrolled_students = db.execute_query("""
        SELECT u.id, u.student_id, u.name 
        FROM lecture_students ls
        JOIN users u ON ls.student_id = u.id
        WHERE ls.lecture_id = %s
    """, (lecture_id,))
    
    enrolled_ids = [s['id'] for s in enrolled_students]
    
    return render_template('enroll_students.html',
                            lecture=lecture,
                            all_students=all_students,
                            enrolled_students=enrolled_students,
                            enrolled_ids=enrolled_ids)

@app.route('/auto_enroll_from_attendance/<lecture_id>')
def auto_enroll_from_attendance(lecture_id):
    """Automatically enroll students who have attended this lecture"""
    if 'faculty_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    # Get students who have attended this lecture but aren't enrolled
    students_to_enroll = db.execute_query("""
        SELECT DISTINCT a.student_id 
        FROM attendance a
        LEFT JOIN lecture_students ls ON a.student_id = ls.student_id AND ls.lecture_id = %s
        WHERE a.lecture_id = %s AND ls.student_id IS NULL
    """, (lecture_id, lecture_id))
    
    enrolled_count = 0
    for student in students_to_enroll:
        result = db.execute_query("""
            INSERT IGNORE INTO lecture_students (lecture_id, student_id)
            VALUES (%s, %s)
        """, (lecture_id, student['student_id']))
        if result:
            enrolled_count += 1
    
    return jsonify({
        'success': True,
        'message': f'Automatically enrolled {enrolled_count} students from attendance records'
    })
@app.route('/debug_attendance_status/<lecture_id>')
def debug_attendance_status(lecture_id):
    """Check current attendance status for a lecture"""
    if 'faculty_id' not in session:
        return "Not authorized"
    
    # Get all students
    all_students = db.execute_query("SELECT id, student_id, name FROM users")
    
    # Get present students today
    present_today = db.execute_query("""
        SELECT u.id, u.student_id, u.name, a.attendance_time
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        WHERE a.lecture_id = %s 
        AND a.faculty_id = %s
        AND DATE(a.attendance_time) = CURDATE()
        AND a.status = 'Present'
    """, (lecture_id, session['faculty_id']))
    
    # Get absent students today  
    absent_today = db.execute_query("""
        SELECT u.id, u.student_id, u.name, a.attendance_time
        FROM attendance a
        JOIN users u ON a.student_id = u.id
        WHERE a.lecture_id = %s 
        AND a.faculty_id = %s
        AND DATE(a.attendance_time) = CURDATE()
        AND a.status = 'Absent'
    """, (lecture_id, session['faculty_id']))
    
    present_ids = [s['id'] for s in present_today]
    absent_ids = [s['id'] for s in absent_today]
    
    # Find students with no attendance record today
    no_record = [s for s in all_students if s['id'] not in present_ids and s['id'] not in absent_ids]
    
    return jsonify({
        'total_students': len(all_students),
        'present_today': present_today,
        'absent_today': absent_today, 
        'no_record_today': no_record,
        'summary': {
            'present_count': len(present_today),
            'absent_count': len(absent_today),
            'no_record_count': len(no_record),
            'total_count': len(all_students)
        }
    })
# ==================== UPDATED VIEW ATTENDANCE WITH DATE FILTERING ====================

@app.route('/view_attendance/<lecture_id>')
def view_attendance(lecture_id):
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    # Verify faculty has access to this lecture
    query = "SELECT id FROM lecture_faculty WHERE lecture_id = %s AND faculty_id = %s"
    access = db.execute_query(query, (lecture_id, session['faculty_id']))
    
    if not access:
        return "Access denied", 403
    
    # Get date filter
    selected_date = request.args.get('date', '')
    
    # Get attendance records for this lecture
    query = """
    SELECT u.student_id, u.name, a.attendance_time, a.status
    FROM attendance a
    JOIN users u ON a.student_id = u.id
    WHERE a.lecture_id = %s
    """
    params = [lecture_id]
    
    if selected_date:
        query += " AND DATE(a.attendance_time) = %s"
        params.append(selected_date)
    
    query += " ORDER BY a.attendance_time DESC"
    records = db.execute_query(query, params)
    
    # Get lecture details
    lecture_query = "SELECT lecture_code, title FROM lectures WHERE id = %s"
    lecture = db.execute_query(lecture_query, (lecture_id,))
    
    if lecture:
        return render_template('lecture_attendance.html', 
                                records=records, 
                                lecture_code=lecture[0]['lecture_code'],
                                lecture_title=lecture[0]['title'],
                                selected_date=selected_date)
    else:
        return "Lecture not found", 404

# ==================== EXISTING ROUTES (UNCHANGED) ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        
        # Save photo
        photo = request.files['photo']
        if photo:
            filename = f"{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            photo_path = os.path.join(Config.KNOWN_FACES_DIR, filename)
            photo.save(photo_path)
            
            # Save to database
            query = "INSERT INTO users (student_id, name, email, photo_path) VALUES (%s, %s, %s, %s)"
            result = db.execute_query(query, (student_id, name, email, filename))
            
            if result:
                # Reload known faces
                face_recognizer.load_known_faces()
                return redirect(url_for('register_success'))
    
    return render_template('register.html')

@app.route('/register_success')
def register_success():
    return render_template('register_success.html')

@app.route('/take_attendance', methods=['GET', 'POST'])
def take_attendance():
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    if request.method == 'POST':
        lecture_id = request.form['lecture_id']
        # This would be handled by JavaScript capturing and processing the image
        
    # Get lectures for this faculty
    query = """
    SELECT l.id, l.lecture_code, l.title 
    FROM lectures l 
    JOIN lecture_faculty lf ON l.id = lf.lecture_id 
    WHERE lf.faculty_id = %s
    """
    lectures = db.execute_query(query, (session['faculty_id'],))
    
    return render_template('attendance.html', lectures=lectures)

@app.route('/process_attendance', methods=['POST'])
def process_attendance():
    if 'faculty_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    # Get data from request
    data = request.get_json()
    student_id = data.get('student_id')
    lecture_id = data.get('lecture_id')
    
    # Debug print to see what data we're receiving
    print(f"Processing attendance: student_id={student_id}, lecture_id={lecture_id}, faculty_id={session['faculty_id']}")
    
    # Validate inputs
    if not student_id or not lecture_id:
        return jsonify({'success': False, 'message': 'Missing student_id or lecture_id'})
    
    # Mark attendance
    success = face_recognizer.mark_attendance(student_id, lecture_id, session['faculty_id'])
    
    if success:
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    else:
        return jsonify({'success': False, 'message': 'Attendance already marked or database error'})

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        email = request.form['email']
        
        query = "SELECT id, name FROM users WHERE student_id = %s AND email = %s"
        student = db.execute_query(query, (student_id, email))
        
        if student:
            session['student_id'] = student[0]['id']
            session['student_name'] = student[0]['name']
            session['user_type'] = 'student'
            # Redirect to dashboard on success
            return redirect(url_for('student_dashboard'))
        else:
            # Use flash to store an error message
            flash('Invalid Student ID or Email. Please try again.', 'error')
            # It's good practice to return to the login page on failure
            return redirect(url_for('student_login'))  # This ensures a fresh GET request
    
    # This handles the GET request (initial page load or redirect after failed login)
    return render_template('student_login.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    # Get student's attendance summary
    query = """
    SELECT l.lecture_code, l.title, 
           COUNT(a.id) as total_classes,
           SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended_classes,
           ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.id)) * 100, 2) as attendance_percentage
    FROM attendance a
    JOIN lectures l ON a.lecture_id = l.id
    WHERE a.student_id = %s
    GROUP BY l.id
    """
    attendance_summary = db.execute_query(query, (session['student_id'],))

    # Get recent attendance records for chart
    recent_query = """
    SELECT l.lecture_code, l.title, 
           a.attendance_time,
           a.status
    FROM attendance a
    JOIN lectures l ON a.lecture_id = l.id
    WHERE a.student_id = %s
    ORDER BY a.attendance_time DESC
    LIMIT 10
    """
    recent_records = db.execute_query(recent_query, (session['student_id'],))
    chart_labels = [item['lecture_code'] for item in attendance_summary] if attendance_summary else []
    chart_values = [item['attendance_percentage'] for item in attendance_summary] if attendance_summary else []

    return render_template('student_dashboard.html',
                            student_name=session['student_name'],
                            attendance_summary=attendance_summary,
                            recent_records=recent_records,
                            chart_labels=chart_labels,
                            chart_values=chart_values)
    
    return render_template('student_dashboard.html', 
                            student_name=session['student_name'], 
                            attendance_summary=attendance_summary,
                            recent_records=recent_records)  # This line is IMPORTANT

@app.route('/get_statistics')
def get_statistics():
    # Get statistics for the dashboard
    students = db.execute_query("SELECT COUNT(*) as count FROM users")
    lectures = db.execute_query("SELECT COUNT(*) as count FROM lectures")
    attendance = db.execute_query("SELECT COUNT(*) as count FROM attendance")
    faculty = db.execute_query("SELECT COUNT(*) as count FROM faculty")
    
    return jsonify({
        'students': students[0]['count'] if students else 0,
        'lectures': lectures[0]['count'] if lectures else 0,
        'attendance': attendance[0]['count'] if attendance else 0,
        'faculty': faculty[0]['count'] if faculty else 0
    })


@app.route('/progress_report')
def progress_report():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    # Get detailed attendance report
    query = """
    SELECT l.lecture_code, l.title, 
           DATE(a.attendance_time) as date,
           a.status,
           f.name as faculty_name
    FROM attendance a
    JOIN lectures l ON a.lecture_id = l.id
    JOIN faculty f ON a.faculty_id = f.id
    WHERE a.student_id = %s
    ORDER BY a.attendance_time DESC
    """
    records = db.execute_query(query, (session['student_id'],))

    return render_template(
        'progress_report.html',
        student_name=session['student_name'],
        records=records
    )



@app.route('/recognize_faces', methods=['POST'])
def recognize_faces():

    # Check if image is present
    if 'image' not in request.files:
        return jsonify([])

    # Create temp directory
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Save the uploaded frame
    image_file = request.files['image']
    temp_path = os.path.join(temp_dir, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.jpg")
    image_file.save(temp_path)

    try:
        # Read image
        image = fr.load_image_file(temp_path)
        face_locations = fr.face_locations(image)
        face_encodings = fr.face_encodings(image, face_locations)

        recognized_faces = []

        for face_encoding, face_location in zip(face_encodings, face_locations):

            # Compare with known encodings
            matches = fr.compare_faces(
                face_recognizer.known_face_encodings,
                face_encoding,
                tolerance=Config.TOLERANCE
            )

            name = "Unknown"
            face_id = None

            if True in matches:
                matched_index = matches.index(True)
                name = face_recognizer.known_face_names[matched_index]
                face_id = face_recognizer.known_face_ids[matched_index]

            # Convert to int safely
            if face_id is not None:
                try:
                    face_id = int(face_id)
                except:
                    pass  # If ID is string name, leave it

            # Convert face_location
            top, right, bottom, left = face_location

            # Append response object
            recognized_faces.append({
                "id": face_id,
                "name": name,
                "x": left,
                "y": top,
                "width": right - left,
                "height": bottom - top
            })

        return jsonify(recognized_faces)

    except Exception as e:
        print("Error in face recognition:", e)
        return jsonify([])

    finally:
        # Remove temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)



@app.route('/take_attendance_new')
def take_attendance_new():
    """NEW perfect attendance page"""
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    # Get lectures for this faculty
    query = """
    SELECT l.id, l.lecture_code, l.title 
    FROM lectures l 
    JOIN lecture_faculty lf ON l.id = lf.lecture_id 
    WHERE lf.faculty_id = %s
    """
    lectures = db.execute_query(query, (session['faculty_id'],))
    
    return render_template('attendance_new.html', lectures=lectures)

@app.route('/process_attendance_simple', methods=['POST'])
def process_attendance_simple():
    """Simple attendance processing"""
    if 'faculty_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        lecture_id = data.get('lecture_id')
        
        print(f"Processing attendance - Student: {student_id}, Lecture: {lecture_id}")
        
        # Simple attendance marking
        query = """
        INSERT INTO attendance (student_id, lecture_id, faculty_id, status) 
        VALUES (%s, %s, %s, 'Present')
        """
        result = db.execute_query(query, (student_id, lecture_id, session['faculty_id']))
        
        if result:
            return jsonify({'success': True, 'message': 'Attendance marked'})
        else:
            return jsonify({'success': False, 'message': 'Database error'})
            
    except Exception as e:
        print(f"Attendance error: {e}")
        return jsonify({'success': False, 'message': str(e)}) 
    # ==================== REAL-TIME FACE RECOGNITION ROUTES ====================

@app.route('/take_attendance_realtime')
def take_attendance_realtime():
    """Real-time face recognition attendance"""
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    # Get lectures for this faculty
    query = """
    SELECT l.id, l.lecture_code, l.title 
    FROM lectures l 
    JOIN lecture_faculty lf ON l.id = lf.lecture_id 
    WHERE lf.faculty_id = %s
    """
    lectures = db.execute_query(query, (session['faculty_id'],))
    
    return render_template('attendance_realtime.html', lectures=lectures)

@app.route('/mark_attendance_realtime', methods=['POST'])
def mark_attendance_realtime():
    """Mark attendance for recognized faces in real-time"""
    if 'faculty_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        lecture_id = data.get('lecture_id')
        student_name = data.get('student_name')
        
        print(f"Real-time attendance - Student: {student_name} ({student_id}), Lecture: {lecture_id}")
        
        # Check if already marked today
        check_query = """
        SELECT id FROM attendance 
        WHERE student_id = %s AND lecture_id = %s 
        AND DATE(attendance_time) = CURDATE()
        """
        existing = db.execute_query(check_query, (student_id, lecture_id))
        
        if existing:
            return jsonify({
                'success': False, 
                'message': f'Attendance already marked for {student_name}',
                'already_marked': True
            })
        
        # Mark attendance
        insert_query = """
        INSERT INTO attendance (student_id, lecture_id, faculty_id, status) 
        VALUES (%s, %s, %s, 'Present')
        """
        result = db.execute_query(insert_query, (student_id, lecture_id, session['faculty_id']))
        
        if result:
            return jsonify({
                'success': True, 
                'message': f'Attendance marked for {student_name}',
                'student_name': student_name
            })
        else:
            return jsonify({'success': False, 'message': 'Database error'})
            
    except Exception as e:
        print(f"Real-time attendance error: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ==================== EXISTING ROUTES CONTINUE BELOW ====================
# Make sure all your existing routes continue here with proper indentation
@app.route('/registered_users')
def registered_users():
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    users = db.execute_query("SELECT student_id, name, email, created_at FROM users ORDER BY created_at DESC")
    return render_template('registered_users.html', users=users)

@app.route('/manage_lectures')
def manage_lectures():
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    # Get all lectures
    lectures = db.execute_query("SELECT id, lecture_code, title, description FROM lectures")
    
    # Get lectures assigned to this faculty with faculty info
    faculty_lectures_query = """
    SELECT l.id, l.lecture_code, l.title, l.description, 
           f.name as faculty_name, f.id as faculty_id,
           (SELECT COUNT(*) FROM attendance WHERE lecture_id = l.id) as attendance_count
    FROM lectures l 
    JOIN lecture_faculty lf ON l.id = lf.lecture_id 
    JOIN faculty f ON lf.faculty_id = f.id
    WHERE lf.faculty_id = %s
    """
    faculty_lectures = db.execute_query(faculty_lectures_query, (session['faculty_id'],))
    
    # Get faculty info for all lectures
    all_lectures_faculty_query = """
    SELECT lf.lecture_id, f.name as faculty_name 
    FROM lecture_faculty lf 
    JOIN faculty f ON lf.faculty_id = f.id
    """
    all_faculty_assignments = db.execute_query(all_lectures_faculty_query)
    
    return render_template('manage_lectures.html', 
                         lectures=lectures, 
                         faculty_lectures=faculty_lectures,
                         all_faculty_assignments=all_faculty_assignments)

@app.route('/add_lecture', methods=['POST'])
def add_lecture():
    if 'faculty_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    lecture_code = request.form.get('lecture_code')
    title = request.form.get('title')
    description = request.form.get('description')
    
    # Check if lecture code already exists
    existing = db.execute_query("SELECT id FROM lectures WHERE lecture_code = %s", (lecture_code,))
    if existing:
        return jsonify({'success': False, 'message': 'Lecture code already exists'})
    
    # Add new lecture
    query = "INSERT INTO lectures (lecture_code, title, description) VALUES (%s, %s, %s)"
    result = db.execute_query(query, (lecture_code, title, description))
    
    if result:
        # Automatically assign to the faculty who created it
        assign_query = "INSERT INTO lecture_faculty (lecture_id, faculty_id) VALUES (%s, %s)"
        db.execute_query(assign_query, (result, session['faculty_id']))
        
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Database error'})

@app.route('/get_attendance_data/<lecture_id>')
def get_attendance_data(lecture_id):
    if 'faculty_id' not in session:
        return jsonify({'error': 'Not authorized'})
    
    # Verify faculty has access to this lecture
    query = "SELECT id FROM lecture_faculty WHERE lecture_id = %s AND faculty_id = %s"
    access = db.execute_query(query, (lecture_id, session['faculty_id']))
    
    if not access:
        return jsonify({'error': 'Access denied'})
    
    # Get attendance data for chart
    query = """
    SELECT DATE(attendance_time) as date, COUNT(*) as count 
    FROM attendance 
    WHERE lecture_id = %s 
    GROUP BY DATE(attendance_time) 
    ORDER BY date
    """
    data = db.execute_query(query, (lecture_id,))
    
    return jsonify(data)

@app.route("/end_attendance/<int:lecture_id>")
def end_attendance(lecture_id):
    # Faculty must be logged in
    if "faculty_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("faculty_login"))

    faculty_id = session["faculty_id"]
    message = mark_absentees_for_lecture(lecture_id, faculty_id)
    flash(message, "success")
    return redirect(url_for("faculty_dashboard"))

def mark_absentees_for_lecture(lecture_id, faculty_id):
    conn = None   # ✅ Initialize first

    try:
        # ✅ Connect to your actual database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # add if you have
            database="face_attendance_db"
        )
        cursor = conn.cursor(dictionary=True)

        # ✅ Get all students
        cursor.execute("SELECT id, student_id, name FROM users")
        all_students = cursor.fetchall()

        # ✅ Get students who are already present for this lecture
        cursor.execute("""
            SELECT student_id FROM attendance 
            WHERE lecture_id = %s AND faculty_id = %s AND status = 'Present'
        """, (lecture_id, faculty_id))
        present_students = [row['student_id'] for row in cursor.fetchall()]

        # ✅ Mark absent for others
        absent_count = 0
        for student in all_students:
            if student['id'] not in present_students:
                cursor.execute("""
                    INSERT INTO attendance (student_id, lecture_id, faculty_id, attendance_time, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (student['id'], lecture_id, faculty_id, datetime.now(), 'Absent'))
                absent_count += 1

        conn.commit()
        return f"{absent_count} students marked as Absent."

    except mysql.connector.Error as err:
        print("Database error:", err)
        return f"Error: {err}"

    finally:
        # ✅ Close connection safely
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@app.route('/get_student_attendance/<student_id>')
def get_student_attendance(student_id):
    if 'faculty_id' not in session and ('student_id' not in session or session['student_id'] != int(student_id)):
        return jsonify({'error': 'Not authorized'})
    
    # Get student attendance summary
    query = """
    SELECT l.lecture_code, l.title, 
           COUNT(a.id) as total_classes,
           SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended_classes,
           ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.id)) * 100, 2) as attendance_percentage
    FROM attendance a
    JOIN lectures l ON a.lecture_id = l.id
    WHERE a.student_id = %s
    GROUP BY l.id
    """
    data = db.execute_query(query, (student_id,))
    
    return jsonify(data)

@app.route('/dashboard')
def dashboard():
    # This is the main admin dashboard
    if 'user_type' not in session:
        return redirect(url_for('index'))
    
    return render_template('dashboard.html')

@app.route('/view_records')
def view_records():
    if 'user_type' not in session:
        return redirect(url_for('index'))
    
    # Get all attendance records with related information
    query = """
    SELECT a.id, a.attendance_time, a.status,
           u.name as student_name, u.student_id,
           l.lecture_code, l.title as lecture_title,
           f.name as faculty_name
    FROM attendance a
    JOIN users u ON a.student_id = u.id
    JOIN lectures l ON a.lecture_id = l.id
    JOIN faculty f ON a.faculty_id = f.id
    ORDER BY a.attendance_time DESC
    LIMIT 100
    """
    records = db.execute_query(query)
    
    # Get filter options
    lectures = db.execute_query("SELECT id, lecture_code, title FROM lectures ORDER BY lecture_code")
    students = db.execute_query("SELECT id, name, student_id FROM users ORDER BY name")
    faculty_members = db.execute_query("SELECT id, name, faculty_id FROM faculty ORDER BY name")
    
    return render_template('view_records.html', 
                         records=records, 
                         lectures=lectures,
                         students=students,
                         faculty_members=faculty_members)

@app.route('/filter_records')
def filter_records():
    if 'user_type' not in session:
        return jsonify({'error': 'Not authorized'})
    
    # Get filter parameters
    lecture_id = request.args.get('lecture_filter')
    student_id = request.args.get('student_filter')
    faculty_id = request.args.get('faculty_filter')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status_filter')
    
    # Build query with filters
    query = """
    SELECT a.id, a.attendance_time, a.status,
           u.name as student_name, u.student_id,
           l.lecture_code, l.title as lecture_title,
           f.name as faculty_name
    FROM attendance a
    JOIN users u ON a.student_id = u.id
    JOIN lectures l ON a.lecture_id = l.id
    JOIN faculty f ON a.faculty_id = f.id
    WHERE 1=1
    """
    params = []
    
    if lecture_id:
        query += " AND l.id = %s"
        params.append(lecture_id)
    
    if student_id:
        query += " AND u.id = %s"
        params.append(student_id)
    
    if faculty_id:
        query += " AND f.id = %s"
        params.append(faculty_id)
    
    if date_from:
        query += " AND DATE(a.attendance_time) >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(a.attendance_time) <= %s"
        params.append(date_to)
    
    if status:
        query += " AND a.status = %s"
        params.append(status)
    
    query += " ORDER BY a.attendance_time DESC LIMIT 100"
    
    records = db.execute_query(query, params)
    return jsonify({'records': records})

@app.route('/get_record_details/<record_id>')
def get_record_details(record_id):
    if 'user_type' not in session:
        return jsonify({'error': 'Not authorized'})
    
    query = """
    SELECT a.id, a.attendance_time, a.status,
           u.name as student_name, u.student_id,
           l.lecture_code, l.title as lecture_title,
           f.name as faculty_name
    FROM attendance a
    JOIN users u ON a.student_id = u.id
    JOIN lectures l ON a.lecture_id = l.id
    JOIN faculty f ON a.faculty_id = f.id
    WHERE a.id = %s
    """
    record = db.execute_query(query, (record_id,))
    
    if record:
        return jsonify(record[0])
    else:
        return jsonify({'error': 'Record not found'})

@app.route('/update_lecture', methods=['POST'])
def update_lecture():
    if 'faculty_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    lecture_id = request.form.get('lecture_id')
    lecture_code = request.form.get('lecture_code')
    title = request.form.get('title')
    description = request.form.get('description')
    
    # Check if lecture code already exists (excluding current lecture)
    existing_query = "SELECT id FROM lectures WHERE lecture_code = %s AND id != %s"
    existing = db.execute_query(existing_query, (lecture_code, lecture_id))
    
    if existing:
        return jsonify({'success': False, 'message': 'Lecture code already exists'})
    
    # Update lecture
    query = "UPDATE lectures SET lecture_code = %s, title = %s, description = %s WHERE id = %s"
    result = db.execute_query(query, (lecture_code, title, description, lecture_id))
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Database error'})

@app.route('/delete_lecture/<lecture_id>', methods=['DELETE'])
def delete_lecture(lecture_id):
    if 'faculty_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    # First delete from lecture_faculty table
    delete_faculty_query = "DELETE FROM lecture_faculty WHERE lecture_id = %s"
    db.execute_query(delete_faculty_query, (lecture_id,))
    
    # Then delete from attendance table
    delete_attendance_query = "DELETE FROM attendance WHERE lecture_id = %s"
    db.execute_query(delete_attendance_query, (lecture_id,))
    
    # Finally delete the lecture
    delete_lecture_query = "DELETE FROM lectures WHERE id = %s"
    result = db.execute_query(delete_lecture_query, (lecture_id,))
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Database error'})

@app.route('/update_record', methods=['POST'])
def update_record():
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    record_id = request.form.get('record_id')
    status = request.form.get('status')
    datetime_str = request.form.get('datetime')
    
    query = "UPDATE attendance SET status = %s, attendance_time = %s WHERE id = %s"
    result = db.execute_query(query, (status, datetime_str, record_id))
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Database error'})

@app.route('/delete_record/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    if 'user_type' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    query = "DELETE FROM attendance WHERE id = %s"
    result = db.execute_query(query, (record_id,))
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Database error'})

@app.route('/export_records')
def export_records():
    if 'user_type' not in session:
        return redirect(url_for('index'))
    
    # Get filter parameters
    lecture_id = request.args.get('lecture')
    student_id = request.args.get('student')
    faculty_id = request.args.get('faculty')
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    status = request.args.get('status')
    
    # Build query with filters
    query = """
    SELECT a.attendance_time, a.status,
           u.name as student_name, u.student_id,
           l.lecture_code, l.title as lecture_title,
           f.name as faculty_name
    FROM attendance a
    JOIN users u ON a.student_id = u.id
    JOIN lectures l ON a.lecture_id = l.id
    JOIN faculty f ON a.faculty_id = f.id
    WHERE 1=1
    """
    params = []
    
    if lecture_id:
        query += " AND l.id = %s"
        params.append(lecture_id)
    
    if student_id:
        query += " AND u.id = %s"
        params.append(student_id)
    
    if faculty_id:
        query += " AND f.id = %s"
        params.append(faculty_id)
    
    if date_from:
        query += " AND DATE(a.attendance_time) >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(a.attendance_time) <= %s"
        params.append(date_to)
    
    if status:
        query += " AND a.status = %s"
        params.append(status)
    
    query += " ORDER BY a.attendance_time DESC"
    
    records = db.execute_query(query, params)
    
    # Create CSV content
    csv_content = "Date,Student Name,Student ID,Lecture Code,Lecture Title,Faculty,Status\n"
    for record in records:
        csv_content += f"\"{record['attendance_time']}\",\"{record['student_name']}\",\"{record['student_id']}\",\"{record['lecture_code']}\",\"{record['lecture_title']}\",\"{record['faculty_name']}\",\"{record['status']}\"\n"
    
    # Create response with CSV file
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = "attachment; filename=attendance_records.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response

# ==================== DEBUG ROUTES ====================
@app.route('/debug/student/<student_id>')
def debug_student(student_id):
    """Debug route to check if a student exists"""
    query = "SELECT id, student_id, name FROM users WHERE id = %s OR student_id = %s"
    student = db.execute_query(query, (student_id, student_id))
    return jsonify({'student': student})

@app.route('/debug/lecture/<lecture_id>')
def debug_lecture(lecture_id):
    """Debug route to check if a lecture exists"""
    query = "SELECT id, lecture_code, title FROM lectures WHERE id = %s"
    lecture = db.execute_query(query, (lecture_id,))
    return jsonify({'lecture': lecture})

@app.route('/debug/attendance')
def debug_attendance():
    """Debug route to check recent attendance records"""
    query = """
    SELECT a.id, a.attendance_time, a.status, 
           u.student_id, u.name as student_name,
           l.lecture_code, l.title as lecture_title
    FROM attendance a
    JOIN users u ON a.student_id = u.id
    JOIN lectures l ON a.lecture_id = l.id
    ORDER BY a.attendance_time DESC
    LIMIT 10
    """
    records = db.execute_query(query)
    return jsonify({'attendance': records})

@app.route('/debug/student_by_name/<name>')
def debug_student_by_name(name):
    """Debug route to find a student by name"""
    query = "SELECT id, student_id, name FROM users WHERE name LIKE %s"
    student = db.execute_query(query, (f"%{name}%",))
    return jsonify({'student': student})

@app.route('/student_dashboard_chart')
def student_dashboard_chart():
    student_name = session.get('student_name')
    attendance_summary = get_attendance_summary(student_name) or []
    recent_records = get_recent_records(student_name) or []

    labels = [a.get('lecture_code', '') for a in attendance_summary]
    percentages = [a.get('attendance_percentage', 0) for a in attendance_summary]

    return render_template(
        'student_dashboard.html',
        student_name=student_name,
        attendance_summary=attendance_summary,
        recent_records=recent_records,
        chart_labels=labels,
        chart_values=percentages
    )




# ==================== ADMIN ROUTES ====================

@app.route('/admin_dashboard')
def admin_dashboard():
    """Main admin dashboard page"""
    return render_template('admin_dashboard.html')

@app.route('/admin_detections')
def admin_detections():
    """Face detection logs"""
    return render_template('admin_detections.html')

@app.route('/admin_users')
def admin_users():
    """User management"""
    return render_template('admin_users.html')

@app.route('/admin_access_logs')
def admin_access_logs():
    """System access logs"""
    return render_template('admin_access_logs.html')


# ==================== ADMIN API ROUTES ====================

@app.route('/admin_api/stats')
def admin_api_stats():
    """Get dashboard statistics"""
    try:
        # Get counts from database
        students_count = db.execute_query("SELECT COUNT(*) as count FROM users")
        faculty_count = db.execute_query("SELECT COUNT(*) as count FROM faculty")
        lectures_count = db.execute_query("SELECT COUNT(*) as count FROM lectures")
        attendance_count = db.execute_query("SELECT COUNT(*) as count FROM attendance WHERE DATE(attendance_time) = CURDATE()")
        
        total_students = students_count[0]['count'] if students_count else 0
        total_faculty = faculty_count[0]['count'] if faculty_count else 0
        total_lectures = lectures_count[0]['count'] if lectures_count else 0
        today_attendance = attendance_count[0]['count'] if attendance_count else 0
        
        return jsonify({
            'success': True,
            'total_students': total_students,
            'total_faculty': total_faculty,
            'total_lectures': total_lectures,
            'today_attendance': today_attendance,
            'total_users': total_students + total_faculty
        })
    except Exception as e:
        print(f"Error in admin_api_stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/recent_attendance')
def admin_api_recent_attendance():
    """Get recent attendance records"""
    try:
        records = db.execute_query("""
            SELECT a.attendance_time, a.status,
                    u.name as student_name, u.student_id,
                    l.lecture_code, l.title as lecture_title,
                    f.name as faculty_name
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN lectures l ON a.lecture_id = l.id
            JOIN faculty f ON a.faculty_id = f.id
            ORDER BY a.attendance_time DESC
            LIMIT 10
        """) or []
        
        return jsonify({
            'success': True,
            'records': records
        })
    except Exception as e:
        print(f"Error in admin_api_recent_attendance: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/recent_activity')
def admin_api_recent_activity():
    """Get recent system activity"""
    try:
        activities = []
        
        # Get recent student registrations
        recent_students = db.execute_query("""
            SELECT name, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 3
        """) or []
        
        for student in recent_students:
            activities.append({
                'type': 'user',
                'title': f'New student: {student["name"]}',
                'time': student['created_at'].strftime('%H:%M') if student['created_at'] else 'Recently',
                'icon': 'user-plus',
                'color': '#4361ee'
            })
        
        # Get recent faculty
        recent_faculty = db.execute_query("""
            SELECT name, created_at 
            FROM faculty 
            ORDER BY created_at DESC 
            LIMIT 2
        """) or []
        
        for faculty in recent_faculty:
            activities.append({
                'type': 'faculty',
                'title': f'New faculty: {faculty["name"]}',
                'time': faculty['created_at'].strftime('%H:%M') if faculty['created_at'] else 'Recently',
                'icon': 'chalkboard-teacher',
                'color': '#4cc9f0'
            })
        
        # Get recent attendance
        recent_attendance = db.execute_query("""
            SELECT u.name, a.attendance_time 
            FROM attendance a 
            JOIN users u ON a.student_id = u.id 
            ORDER BY a.attendance_time DESC 
            LIMIT 2
        """) or []
        
        for att in recent_attendance:
            activities.append({
                'type': 'attendance',
                'title': f'Attendance: {att["name"]}',
                'time': att['attendance_time'].strftime('%H:%M') if att['attendance_time'] else 'Recently',
                'icon': 'clipboard-check',
                'color': '#4bb543'
            })
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        print(f"Error in admin_api_recent_activity: {e}")
        return jsonify({'success': False, 'error': str(e)})
    


# Add these endpoints to your app.py with UNIQUE names

@app.route('/admin/user_management_page')
def admin_user_management_page():
    return render_template('admin_users.html')

@app.route('/admin_api/get_all_students')
def admin_api_get_all_students():
    db = Database()
    try:
        students = db.execute_query("""
            SELECT u.*, COUNT(ls.student_id) as enrolled_lectures
            FROM users u 
            LEFT JOIN lecture_students ls ON u.id = ls.student_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        return jsonify({'success': True, 'students': students or []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_all_faculty')
def admin_api_get_all_faculty():
    db = Database()
    try:
        faculty = db.execute_query("""
            SELECT f.*, COUNT(lf.lecture_id) as assigned_lectures
            FROM faculty f 
            LEFT JOIN lecture_faculty lf ON f.id = lf.faculty_id
            GROUP BY f.id
            ORDER BY f.created_at DESC
        """)
        return jsonify({'success': True, 'faculty': faculty or []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/create_new_user', methods=['POST'])
def admin_api_create_new_user():
    data = request.get_json()
    db = Database()
    
    try:
        if data['user_type'] == 'student':
            # Check if student ID already exists
            existing = db.execute_query("SELECT id FROM users WHERE student_id = %s", (data['user_id'],))
            if existing:
                return jsonify({'success': False, 'error': 'Student ID already exists'})
            
            result = db.execute_query(
                "INSERT INTO users (student_id, name, email, photo_path) VALUES (%s, %s, %s, %s)",
                (data['user_id'], data['name'], data['email'], 'default.jpg')
            )
        else:
            # Check if faculty ID already exists
            existing = db.execute_query("SELECT id FROM faculty WHERE faculty_id = %s", (data['user_id'],))
            if existing:
                return jsonify({'success': False, 'error': 'Faculty ID already exists'})
            
            # Hash password for faculty
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(data['password'] or 'password123')
            result = db.execute_query(
                "INSERT INTO faculty (faculty_id, name, email, password) VALUES (%s, %s, %s, %s)",
                (data['user_id'], data['name'], data['email'], hashed_password)
            )
        
        return jsonify({'success': result is not None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/remove_user_account/<user_type>/<int:user_id>', methods=['DELETE'])
def admin_api_remove_user_account(user_type, user_id):
    db = Database()
    
    try:
        if user_type == 'student':
            result = db.execute_query("DELETE FROM users WHERE id = %s", (user_id,))
        else:
            result = db.execute_query("DELETE FROM faculty WHERE id = %s", (user_id,))
        
        return jsonify({'success': result is not None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_student/<int:user_id>')
def admin_api_get_student(user_id):
    db = Database()
    try:
        result = db.execute_query(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        if result:
            return jsonify({'success': True, 'student': result[0]})
        return jsonify({'success': False, 'error': 'Student not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_faculty/<int:user_id>')
def admin_api_get_faculty(user_id):
    db = Database()
    try:
        result = db.execute_query(
            "SELECT * FROM faculty WHERE id = %s",
            (user_id,)
        )
        if result:
            return jsonify({'success': True, 'faculty': result[0]})
        return jsonify({'success': False, 'error': 'Faculty not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/update_user', methods=['POST'])
def admin_api_update_user():
    data = request.get_json()
    db = Database()

    try:
        user_id = data['edit_user_id']
        user_type = data['edit_user_type']

        if user_type == 'student':
            query = """
                UPDATE users 
                SET student_id=%s, name=%s, email=%s, photo_path=%s
                WHERE id=%s
            """
            params = (
                data['user_id'],
                data['name'],
                data['email'],
                data.get('photo_path', 'default.jpg'),
                user_id
            )
        
        else:  # faculty
            query = """
                UPDATE faculty 
                SET faculty_id=%s, name=%s, email=%s
                WHERE id=%s
            """
            params = (
                data['user_id'],
                data['name'],
                data['email'],
                user_id
            )

        result = db.execute_query(query, params)
        return jsonify({'success': result is not None})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Lecture Management Routes
@app.route('/admin/lecture_management_page')
def admin_lecture_management_page():
    return render_template('admin_lectures.html')

@app.route('/admin_api/get_all_lectures')
def admin_api_get_all_lectures():
    db = Database()
    try:
        lectures = db.execute_query("""
            SELECT l.*, 
                   COUNT(DISTINCT lf.faculty_id) as assigned_faculty_count,
                   COUNT(DISTINCT ls.student_id) as enrolled_students_count
            FROM lectures l
            LEFT JOIN lecture_faculty lf ON l.id = lf.lecture_id
            LEFT JOIN lecture_students ls ON l.id = ls.lecture_id
            GROUP BY l.id
            ORDER BY l.created_at DESC
        """)
        return jsonify({'success': True, 'lectures': lectures or []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/create_new_lecture', methods=['POST'])
def admin_api_create_new_lecture():
    data = request.get_json()
    db = Database()
    
    try:
        lecture_code = data.get('lecture_code')
        title = data.get('title')
        description = data.get('description', '')

        # Check if lecture code already exists
        existing = db.execute_query("SELECT id FROM lectures WHERE lecture_code = %s", (lecture_code,))
        if existing:
            return jsonify({'success': False, 'error': 'Lecture code already exists'})

        result = db.execute_query(
            "INSERT INTO lectures (lecture_code, title, description) VALUES (%s, %s, %s)",
            (lecture_code, title, description)
        )
        
        return jsonify({'success': result is not None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/remove_lecture/<int:lecture_id>', methods=['DELETE'])
def admin_api_remove_lecture(lecture_id):
    db = Database()
    
    try:
        result = db.execute_query("DELETE FROM lectures WHERE id = %s", (lecture_id,))
        return jsonify({'success': result is not None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_lecture_details/<int:lecture_id>')
def admin_api_get_lecture_details(lecture_id):
    db = Database()
    try:
        # Get lecture basic info
        lecture = db.execute_query("SELECT * FROM lectures WHERE id = %s", (lecture_id,))
        if not lecture:
            return jsonify({'success': False, 'error': 'Lecture not found'})

        # Get assigned faculty
        faculty = db.execute_query("""
            SELECT f.* FROM faculty f
            JOIN lecture_faculty lf ON f.id = lf.faculty_id
            WHERE lf.lecture_id = %s
        """, (lecture_id,))

        # Get enrolled students
        students = db.execute_query("""
            SELECT u.* FROM users u
            JOIN lecture_students ls ON u.id = ls.student_id
            WHERE ls.lecture_id = %s
        """, (lecture_id,))

        return jsonify({
            'success': True,
            'lecture': lecture[0],
            'faculty': faculty or [],
            'students': students or []
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    

@app.route('/admin_api/update_lecture/<int:lecture_id>', methods=['POST'])
def admin_api_update_lecture(lecture_id):
    data = request.get_json()
    db = Database()

    try:
        result = db.execute_query("""
            UPDATE lectures 
            SET lecture_code=%s, title=%s, description=%s 
            WHERE id=%s
        """, (data['lecture_code'], data['title'], data.get('description', ''), lecture_id))

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Add to your app.py

@app.route('/admin_api/get_face_detections')
def get_face_detections():
    """Get face detection logs from database"""
    try:
        # Since we don't have a dedicated face_detections table,
        # we'll use attendance records as detection logs
        detections = db.execute_query("""
            SELECT 
                a.id,
                u.name as student_name,
                u.student_id,
                l.lecture_code,
                a.attendance_time as detection_time,
                CASE 
                    WHEN a.status = 'Present' THEN 'success'
                    WHEN a.status = 'Absent' THEN 'failed' 
                    ELSE 'unknown'
                END as status,
                0.85 as confidence,  -- Mock confidence score
                f.name as faculty_name
            FROM attendance a
            LEFT JOIN users u ON a.student_id = u.id
            LEFT JOIN lectures l ON a.lecture_id = l.id
            LEFT JOIN faculty f ON a.faculty_id = f.id
            ORDER BY a.attendance_time DESC
            LIMIT 100
        """)
        
        return jsonify({
            'success': True,
            'detections': detections or []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin_api/get_access_logs')
def get_access_logs():
    """Get system access logs"""
    try:
        # Since we don't have an access_logs table, we'll create mock data
        # In a real system, you'd log all login attempts
        access_logs = db.execute_query("""
            SELECT 
                'login_' || ROW_NUMBER() OVER () as id,
                u.name as user_name,
                CASE 
                    WHEN u.student_id IS NOT NULL THEN u.student_id
                    WHEN f.faculty_id IS NOT NULL THEN f.faculty_id
                    ELSE 'admin'
                END as user_id,
                CASE 
                    WHEN u.student_id IS NOT NULL THEN 'student'
                    WHEN f.faculty_id IS NOT NULL THEN 'faculty'
                    ELSE 'admin'
                END as user_type,
                COALESCE(u.created_at, f.created_at, NOW()) as login_time,
                '192.168.1.' || (FLOOR(RANDOM() * 255) + 1) as ip_address,
                CASE 
                    WHEN RANDOM() > 0.1 THEN 'success'
                    ELSE 'failed'
                END as status,
                'Mozilla/5.0...' as user_agent
            FROM (
                SELECT id, name, student_id, created_at, 'student' as type FROM users
                UNION ALL
                SELECT id, name, faculty_id, created_at, 'faculty' as type FROM faculty
            ) u
            LEFT JOIN faculty f ON u.type = 'faculty' AND f.id = u.id
            ORDER BY login_time DESC
            LIMIT 100
        """)
        
        return jsonify({
            'success': True,
            'logs': access_logs or []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
# Add these NEW routes to your app.py (make sure they don't already exist)

@app.route('/admin_api/attendance_chart')
def attendance_chart():
    """Get attendance data for charts"""
    try:
        period = request.args.get('period', '7')
        
        # Generate chart data based on period
        if period == '7':
            query = """
            SELECT DATE(attendance_time) as date, COUNT(*) as count
            FROM attendance 
            WHERE attendance_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(attendance_time)
            ORDER BY date
            """
        elif period == '30':
            query = """
            SELECT DATE(attendance_time) as date, COUNT(*) as count
            FROM attendance 
            WHERE attendance_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(attendance_time)
            ORDER BY date
            """
        else:  # 90 days
            query = """
            SELECT DATE_FORMAT(attendance_time, '%%Y-%%m') as month, COUNT(*) as count
            FROM attendance 
            WHERE attendance_time >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            GROUP BY DATE_FORMAT(attendance_time, '%%Y-%%m')
            ORDER BY month
            """
        
        chart_data = db.execute_query(query)
        
        labels = []
        data = []
        
        for row in chart_data:
            labels.append(row['date'] if period != '90' else row['month'])
            data.append(row['count'])
        
        return jsonify({
            'success': True,
            'chartData': {
                'labels': labels,
                'data': data
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin_api/quick_stats')
def quick_stats():
    """Get quick statistics for dashboard"""
    try:
        # Attendance rate (percentage of present vs total records today)
        attendance_rate_query = """
        SELECT 
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    ROUND((SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 1)
                ELSE 0 
            END as rate
        FROM attendance 
        WHERE DATE(attendance_time) = CURDATE()
        """
        attendance_rate_result = db.execute_query(attendance_rate_query)
        
        # Recognition accuracy (mock data for now)
        recognition_accuracy = "98.5%"
        
        # System load (mock data)
        system_load = "45%"
        
        # Active lectures today
        active_lectures_query = """
        SELECT COUNT(DISTINCT lecture_id) as count
        FROM attendance 
        WHERE DATE(attendance_time) = CURDATE()
        """
        active_lectures_result = db.execute_query(active_lectures_query)
        
        attendance_rate = attendance_rate_result[0]['rate'] if attendance_rate_result else 0
        active_lectures = active_lectures_result[0]['count'] if active_lectures_result else 0
        
        return jsonify({
            'success': True,
            'attendance_rate': f"{attendance_rate}%",
            'recognition_accuracy': recognition_accuracy,
            'system_load': system_load,
            'active_lectures': active_lectures
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
    
    # Add these routes to your Flask application

@app.route('/admin_api/recent_students')
def recent_students():
    db = Database()
    students = db.execute_query("""
        SELECT id, student_id, name, email, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    return jsonify({
        'success': True,
        'students': students or []
    })

@app.route('/admin_api/recent_faculty')
def recent_faculty():
    db = Database()
    faculty = db.execute_query("""
        SELECT id, faculty_id, name, email, created_at 
        FROM faculty 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    return jsonify({
        'success': True,
        'faculty': faculty or []
    })

@app.route('/admin_api/recent_attendance_activity')
def recent_attendance_activity():
    db = Database()
    attendance = db.execute_query("""
        SELECT a.id, a.student_id, a.lecture_id, a.faculty_id, 
                a.attendance_time, a.status,
                u.name as student_name, l.lecture_code
        FROM attendance a
        LEFT JOIN users u ON a.student_id = u.id
        LEFT JOIN lectures l ON a.lecture_id = l.id
        ORDER BY a.attendance_time DESC 
        LIMIT 10
    """)
    return jsonify({
        'success': True,
        'attendance': attendance or []
    })


@app.route('/admin_api/create_new_user', methods=['POST'])
def create_new_user():
    try:
        data = request.get_json()
        user_type = data.get('user_type')
        user_id = data.get('user_id')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        photo_path = data.get('photo_path', '')

        if not all([user_type, user_id, name, email]):
            return jsonify({'success': False, 'error': 'Missing required fields'})

        if user_type == 'student':
            # Create student
            query = "INSERT INTO users (student_id, name, email, photo_path) VALUES (%s, %s, %s, %s)"
            params = (user_id, name, email, photo_path)
            result = db.execute_query(query, params)
            
            if result:
                return jsonify({'success': True, 'message': 'Student created successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to create student'})

        elif user_type == 'faculty':
            # Create faculty - password is required
            if not password:
                return jsonify({'success': False, 'error': 'Password is required for faculty'})
            
            # Hash the password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            query = "INSERT INTO faculty (faculty_id, name, email, password) VALUES (%s, %s, %s, %s)"
            params = (user_id, name, email, hashed_password)
            result = db.execute_query(query, params)
            
            if result:
                return jsonify({'success': True, 'message': 'Faculty created successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to create faculty'})

        else:
            return jsonify({'success': False, 'error': 'Invalid user type'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/update_user', methods=['POST'])
def update_user():
    try:
        data = request.get_json()
        user_type = data.get('user_type')
        user_id = data.get('user_id')
        edit_user_id = data.get('edit_user_id')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        photo_path = data.get('photo_path')

        if not all([user_type, edit_user_id, user_id, name, email]):
            return jsonify({'success': False, 'error': 'Missing required fields'})

        if user_type == 'student':
            query = "UPDATE users SET student_id = %s, name = %s, email = %s, photo_path = %s WHERE id = %s"
            params = (user_id, name, email, photo_path, edit_user_id)
            result = db.execute_query(query, params)
            
            if result:
                return jsonify({'success': True, 'message': 'Student updated successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to update student'})

        elif user_type == 'faculty':
            if password:
                # Hash the new password
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                query = "UPDATE faculty SET faculty_id = %s, name = %s, email = %s, password = %s WHERE id = %s"
                params = (user_id, name, email, hashed_password, edit_user_id)
            else:
                query = "UPDATE faculty SET faculty_id = %s, name = %s, email = %s WHERE id = %s"
                params = (user_id, name, email, edit_user_id)
            
            result = db.execute_query(query, params)
            
            if result:
                return jsonify({'success': True, 'message': 'Faculty updated successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to update faculty'})

        else:
            return jsonify({'success': False, 'error': 'Invalid user type'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_all_students', methods=['GET'])
def get_all_students():
    try:
        query = """
        SELECT u.*, COUNT(ls.lecture_id) as enrolled_lectures 
        FROM users u 
        LEFT JOIN lecture_students ls ON u.id = ls.student_id 
        GROUP BY u.id
        """
        students = db.execute_query(query)
        
        if students is not None:
            return jsonify({'success': True, 'students': students})
        else:
            return jsonify({'success': False, 'error': 'Failed to fetch students'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_all_faculty', methods=['GET'])
def get_all_faculty():
    try:
        query = """
        SELECT f.*, COUNT(lf.lecture_id) as assigned_lectures 
        FROM faculty f 
        LEFT JOIN lecture_faculty lf ON f.id = lf.faculty_id 
        GROUP BY f.id
        """
        faculty = db.execute_query(query)
        
        if faculty is not None:
            return jsonify({'success': True, 'faculty': faculty})
        else:
            return jsonify({'success': False, 'error': 'Failed to fetch faculty'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_student/<int:student_id>', methods=['GET'])
def get_student(student_id):
    try:
        query = "SELECT * FROM users WHERE id = %s"
        student = db.execute_query(query, (student_id,))
        
        if student and len(student) > 0:
            return jsonify({'success': True, 'student': student[0]})
        else:
            return jsonify({'success': False, 'error': 'Student not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/get_faculty/<int:faculty_id>', methods=['GET'])
def get_faculty(faculty_id):
    try:
        query = "SELECT * FROM faculty WHERE id = %s"
        faculty = db.execute_query(query, (faculty_id,))
        
        if faculty and len(faculty) > 0:
            return jsonify({'success': True, 'faculty': faculty[0]})
        else:
            return jsonify({'success': False, 'error': 'Faculty not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin_api/remove_user_account/<user_type>/<int:user_id>', methods=['DELETE'])
def remove_user_account(user_type, user_id):
    try:
        if user_type == 'student':
            query = "DELETE FROM users WHERE id = %s"
        elif user_type == 'faculty':
            query = "DELETE FROM faculty WHERE id = %s"
        else:
            return jsonify({'success': False, 'error': 'Invalid user type'})
        
        result = db.execute_query(query, (user_id,))
        
        if result:
            return jsonify({'success': True, 'message': f'{user_type.capitalize()} deleted successfully'})
        else:
            return jsonify({'success': False, 'error': f'Failed to delete {user_type}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
        
    
# ==================== MAIN APPLICATION ====================

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(Config.KNOWN_FACES_DIR, exist_ok=True)
    os.makedirs(Config.ATTENDANCE_RECORDS_DIR, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)