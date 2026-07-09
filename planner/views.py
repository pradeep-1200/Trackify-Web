from django.forms import BooleanField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, F, Case, When, Value, CharField, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractHour
from django.http import JsonResponse
import json
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import models

from .models import Task, TimerSession, StudySession, UserSettings
from .forms import TaskForm, CustomUserCreationForm, CustomAuthenticationForm, UserSettingsForm
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, Case, When, Value, CharField, BooleanField
from django.http import JsonResponse

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Sync user to MongoDB
            try:
                from tasks.sync_utils import sync_user_to_mongodb
                sync_user_to_mongodb(user)
            except Exception as e:
                print(f"Error syncing user to MongoDB: {e}")

            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Trackify.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'planner/register.html', {
        'form': form,
        'title': 'Create Your Account'
    })

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                # Sync user to MongoDB
                try:
                    from tasks.sync_utils import sync_user_to_mongodb
                    sync_user_to_mongodb(user)
                except Exception as e:
                    print(f"Error syncing user to MongoDB: {e}")

                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'planner/login.html', {
        'form': form,
        'title': 'Login to Your Account'
    })

@login_required
def dashboard(request):
    settings, created = UserSettings.objects.get_or_create(user=request.user)

    pending_tasks = Task.objects.filter(
        user=request.user,
        completed=False
    ).order_by(
        Case(
            When(priority='H', then=Value(0)),
            When(priority='M', then=Value(1)),
            When(priority='L', then=Value(2)),
            default=Value(3),
            output_field=CharField()
        ),
        'due_date'
    )

    completed_tasks = Task.objects.filter(
        user=request.user,
        completed=True
    ).order_by('-updated_at')[:10]

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    daily_study = StudySession.objects.filter(
        user=request.user,
        start_time__gte=today_start
    ).aggregate(total=Sum('duration'))['total'] or 0

    weekly_study = StudySession.objects.filter(
        user=request.user,
        start_time__gte=week_start
    ).aggregate(total=Sum('duration'))['total'] or 0

    daily_progress = min(100, int((daily_study / settings.daily_goal) * 100) if settings.daily_goal else 0)
    weekly_progress = min(100, int((weekly_study / settings.weekly_goal) * 100) if settings.weekly_goal else 0)

    upcoming_deadlines = Task.objects.filter(
        user=request.user,
        completed=False,
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timedelta(days=3)
    ).order_by('due_date')[:5]

    recent_sessions = StudySession.objects.filter(
        user=request.user
    ).order_by('-start_time')[:5]

    productivity_stats = StudySession.objects.filter(
        user=request.user,
        start_time__gte=timezone.now() - timedelta(days=30)
    ).aggregate(
        avg_score=Avg('productivity_score'),
        total_hours=Sum('duration') / 60
    )

    context = {
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_sessions': recent_sessions,
        'daily_study': daily_study,
        'weekly_study': weekly_study,
        'daily_progress': daily_progress,
        'weekly_progress': weekly_progress,
        'productivity_stats': productivity_stats,
        'settings': settings,
    }

    return render(request, 'planner/dashboard.html', context)

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()

            # Sync task to MongoDB
            try:
                from tasks.models import Task as MongoTask
                import datetime

                # Create new MongoDB task
                mongo_task = MongoTask(
                    user_id=request.user.id,
                    username=request.user.username,
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    category=task.category,
                    due_date=task.due_date,
                    completed=task.completed,
                    estimated_duration=task.estimated_duration,
                    django_id=task.id,
                    created_at=task.created_at,
                    updated_at=task.updated_at
                )
                mongo_task.save()
            except Exception as e:
                print(f"Error syncing task to MongoDB: {e}")

            messages.success(request, 'Task created successfully!')
            return redirect('dashboard')
    else:
        form = TaskForm()

    return render(request, 'planner/task_form.html', {
        'form': form,
        'title': 'Create New Task'
    })

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()

            # Sync task to MongoDB
            try:
                from tasks.models import Task as MongoTask
                import datetime

                # Find the corresponding MongoDB task
                mongo_task = MongoTask.objects(django_id=task.id).first()

                if mongo_task:
                    # Update existing MongoDB task
                    mongo_task.title = updated_task.title
                    mongo_task.description = updated_task.description
                    mongo_task.priority = updated_task.priority
                    mongo_task.category = updated_task.category
                    mongo_task.due_date = updated_task.due_date
                    mongo_task.completed = updated_task.completed
                    mongo_task.estimated_duration = updated_task.estimated_duration
                    mongo_task.updated_at = datetime.datetime.now()
                    mongo_task.save()
                else:
                    # Create new MongoDB task
                    mongo_task = MongoTask(
                        user_id=request.user.id,
                        username=request.user.username,
                        title=updated_task.title,
                        description=updated_task.description,
                        priority=updated_task.priority,
                        category=updated_task.category,
                        due_date=updated_task.due_date,
                        completed=updated_task.completed,
                        estimated_duration=updated_task.estimated_duration,
                        django_id=updated_task.id,
                        created_at=updated_task.created_at,
                        updated_at=updated_task.updated_at
                    )
                    mongo_task.save()
            except Exception as e:
                print(f"Error syncing task to MongoDB: {e}")

            messages.success(request, 'Task updated successfully!')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)

    return render(request, 'planner/task_form.html', {
        'form': form,
        'title': 'Update Task',
        'task': task
    })

