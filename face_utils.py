import face_recognition
import cv2
import numpy as np
import os
from config import Config

class FaceRecognition:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.load_known_faces()
        
    def load_known_faces(self):
        # Load known faces from the database and known_faces folder
        from database import Database
        db = Database()
        
        # Get all users from database
        users = db.execute_query("SELECT id, student_id, name, photo_path FROM users")
        
        if users:
            for user in users:
                image_path = os.path.join(Config.KNOWN_FACES_DIR, user['photo_path'])
                if os.path.exists(image_path):
                    try:
                        # Use the actual face_recognition library
                        image = face_recognition.load_image_file(image_path)
                        encoding = face_recognition.face_encodings(image)
                        
                        if encoding:
                            self.known_face_encodings.append(encoding[0])
                            self.known_face_names.append(user['name'])
                            self.known_face_ids.append(user['id'])
                    except Exception as e:
                        print(f"Error loading face for {user['name']}: {e}")
        
    def recognize_faces(self, frame):
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        
        # Find all faces in the current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        face_ids = []
        
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=Config.TOLERANCE)
            name = "Unknown"
            face_id = None
            
            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    face_id = self.known_face_ids[best_match_index]
            
            face_names.append(name)
            face_ids.append(face_id)
        
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        # Convert from (top, right, bottom, left) to (x, y, width, height)
        face_rects = []
        for (top, right, bottom, left) in face_locations:
            x = left * 4
            y = top * 4
            width = (right - left) * 4
            height = (bottom - top) * 4
            face_rects.append({
                'x': x,
                'y': y, 
                'width': width,
                'height': height
            })
        
        return face_rects, face_names, face_ids
    
    def mark_attendance(self, student_id, lecture_id, faculty_id):
        try:
            from database import Database
            db = Database()
            
            # Check if attendance already marked today
            query = """
            SELECT id FROM attendance 
            WHERE student_id = %s AND lecture_id = %s 
            AND DATE(attendance_time) = CURDATE()
            """
            existing = db.execute_query(query, (student_id, lecture_id))
            
            if existing:
                print(f"Attendance already exists for student {student_id} in lecture {lecture_id} today")
                return False
            
            # Mark attendance
            query = """
            INSERT INTO attendance (student_id, lecture_id, faculty_id, status) 
            VALUES (%s, %s, %s, 'Present')
            """
            result = db.execute_query(query, (student_id, lecture_id, faculty_id))
            
            if result:
                print(f"Attendance marked successfully for student {student_id} in lecture {lecture_id}")
                return True
            else:
                print(f"Database error when marking attendance for student {student_id}")
                return False
                
        except Exception as e:
            print(f"Error in mark_attendance: {e}")
            return False