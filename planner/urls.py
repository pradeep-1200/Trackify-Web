from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Dashboard and Tasks
    path('', views.dashboard, name='dashboard'),
    path('tasks/add/', views.task_create, name='task-create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task-update'),
    path('tasks/<int:pk>/toggle/', views.task_toggle, name='task-toggle'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task-delete'),
    
    # Productivity Tools
    path('pomodoro/', views.pomodoro_timer, name='pomodoro'),
    path('timer-stats/', views.timer_statistics, name='timer-stats'),
    path('analytics/', views.study_analytics, name='analytics'),
    path('timeline/', views.task_timeline, name='task-timeline'),

    # Planning Tools
    path('smart-schedule/', views.smart_schedule, name='smart-schedule'),
    path('priority-tasks/', views.priority_based_tasks, name='priority-tasks'),
    path('eisenhower-matrix/', views.eisenhower_matrix, name='eisenhower-matrix'),
    path('tasks/update-quadrant/', views.update_task_quadrant, name='update-task-quadrant'),
    
    # Settings
    path('settings/', views.user_settings, name='user-settings'),
    
]