@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.completed = not task.completed
    task.save()

    # Sync task to MongoDB
    try:
        from tasks.models import Task as MongoTask
        import datetime

        # Find the corresponding MongoDB task
        mongo_task = MongoTask.objects(django_id=task.id).first()

        if mongo_task:
            # Update existing MongoDB task
            mongo_task.completed = task.completed
            mongo_task.updated_at = datetime.datetime.now()
            mongo_task.save()
        else:
            # Create new MongoDB task
            mongo_task = MongoTask(
                user_id=task.user.id,
                username=task.user.username,
                title=task.title,
                description=task.description,
                priority=task.priority,
                category=task.category,
                due_date=task.due_date,
                completed=task.completed,
                estimated_duration=task.estimated_duration,
                django_id=task.id,
                created_at=task.created_at,
                updated_at=datetime.datetime.now()
            )
            mongo_task.save()
    except Exception as e:
        print(f"Error syncing task to MongoDB: {e}")

    action = 'completed' if task.completed else 'marked as pending'
    messages.success(request, f'Task "{task.title}" {action}.')

    return redirect('dashboard')

@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)

    # Delete from MongoDB first
    try:
        from tasks.models import Task as MongoTask

        # Find and delete the corresponding MongoDB task
        mongo_task = MongoTask.objects(django_id=task.id).first()
        if mongo_task:
            mongo_task.delete()
    except Exception as e:
        print(f"Error deleting task from MongoDB: {e}")

    # Then delete from Django
    task.delete()

    messages.success(request, 'Task deleted successfully.')
    return redirect('dashboard')

@login_required
def pomodoro_timer(request):
    settings = request.user.settings
    active_task = Task.objects.filter(
        user=request.user,
        completed=False
    ).order_by('-priority', 'due_date').first()

    # Get all incomplete tasks for the task selection dropdown
    tasks = Task.objects.filter(
        user=request.user,
        completed=False
    ).order_by('-priority', 'due_date')

    recent_sessions = TimerSession.objects.filter(
        user=request.user
    ).order_by('-start_time')[:10]

    return render(request, 'planner/pomodoro.html', {
        'settings': settings,
        'active_task': active_task,
        'tasks': tasks,
        'recent_sessions': recent_sessions
    })

