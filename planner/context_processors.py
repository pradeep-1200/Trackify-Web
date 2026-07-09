from .models import UserSettings

def settings_context(request):
    if request.user.is_authenticated:
        settings = UserSettings.objects.get_or_create(user=request.user)[0]
        return {
            'user_settings': settings,
        }
    return {}