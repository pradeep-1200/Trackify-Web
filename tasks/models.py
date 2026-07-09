from mongoengine import Document, StringField, DateTimeField, ReferenceField, ListField, BooleanField, IntField
import datetime

# MongoDB models
class Task(Document):
    # User identification (stored as string since we can't use Django's User model directly)
    user_id = IntField(required=True)
    username = StringField(max_length=150)

    # Basic task information
    title = StringField(required=True, max_length=200)
    description = StringField()

    # Task categorization
    PRIORITY_CHOICES = ('H', 'M', 'L')  # High, Medium, Low
    priority = StringField(choices=PRIORITY_CHOICES, default='M')

    CATEGORY_CHOICES = ('STUDY', 'WORK', 'PERSONAL', 'HEALTH', 'OTHER')
    category = StringField(choices=CATEGORY_CHOICES, default='STUDY')

    # Dates and status
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    due_date = DateTimeField()
    completed = BooleanField(default=False)

    # Additional metadata
    tags = ListField(StringField(max_length=50))
    estimated_duration = IntField(default=60)  # in minutes

    # Django model ID for reference
    django_id = IntField()

    meta = {
        'collection': 'tasks',
        'indexes': [
            'user_id',
            'title',
            'priority',
            'created_at',
            'due_date',
            'completed',
            'django_id'
        ]
    }

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return not self.completed and self.due_date and datetime.datetime.now() > self.due_date
