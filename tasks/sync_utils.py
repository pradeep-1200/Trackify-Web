"""
Utility functions for syncing Django models with MongoDB
"""
import datetime
from django.contrib.auth import get_user_model
from planner.models import Task as DjangoTask, UserSettings as DjangoUserSettings
from planner.models import TimerSession as DjangoTimerSession, StudySession as DjangoStudySession
from tasks.models import Task as MongoTask
from tasks.auth_models import MongoUser, MongoUserSettings, MongoTimerSession, MongoStudySession

User = get_user_model()

def sync_user_to_mongodb(user):
    """Sync a Django User to MongoDB"""
    try:
        # Check if MongoDB user already exists
        mongo_user = MongoUser.objects(django_id=user.id).first()
        
        if mongo_user:
            # Update existing MongoDB user
            mongo_user.username = user.username
            mongo_user.email = user.email
            mongo_user.first_name = user.first_name
            mongo_user.last_name = user.last_name
            mongo_user.is_active = user.is_active
            mongo_user.last_login = user.last_login
            mongo_user.save()
        else:
            # Create new MongoDB user
            mongo_user = MongoUser(
                django_id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                date_joined=user.date_joined,
                last_login=user.last_login
            )
            mongo_user.save()
        
        return mongo_user
    except Exception as e:
        print(f"Error syncing user to MongoDB: {e}")
        return None

def sync_user_settings_to_mongodb(user_settings):
    """Sync Django UserSettings to MongoDB"""
    try:
        # Check if MongoDB user settings already exist
        mongo_settings = MongoUserSettings.objects(user_id=user_settings.user.id).first()
        
        if mongo_settings:
            # Update existing MongoDB user settings
            mongo_settings.username = user_settings.user.username
            mongo_settings.work_duration = user_settings.work_duration
            mongo_settings.short_break_duration = user_settings.short_break_duration
            mongo_settings.long_break_duration = user_settings.long_break_duration
            mongo_settings.long_break_interval = user_settings.long_break_interval
            mongo_settings.most_productive_time = user_settings.most_productive_time
            mongo_settings.daily_goal = user_settings.daily_goal
            mongo_settings.weekly_goal = user_settings.weekly_goal
            mongo_settings.enable_dark_mode = user_settings.enable_dark_mode
            mongo_settings.enable_sounds = user_settings.enable_sounds
            mongo_settings.updated_at = datetime.datetime.now()
            mongo_settings.save()
        else:
            # Create new MongoDB user settings
            mongo_settings = MongoUserSettings(
                user_id=user_settings.user.id,
                username=user_settings.user.username,
                work_duration=user_settings.work_duration,
                short_break_duration=user_settings.short_break_duration,
                long_break_duration=user_settings.long_break_duration,
                long_break_interval=user_settings.long_break_interval,
                most_productive_time=user_settings.most_productive_time,
                daily_goal=user_settings.daily_goal,
                weekly_goal=user_settings.weekly_goal,
                enable_dark_mode=user_settings.enable_dark_mode,
                enable_sounds=user_settings.enable_sounds
            )
            mongo_settings.save()
        
        return mongo_settings
    except Exception as e:
        print(f"Error syncing user settings to MongoDB: {e}")
        return None

def sync_timer_session_to_mongodb(timer_session):
    """Sync Django TimerSession to MongoDB"""
    try:
        # Check if MongoDB timer session already exists
        mongo_session = MongoTimerSession.objects(
            user_id=timer_session.user.id,
            start_time=timer_session.start_time
        ).first()
        
        task_id = timer_session.task.id if timer_session.task else None
        task_title = timer_session.task.title if timer_session.task else None
        
        if mongo_session:
            # Update existing MongoDB timer session
            mongo_session.username = timer_session.user.username
            mongo_session.session_type = timer_session.session_type
            mongo_session.duration = timer_session.duration
            mongo_session.task_id = task_id
            mongo_session.task_title = task_title
            mongo_session.end_time = timer_session.end_time
            mongo_session.save()
        else:
            # Create new MongoDB timer session
            mongo_session = MongoTimerSession(
                user_id=timer_session.user.id,
                username=timer_session.user.username,
                session_type=timer_session.session_type,
                duration=timer_session.duration,
                task_id=task_id,
                task_title=task_title,
                start_time=timer_session.start_time,
                end_time=timer_session.end_time
            )
            mongo_session.save()
        
        return mongo_session
    except Exception as e:
        print(f"Error syncing timer session to MongoDB: {e}")
        return None

def sync_study_session_to_mongodb(study_session):
    """Sync Django StudySession to MongoDB"""
    try:
        # Check if MongoDB study session already exists
        mongo_session = MongoStudySession.objects(
            user_id=study_session.user.id,
            start_time=study_session.start_time
        ).first()
        
        task_id = study_session.task.id if study_session.task else None
        task_title = study_session.task.title if study_session.task else None
        
        if mongo_session:
            # Update existing MongoDB study session
            mongo_session.username = study_session.user.username
            mongo_session.duration = study_session.duration
            mongo_session.productivity_score = study_session.productivity_score
            mongo_session.distractions = study_session.distractions
            mongo_session.task_id = task_id
            mongo_session.task_title = task_title
            mongo_session.end_time = study_session.end_time
            mongo_session.save()
        else:
            # Create new MongoDB study session
            mongo_session = MongoStudySession(
                user_id=study_session.user.id,
                username=study_session.user.username,
                duration=study_session.duration,
                productivity_score=study_session.productivity_score,
                distractions=study_session.distractions,
                task_id=task_id,
                task_title=task_title,
                start_time=study_session.start_time,
                end_time=study_session.end_time
            )
            mongo_session.save()
        
        return mongo_session
    except Exception as e:
        print(f"Error syncing study session to MongoDB: {e}")
        return None
