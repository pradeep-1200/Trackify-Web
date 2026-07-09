from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Task, UserSettings

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your@email.com'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserSettings.objects.create(user=user)
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )

class TaskForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-input'
        }),
        required=False,
        input_formats=['%Y-%m-%dT%H:%M']
    )
    estimated_duration = forms.IntegerField(
        min_value=1,
        max_value=600,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Minutes'
        })
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'priority', 'due_date', 'estimated_duration']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Task title'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-input',
                'placeholder': 'Task description (optional)'
            }),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise ValidationError("Due date cannot be in the past.")
        return due_date

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            'work_duration', 
            'short_break_duration', 
            'long_break_duration',
            'long_break_interval',
            'most_productive_time',
            'enable_dark_mode',
            'enable_sounds',
            'daily_goal',
            'weekly_goal'
        ]
        widgets = {
            'work_duration': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 5,
                'max': 120
            }),
            'short_break_duration': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 30
            }),
            'long_break_duration': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 5,
                'max': 60
            }),
            'long_break_interval': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 10
            }),
            'most_productive_time': forms.Select(attrs={'class': 'form-input'}),
            'enable_dark_mode': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'enable_sounds': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'daily_goal': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 15,
                'max': 600
            }),
            'weekly_goal': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 60,
                'max': 3000
            }),
        }