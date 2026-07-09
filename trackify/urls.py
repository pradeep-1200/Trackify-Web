from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from planner import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),

    # Updated auth URLs with explicit logout
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('accounts/register/', views.register, name='register'),

    # Direct access to pomodoro timer
    path('pomodoro/', views.pomodoro_timer, name='pomodoro-direct'),

    # App URLs
    path('planner/', include('planner.urls')),
    path('tasks/', include('tasks.urls')),  # Add MongoDB tasks URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)