@login_required
def timer_statistics(request):
    # Calculate date ranges
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Daily statistics
    daily_stats = {
        'total_time': TimerSession.objects.filter(
            user=request.user,
            start_time__date=today
        ).aggregate(total=Sum('duration'))['total'] or 0,
        'sessions': TimerSession.objects.filter(
            user=request.user,
            start_time__date=today
        ).count(),
        'avg_session': TimerSession.objects.filter(
            user=request.user,
            start_time__date=today
        ).aggregate(avg=Avg('duration'))['avg'] or 0
    }

    # Weekly statistics
    weekly_stats = {
        'total_time': TimerSession.objects.filter(
            user=request.user,
            start_time__date__gte=week_start
        ).aggregate(total=Sum('duration'))['total'] or 0,
        'sessions': TimerSession.objects.filter(
            user=request.user,
            start_time__date__gte=week_start
        ).count(),
        'avg_session': TimerSession.objects.filter(
            user=request.user,
            start_time__date__gte=week_start
        ).aggregate(avg=Avg('duration'))['avg'] or 0
    }

    # Monthly statistics
    monthly_stats = {
        'total_time': TimerSession.objects.filter(
            user=request.user,
            start_time__date__gte=month_start
        ).aggregate(total=Sum('duration'))['total'] or 0,
        'sessions': TimerSession.objects.filter(
            user=request.user,
            start_time__date__gte=month_start
        ).count(),
        'avg_session': TimerSession.objects.filter(
            user=request.user,
            start_time__date__gte=month_start
        ).aggregate(avg=Avg('duration'))['avg'] or 0
    }

    # Session distribution
    session_distribution = {
        'work_count': TimerSession.objects.filter(
            user=request.user,
            session_type='work'
        ).count(),
        'short_break_count': TimerSession.objects.filter(
            user=request.user,
            session_type='short_break'
        ).count(),
        'long_break_count': TimerSession.objects.filter(
            user=request.user,
            session_type='long_break'
        ).count()
    }

    total_sessions = (session_distribution['work_count'] +
                     session_distribution['short_break_count'] +
                     session_distribution['long_break_count'])

    if total_sessions > 0:
        session_distribution['work_percentage'] = (session_distribution['work_count'] / total_sessions) * 100
        session_distribution['short_break_percentage'] = (session_distribution['short_break_count'] / total_sessions) * 100
        session_distribution['long_break_percentage'] = (session_distribution['long_break_count'] / total_sessions) * 100
    else:
        session_distribution['work_percentage'] = 0
        session_distribution['short_break_percentage'] = 0
        session_distribution['long_break_percentage'] = 0

    # Get tasks with time spent
    tasks = Task.objects.filter(user=request.user).annotate(
        total_time=Sum('study_sessions__duration')
    ).order_by('-total_time')

    # Recent sessions
    recent_sessions = TimerSession.objects.filter(
        user=request.user
    ).order_by('-start_time')[:15]

    return render(request, 'planner/timer_statistics.html', {
        'daily_stats': daily_stats,
        'weekly_stats': weekly_stats,
        'monthly_stats': monthly_stats,
        'session_distribution': session_distribution,
        'tasks': tasks,
        'recent_sessions': recent_sessions
    })

@login_required
def study_analytics(request):
    # Get the current user
    user = request.user

    # Calculate date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # Get daily study data for the last 30 days
    daily_study = (
        StudySession.objects.filter(
            user=user,
            start_time__date__gte=thirty_days_ago
        )
        .annotate(day=TruncDay('start_time'))
        .values('day')
        .annotate(
            total_duration=Sum('duration'),
            avg_productivity=Avg('productivity_score')
        )
        .order_by('day')
    )

    # Get category distribution data
    category_data = (
        StudySession.objects.filter(
            user=user,
            task__isnull=False
        )
        .values('task__category')
        .annotate(total_duration=Sum('duration'))
        .order_by('-total_duration')
    )

    # Get productivity statistics
    productivity_stats = (
        StudySession.objects.filter(
            user=user,
            productivity_score__isnull=False
        )
        .values('productivity_score')
        .annotate(
            count=Count('id'),
            avg_duration=Avg('duration')
        )
        .order_by('productivity_score')
    )

    # Get recent study sessions
    recent_sessions = StudySession.objects.filter(
        user=user
    ).order_by('-start_time')[:10]

    context = {
        'daily_study': json.dumps(list(daily_study)),
        'category_data': json.dumps(list(category_data)),
        'productivity_stats': json.dumps(list(productivity_stats)),
        'recent_sessions': recent_sessions,
    }

    return render(request, 'planner/analytics.html', context)

