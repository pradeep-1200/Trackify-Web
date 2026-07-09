from mongoengine import Document, StringField, DateTimeField, IntField, BooleanField, ListField, EmbeddedDocument, EmbeddedDocumentField
import datetime

class MongoUser(Document):
    """MongoDB model for user authentication data"""
    # User identification (linked to Django User model)
    django_id = IntField(required=True, unique=True)
    username = StringField(required=True, max_length=150, unique=True)
    email = StringField(max_length=254)
    
    # User metadata
    date_joined = DateTimeField(default=datetime.datetime.now)
    last_login = DateTimeField()
    is_active = BooleanField(default=True)
    
    # Additional user information
    first_name = StringField(max_length=150)
    last_name = StringField(max_length=150)
    
    meta = {
        'collection': 'users',
        'indexes': [
            'django_id',
            'username',
            'email'
        ]
    }
    
    def __str__(self):
        return self.username

class MongoUserSettings(Document):
    """MongoDB model for user settings"""
    # User identification
    user_id = IntField(required=True, unique=True)
    username = StringField(required=True, max_length=150)
    
    # Timer settings
    work_duration = IntField(default=25)  # in minutes
    short_break_duration = IntField(default=5)  # in minutes
    long_break_duration = IntField(default=15)  # in minutes
    long_break_interval = IntField(default=4)  # number of work sessions before long break
    
    # Productivity settings
    most_productive_time = StringField(choices=('MORNING', 'AFTERNOON', 'EVENING', 'NIGHT'), default='MORNING')
    daily_goal = IntField(default=120)  # in minutes
    weekly_goal = IntField(default=600)  # in minutes
    
    # Preferences
    enable_dark_mode = BooleanField(default=False)
    enable_sounds = BooleanField(default=True)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    meta = {
        'collection': 'user_settings',
        'indexes': [
            'user_id',
            'username'
        ]
    }
    
    def __str__(self):
        return f"Settings for {self.username}"

class MongoTimerSession(Document):
    """MongoDB model for timer sessions"""
    # User identification
    user_id = IntField(required=True)
    username = StringField(required=True, max_length=150)
    
    # Session details
    session_type = StringField(choices=('work', 'short_break', 'long_break'), default='work')
    duration = IntField(default=0)  # in seconds
    
    # Task reference (if associated with a task)
    task_id = IntField()
    task_title = StringField(max_length=200)
    
    # Timestamps
    start_time = DateTimeField()
    end_time = DateTimeField()
    created_at = DateTimeField(default=datetime.datetime.now)
    
    meta = {
        'collection': 'timer_sessions',
        'indexes': [
            'user_id',
            'session_type',
            'start_time',
            'task_id'
        ]
    }
    
    def __str__(self):
        return f"{self.session_type} session for {self.username}"

class MongoStudySession(Document):
    """MongoDB model for study sessions"""
    # User identification
    user_id = IntField(required=True)
    username = StringField(required=True, max_length=150)
    
    # Session details
    duration = IntField(default=0)  # in minutes
    productivity_score = IntField(min_value=1, max_value=5, default=3)
    distractions = IntField(default=0)
    
    # Task reference (if associated with a task)
    task_id = IntField()
    task_title = StringField(max_length=200)
    
    # Timestamps
    start_time = DateTimeField()
    end_time = DateTimeField()
    created_at = DateTimeField(default=datetime.datetime.now)
    
    meta = {
        'collection': 'study_sessions',
        'indexes': [
            'user_id',
            'productivity_score',
            'start_time',
            'task_id'
        ]
    }
    
    def __str__(self):
        return f"Study session for {self.username}"
