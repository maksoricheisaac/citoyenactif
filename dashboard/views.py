from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from reports.models import Report, Comment, ContactMessage
from django.contrib.auth import get_user_model

User = get_user_model()

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

@login_required
@staff_required
def dashboard_view(request):
    stats = {
        'reports_count': Report.objects.count(),
        'users_count': User.objects.filter(is_staff=False).count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
        'comments_count': Comment.objects.count(),
        'messages_count': ContactMessage.objects.count(),
    }
    return render(request, 'dashboard/dashboard.html', {'stats': stats})
