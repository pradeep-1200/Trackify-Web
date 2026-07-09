from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('H', 'High'),
        ('M', 'Medium'),
        ('L', 'Low'),
    ]
    
    CATEGORY_CHOICES = [
        ('STUDY', 'Study'),
        ('WORK', 'Work'),
        ('PERSONAL', 'Personal'),
        ('HEALTH', 'Health'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='STUDY')
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='M')
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated duration in minutes",
        default=60,
        validators=[MinValueValidator(1)]
    )
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['completed', '-priority', 'due_date']
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"

    @property
    def is_overdue(self):
        return not self.completed and self.due_date and timezone.now() > self.due_date

    def get_priority_badge_class(self):
        return {
            'H': 'bg-red-100 text-red-800',
            'M': 'bg-yellow-100 text-yellow-800',
            'L': 'bg-green-100 text-green-800'
        }.get(self.priority, 'bg-gray-100 text-gray-800')

class TimerSession(models.Model):
    SESSION_TYPES = [
        ('WORK', 'Work Session'),
        ('SHORT_BREAK', 'Short Break'),
        ('LONG_BREAK', 'Long Break'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timer_sessions')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    session_type = models.CharField(max_length=15, choices=SESSION_TYPES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['session_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_session_type_display()} ({self.duration}s)"

class StudySession(models.Model):
    PRODUCTIVITY_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Medium'),
        (4, 'High'),
        (5, 'Very High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='study_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    productivity_score = models.PositiveSmallIntegerField(
        choices=PRODUCTIVITY_CHOICES,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    distractions = models.PositiveIntegerField(
        default=0,
        help_text="Number of distractions during session"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['productivity_score']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.duration}min (Score: {self.productivity_score})"

class UserSettings(models.Model):
    TIME_CHOICES = [
        ('MORNING', 'Morning (5AM-12PM)'),
        ('AFTERNOON', 'Afternoon (12PM-5PM)'),
        ('EVENING', 'Evening (5PM-12AM)'),
        ('NIGHT', 'Night (12AM-5AM)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    work_duration = models.PositiveIntegerField(
        default=25,
        validators=[MinValueValidator(5), MaxValueValidator(120)],
        help_text="Work duration in minutes"
    )
    short_break_duration = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Short break duration in minutes"
    )
    long_break_duration = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Long break duration in minutes"
    )
    long_break_interval = models.PositiveIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Number of work sessions before long break"
    )
    most_productive_time = models.CharField(
        max_length=10,
        choices=TIME_CHOICES,
        default='MORNING'
    )
    enable_dark_mode = models.BooleanField(default=False)
    enable_sounds = models.BooleanField(default=True)
    daily_goal = models.PositiveIntegerField(
        default=120,
        validators=[MinValueValidator(15), MaxValueValidator(600)],
        help_text="Daily study goal in minutes"
    )
    weekly_goal = models.PositiveIntegerField(
        default=600,
        validators=[MinValueValidator(60), MaxValueValidator(3000)],
        help_text="Weekly study goal in minutes"
    )
    
    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"Settings for {self.user.username}"