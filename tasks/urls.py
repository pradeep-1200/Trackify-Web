from django.urls import path
from . import views

urlpatterns = [
    path('sync-to-mongodb/', views.sync_task_to_mongodb, name='sync-task-to-mongodb'),
    path('update-quadrant-mongodb/', views.update_task_quadrant_mongodb, name='update-task-quadrant-mongodb'),
    path('create-timer-session/', views.create_timer_session, name='create-timer-session'),
    path('create-study-session/', views.create_study_session, name='create-study-session'),
]