@login_required
def calendar_view(request):
    return render(request, 'planner/calendar.html')

@login_required
def user_settings(request):
    settings = get_object_or_404(UserSettings, user=request.user)

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            updated_settings = form.save()

            # Sync user settings to MongoDB
            try:
                from tasks.sync_utils import sync_user_settings_to_mongodb
                sync_user_settings_to_mongodb(updated_settings)
            except Exception as e:
                print(f"Error syncing user settings to MongoDB: {e}")

            messages.success(request, 'Settings updated successfully!')
            return redirect('user-settings')
    else:
        form = UserSettingsForm(instance=settings)

    return render(request, 'planner/settings.html', {
        'form': form,
        'settings': settings
    })

@login_required
def task_timeline(request):
    # Get tasks ordered by due date
    tasks = Task.objects.filter(
        user=request.user,
        due_date__isnull=False
    ).order_by('due_date')

    # Group tasks by date
    tasks_by_date = {}
    for task in tasks:
        date_str = task.due_date.strftime('%Y-%m-%d')
        if date_str not in tasks_by_date:
            tasks_by_date[date_str] = []
        tasks_by_date[date_str].append(task)

    return render(request, 'planner/timeline.html', {
        'tasks_by_date': tasks_by_date
    })

@login_required
def smart_schedule(request):
    tasks = Task.objects.filter(
        user=request.user,
        completed=False
    ).order_by('-priority', 'due_date')

    productive_time = request.user.settings.most_productive_time.lower()

    time_blocks = {
        'morning': {'duration': 120, 'tasks': []},
        'afternoon': {'duration': 180, 'tasks': []},
        'evening': {'duration': 90, 'tasks': []}
    }

    remaining_tasks = []
    for task in tasks:
        allocated = False

        # First try to allocate high priority tasks to productive time
        if task.priority == 'H' and productive_time in time_blocks:
            if task.estimated_duration <= time_blocks[productive_time]['duration']:
                time_blocks[productive_time]['tasks'].append(task)
                time_blocks[productive_time]['duration'] -= task.estimated_duration
                allocated = True

        # Then try to allocate to any available time block
        if not allocated:
            for block_name, block in time_blocks.items():
                if task.estimated_duration <= block['duration']:
                    block['tasks'].append(task)
                    block['duration'] -= task.estimated_duration
                    allocated = True
                    break

        if not allocated:
            remaining_tasks.append(task)

    return render(request, 'planner/smart_schedule.html', {
        'schedule': {
            'morning': time_blocks['morning']['tasks'],
            'afternoon': time_blocks['afternoon']['tasks'],
            'evening': time_blocks['evening']['tasks']
        },
        'remaining_time': {
            'morning': time_blocks['morning']['duration'],
            'afternoon': time_blocks['afternoon']['duration'],
            'evening': time_blocks['evening']['duration']
        },
        'remaining_tasks': remaining_tasks,
        'productive_time': productive_time
    })

@login_required
def priority_based_tasks(request):
    productive_time = request.user.settings.most_productive_time

    tasks = Task.objects.filter(
        user=request.user,
        completed=False
    ).order_by('-priority', 'due_date')[:8]

    return render(request, 'planner/priority_tasks.html', {
        'tasks': tasks,
        'productive_time': productive_time
    })


