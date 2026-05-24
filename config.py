import os

class Config:
    # Database configuration (XAMPP MySQL)
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'face_attendance_db'
    
    # File paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    KNOWN_FACES_DIR = os.path.join(BASE_DIR, 'known_faces')
    ATTENDANCE_RECORDS_DIR = os.path.join(BASE_DIR, 'attendance_records')
    
    # Secret key for sessions
    SECRET_KEY = 'your-secret-key-here'
    
    # Face recognition settings
    TOLERANCE = 0.5  # Lowered from 0.6 for stricter matching
    FRAME_THICKNESS = 3
    FONT_THICKNESS = 2
    
    # Email Configuration for Password Reset
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'pankti112004@gmail.com'
    MAIL_PASSWORD = 'klqv jjig bkxy kuzi'
    MAIL_DEFAULT_SENDER = 'pankti112004@gmail.com'
    
    # NEW: Enhanced configuration for improved accuracy
    MIN_CONFIDENCE = 0.7  # Minimum confidence for attendance (70% confidence required)
    ATTENDANCE_COOLDOWN = 30  # Seconds between attendance marks for same student
    FACE_QUALITY_THRESHOLD = 100  # Minimum face quality score (Laplacian variance)
    MAX_UNKNOWN_FACES = 10  # Maximum unknown faces to track simultaneously
    
    # Performance settings
    PROCESSING_INTERVAL = 1  # Process every frame (1 = process all frames)
    ENABLE_ANTI_SPOOFING = True  # Enable liveness detection
    ENABLE_FACE_QUALITY_CHECK = True  # Check face quality during registration
    
    # Face detection settings
    FACE_DETECTION_MODEL = 'hog'  # Options: 'hog' (faster) or 'cnn' (more accurate)
    MIN_FACE_SIZE = 50  # Minimum face size in pixels
    MAX_FACE_SIZE = 400  # Maximum face size in pixels
    
    # Image processing
    RESIZE_FACTOR = 0.25  # Resize factor for faster processing
    BRIGHTNESS_THRESHOLD_LOW = 50  # Minimum brightness
    BRIGHTNESS_THRESHOLD_HIGH = 200  # Maximum brightness
    
    # Attendance settings
    ATTENDANCE_START_TIME = '09:00:00'  # Default attendance start time
    ATTENDANCE_END_TIME = '17:00:00'  # Default attendance end time
    MAX_ATTENDANCE_DURATION = 300  # Maximum attendance duration in seconds (5 minutes)
    
    # Session settings
    SESSION_TIMEOUT = 1800  # Session timeout in seconds (30 minutes)
    MAX_LOGIN_ATTEMPTS = 5  # Maximum login attempts before lockout
    
    # Logging settings
    LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE = 'face_attendance.log'
    
    # Security settings
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    
    # Camera settings
    CAMERA_RESOLUTION = (640, 480)  # Default camera resolution
    CAMERA_FPS = 30  # Frames per second
    
    # Debug settings
    DEBUG_FACE_RECOGNITION = True  # Print debug info for face recognition
    SAVE_UNKNOWN_FACES = True  # Save unknown faces for training
    UNKNOWN_FACES_DIR = os.path.join(BASE_DIR, 'unknown_faces')  # Directory for unknown faces
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check directories exist
        required_dirs = [cls.KNOWN_FACES_DIR, cls.ATTENDANCE_RECORDS_DIR]
        if cls.SAVE_UNKNOWN_FACES:
            required_dirs.append(cls.UNKNOWN_FACES_DIR)
            
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Created directory: {directory}")
        
        # Validate thresholds
        if not 0 <= cls.TOLERANCE <= 1:
            errors.append("TOLERANCE must be between 0 and 1")
        
        if not 0 <= cls.MIN_CONFIDENCE <= 1:
            errors.append("MIN_CONFIDENCE must be between 0 and 1")
        
        if cls.MIN_CONFIDENCE > (1 - cls.TOLERANCE):
            errors.append(f"MIN_CONFIDENCE ({cls.MIN_CONFIDENCE}) should be <= {1 - cls.TOLERANCE}")
        
        # Validate email configuration
        if '@' not in cls.MAIL_USERNAME:
            errors.append("MAIL_USERNAME must be a valid email address")
        
        # Validate face size
        if cls.MIN_FACE_SIZE > cls.MAX_FACE_SIZE:
            errors.append("MIN_FACE_SIZE cannot be greater than MAX_FACE_SIZE")
        
        # Validate processing interval
        if cls.PROCESSING_INTERVAL < 1:
            errors.append("PROCESSING_INTERVAL must be at least 1")
        
        if errors:
            for error in errors:
                print(f"⚠️ Configuration Error: {error}")
            return False
        
        return True
    
    @classmethod
    def get_face_recognition_params(cls):
        """Get face recognition parameters as a dictionary"""
        return {
            'tolerance': cls.TOLERANCE,
            'min_confidence': cls.MIN_CONFIDENCE,
            'face_detection_model': cls.FACE_DETECTION_MODEL,
            'min_face_size': cls.MIN_FACE_SIZE,
            'max_face_size': cls.MAX_FACE_SIZE,
            'resize_factor': cls.RESIZE_FACTOR,
            'enable_anti_spoofing': cls.ENABLE_ANTI_SPOOFING
        }
    
    @classmethod
    def get_attendance_params(cls):
        """Get attendance parameters as a dictionary"""
        return {
            'attendance_cooldown': cls.ATTENDANCE_COOLDOWN,
            'max_attendance_duration': cls.MAX_ATTENDANCE_DURATION,
            'start_time': cls.ATTENDANCE_START_TIME,
            'end_time': cls.ATTENDANCE_END_TIME
        }

# Validate configuration on import
if __name__ == "__main__":
    print("🔧 Validating configuration...")
    if Config.validate_config():
        print("✅ Configuration is valid!")
        
        # Print current settings
        print("\n📋 Current Configuration:")
        print(f"  • Tolerance: {Config.TOLERANCE}")
        print(f"  • Minimum Confidence: {Config.MIN_CONFIDENCE}")
        print(f"  • Face Detection Model: {Config.FACE_DETECTION_MODEL}")
        print(f"  • Face Quality Check: {'Enabled' if Config.ENABLE_FACE_QUALITY_CHECK else 'Disabled'}")
        print(f"  • Anti-Spoofing: {'Enabled' if Config.ENABLE_ANTI_SPOOFING else 'Disabled'}")
        print(f"  • Save Unknown Faces: {'Enabled' if Config.SAVE_UNKNOWN_FACES else 'Disabled'}")
    else:
        print("❌ Configuration has errors!")