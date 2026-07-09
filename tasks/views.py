from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import datetime
from .models import Task as MongoTask
from planner.models import Task as DjangoTask
from planner.models import TimerSession as DjangoTimerSession
from planner.models import StudySession as DjangoStudySession
from .auth_models import MongoTimerSession, MongoStudySession
from django.shortcuts import get_object_or_404, render

@require_POST
@login_required
def sync_task_to_mongodb(request):
    """
    Sync a task from Django's ORM to MongoDB
    """
    try:
        data = json.loads(request.body)
        django_task_id = data.get('task_id')

        if not django_task_id:
            return JsonResponse({'error': 'Missing task_id'}, status=400)

        # Get the Django task
        django_task = get_object_or_404(DjangoTask, id=django_task_id, user=request.user)

        # Check if a MongoDB task with this django_id already exists
        mongo_task = MongoTask.objects(django_id=django_task_id).first()

        if mongo_task:
            # Update existing MongoDB task
            mongo_task.title = django_task.title
            mongo_task.description = django_task.description
            mongo_task.priority = django_task.priority
            mongo_task.category = django_task.category
            mongo_task.due_date = django_task.due_date
            mongo_task.completed = django_task.completed
            mongo_task.estimated_duration = django_task.estimated_duration
            mongo_task.updated_at = datetime.datetime.now()
        else:
            # Create new MongoDB task
            mongo_task = MongoTask(
                user_id=request.user.id,
                username=request.user.username,
                title=django_task.title,
                description=django_task.description,
                priority=django_task.priority,
                category=django_task.category,
                due_date=django_task.due_date,
                completed=django_task.completed,
                estimated_duration=django_task.estimated_duration,
                django_id=django_task.id
            )

        # Save the MongoDB task
        mongo_task.save()

        return JsonResponse({
            'status': 'success',
            'mongo_id': str(mongo_task.id)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required
def update_task_quadrant_mongodb(request):
    """
    Update a task's quadrant in MongoDB
    """
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_quadrant = data.get('quadrant')

        if not task_id or not new_quadrant:
            return JsonResponse({'error': 'Missing task_id or quadrant'}, status=400)

        # Get the Django task first to verify ownership
        django_task = get_object_or_404(DjangoTask, id=task_id, user=request.user)

        # Find the corresponding MongoDB task
        mongo_task = MongoTask.objects(django_id=task_id).first()

        if not mongo_task:
            # Create a new MongoDB task if it doesn't exist
            mongo_task = MongoTask(
                user_id=request.user.id,
                username=request.user.username,
                title=django_task.title,
                description=django_task.description,
                priority=django_task.priority,
                category=django_task.category,
                due_date=django_task.due_date,
                completed=django_task.completed,
                estimated_duration=django_task.estimated_duration,
                django_id=django_task.id
            )

        # Update task based on quadrant
        if new_quadrant == 'urgent_important':
            mongo_task.priority = 'H'
            if not mongo_task.due_date or mongo_task.due_date > datetime.datetime.now() + datetime.timedelta(days=3):
                mongo_task.due_date = datetime.datetime.now() + datetime.timedelta(days=1)
        elif new_quadrant == 'not_urgent_important':
            mongo_task.priority = 'H'
            mongo_task.due_date = datetime.datetime.now() + datetime.timedelta(days=7)
        elif new_quadrant == 'urgent_not_important':
            mongo_task.priority = 'M'
            if not mongo_task.due_date or mongo_task.due_date > datetime.datetime.now() + datetime.timedelta(days=3):
                mongo_task.due_date = datetime.datetime.now() + datetime.timedelta(days=1)
        elif new_quadrant == 'not_urgent_not_important':
            mongo_task.priority = 'L'
            mongo_task.due_date = datetime.datetime.now() + datetime.timedelta(days=14)
        else:
            return JsonResponse({'error': 'Invalid quadrant'}, status=400)

        mongo_task.updated_at = datetime.datetime.now()
        mongo_task.save()

        return JsonResponse({
            'status': 'success',
            'mongo_id': str(mongo_task.id)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required
def create_timer_session(request):
    """
    Create a timer session in MongoDB
    """
    try:
        data = json.loads(request.body)
        session_type = data.get('session_type')
        duration = data.get('duration')
        task_id = data.get('task_id')

        if not session_type or not duration:
            return JsonResponse({'error': 'Missing session_type or duration'}, status=400)

        # Get the task if provided
        task = None
        task_title = None
        if task_id:
            try:
                task = DjangoTask.objects.get(id=task_id, user=request.user)
                task_title = task.title
            except DjangoTask.DoesNotExist:
                pass

        # Create Django timer session
        start_time = datetime.datetime.now() - datetime.timedelta(seconds=int(duration))
        end_time = datetime.datetime.now()

        django_session = DjangoTimerSession.objects.create(
            user=request.user,
            task=task,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            session_type=session_type
        )

        # Create MongoDB timer session
        mongo_session = MongoTimerSession(
            user_id=request.user.id,
            username=request.user.username,
            session_type=session_type.lower(),
            duration=duration,
            task_id=task_id,
            task_title=task_title,
            start_time=start_time,
            end_time=end_time
        )
        mongo_session.save()

        return JsonResponse({
            'status': 'success',
            'django_id': django_session.id,
            'mongo_id': str(mongo_session.id)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required
def create_study_session(request):
    """
    Create a study session in MongoDB
    """
    try:
        data = json.loads(request.body)
        duration = data.get('duration')
        productivity_score = data.get('productivity_score')
        distractions = data.get('distractions', 0)
        task_id = data.get('task_id')

        if not duration or not productivity_score:
            return JsonResponse({'error': 'Missing duration or productivity_score'}, status=400)

        # Get the task if provided
        task = None
        task_title = None
        if task_id:
            try:
                task = DjangoTask.objects.get(id=task_id, user=request.user)
                task_title = task.title
            except DjangoTask.DoesNotExist:
                pass

        # Create Django study session
        start_time = datetime.datetime.now() - datetime.timedelta(minutes=int(duration))
        end_time = datetime.datetime.now()

        django_session = DjangoStudySession.objects.create(
            user=request.user,
            task=task,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            productivity_score=productivity_score,
            distractions=distractions
        )

        # Create MongoDB study session
        mongo_session = MongoStudySession(
            user_id=request.user.id,
            username=request.user.username,
            duration=duration,
            productivity_score=productivity_score,
            distractions=distractions,
            task_id=task_id,
            task_title=task_title,
            start_time=start_time,
            end_time=end_time
        )
        mongo_session.save()

        return JsonResponse({
            'status': 'success',
            'django_id': django_session.id,
            'mongo_id': str(mongo_session.id)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)