@login_required
def eisenhower_matrix(request):
    tasks = Task.objects.filter(user=request.user, completed=False)

    matrix = {
        'urgent_important': tasks.filter(
            Q(priority='H') &
            (Q(due_date__isnull=True) | Q(due_date__lte=timezone.now() + timedelta(days=3)))
        ),
        'not_urgent_important': tasks.filter(
            Q(priority='H') &
            Q(due_date__gt=timezone.now() + timedelta(days=3))
        ),
        'urgent_not_important': tasks.filter(
            Q(priority__in=['M', 'L']) &
            (Q(due_date__isnull=True) | Q(due_date__lte=timezone.now() + timedelta(days=3)))
        ),
        'not_urgent_not_important': tasks.filter(
            Q(priority__in=['M', 'L']) &
            Q(due_date__gt=timezone.now() + timedelta(days=3))
        )
    }

    quadrant_counts = {
        'q1': matrix['urgent_important'].count(),
        'q2': matrix['not_urgent_important'].count(),
        'q3': matrix['urgent_not_important'].count(),
        'q4': matrix['not_urgent_not_important'].count(),
    }

    return render(request, 'planner/eisenhower_matrix.html', {
        'matrix': matrix,
        'quadrant_counts': quadrant_counts
    })

@require_POST
@login_required
def update_task_quadrant(request):
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_quadrant = data.get('quadrant')

        if not task_id or not new_quadrant:
            return JsonResponse({'error': 'Missing task_id or quadrant'}, status=400)

        task = get_object_or_404(Task, id=task_id, user=request.user)

        # Update task based on quadrant
        if new_quadrant == 'urgent_important':
            task.priority = 'H'
            if not task.due_date or task.due_date > timezone.now() + timedelta(days=3):
                task.due_date = timezone.now() + timedelta(days=1)
        elif new_quadrant == 'not_urgent_important':
            task.priority = 'H'
            task.due_date = timezone.now() + timedelta(days=7)
        elif new_quadrant == 'urgent_not_important':
            task.priority = 'M'
            if not task.due_date or task.due_date > timezone.now() + timedelta(days=3):
                task.due_date = timezone.now() + timedelta(days=1)
        elif new_quadrant == 'not_urgent_not_important':
            task.priority = 'L'
            task.due_date = timezone.now() + timedelta(days=14)
        else:
            return JsonResponse({'error': 'Invalid quadrant'}, status=400)

        task.save()

        # Sync with MongoDB directly
        try:
            from tasks.models import Task as MongoTask
            import datetime

            # Find the corresponding MongoDB task
            mongo_task = MongoTask.objects(django_id=task_id).first()

            if mongo_task:
                # Update existing MongoDB task
                mongo_task.title = task.title
                mongo_task.description = task.description
                mongo_task.priority = task.priority
                mongo_task.category = task.category
                mongo_task.due_date = task.due_date
                mongo_task.completed = task.completed
                mongo_task.estimated_duration = task.estimated_duration
                mongo_task.updated_at = datetime.datetime.now()
            else:
                # Create new MongoDB task
                mongo_task = MongoTask(
                    user_id=request.user.id,
                    username=request.user.username,
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    category=task.category,
                    due_date=task.due_date,
                    completed=task.completed,
                    estimated_duration=task.estimated_duration,
                    django_id=task.id
                )

            # Save the MongoDB task
            mongo_task.save()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error syncing to MongoDB: {e}")

        # Get updated quadrant counts
        tasks = Task.objects.filter(user=request.user, completed=False)
        quadrant_counts = {
            'q1': tasks.filter(
                Q(priority='H') &
                (Q(due_date__isnull=True) | Q(due_date__lte=timezone.now() + timedelta(days=3)))
            ).count(),
            'q2': tasks.filter(
                Q(priority='H') &
                Q(due_date__gt=timezone.now() + timedelta(days=3))
            ).count(),
            'q3': tasks.filter(
                Q(priority__in=['M', 'L']) &
                (Q(due_date__isnull=True) | Q(due_date__lte=timezone.now() + timedelta(days=3)))
            ).count(),
            'q4': tasks.filter(
                Q(priority__in=['M', 'L']) &
                Q(due_date__gt=timezone.now() + timedelta(days=3))
            ).count()
        }

        return JsonResponse({
            'status': 'success',
            'quadrant_counts': quadrant_counts
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)