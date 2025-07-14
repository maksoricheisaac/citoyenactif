from datetime import timedelta, datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

from .models import Report, Category, Comment, ContactMessage
from .forms import ReportForm, AdminReportForm, CommentForm, ContactForm
from accounts.models import User
from accounts.decorators import admin_required
from .forms_category import CategoryForm  # Ajouté pour le formulaire catégorie

# Pages publiques
def home_view(request):
    """Page d'accueil publique"""
    # Statistiques générales
    stats = {
        'total_reports': Report.objects.count(),
        'resolved_reports': Report.objects.filter(status='resolved').count(),
        'categories_count': Category.objects.count(),
        'active_users': User.objects.filter(reports__isnull=False).distinct().count(),
    }
    
    # Derniers signalements résolus (publics)
    recent_resolved = Report.objects.filter(status='resolved').order_by('-updated_at')[:6]
    
    # Catégories populaires
    popular_categories = Category.objects.annotate(
        report_count=Count('reports')
    ).order_by('-report_count')[:6]
    
    context = {
        'stats': stats,
        'recent_resolved': recent_resolved,
        'popular_categories': popular_categories,
    }
    return render(request, 'reports/home.html', context)

def about_view(request):
    """Page à propos"""
    return render(request, 'reports/about.html')

def public_reports_view(request):
    """Page publique de tous les signalements avec filtres et pagination"""
    reports = Report.objects.all().order_by('-updated_at')
    
    # Filtres
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    search = request.GET.get('search')
    
    if category_filter:
        reports = reports.filter(category_id=category_filter)
    if status_filter:
        reports = reports.filter(status=status_filter)
    if search:
        reports = reports.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(reports, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    STATUSES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolu'),
    ]

    # Statistiques dynamiques (sur tous les signalements)
    total_reports = reports.count()
    resolved_reports = reports.filter(status='resolved').count()
    resolution_rate = round((resolved_reports / total_reports * 100), 1) if total_reports else 0
    resolved_qs = reports.filter(status='resolved').exclude(created_at=None).exclude(updated_at=None)
    delais = []
    for r in resolved_qs:
        if r.updated_at and r.created_at:
            delais.append((r.updated_at - r.created_at).total_seconds())
    if delais:
        avg_seconds = sum(delais) / len(delais)
        avg_td = timedelta(seconds=avg_seconds)
        hours = int(avg_td.total_seconds() // 3600)
        minutes = int((avg_td.total_seconds() % 3600) // 60)
        avg_time = f"{hours}h{minutes:02d}"
    else:
        avg_time = 'N/A'
    stats = {
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'resolution_rate': resolution_rate,
        'avg_time': avg_time,
    }
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'STATUSES': STATUSES,
        'current_filters': {
            'category': category_filter,
            'status': status_filter,
            'search': search,
        },
        'stats': stats,
    }
    return render(request, 'reports/public_reports.html', context)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre message a bien été envoyé. Merci de nous avoir contactés !")
            return redirect('reports:contact')
        else:
            messages.error(request, "Une erreur est survenue. Merci de vérifier le formulaire.")
    else:
        form = ContactForm()
    return render(request, 'reports/contact.html', {'form': form})

@login_required
def dashboard_view(request):
    if request.user.is_admin:
        return redirect('reports:admin_dashboard')
    
    user_reports = Report.objects.filter(user=request.user).order_by('-created_at')
    
    # Statistiques utilisateur
    stats = {
        'total': user_reports.count(),
        'pending': user_reports.filter(status='pending').count(),
        'in_progress': user_reports.filter(status='in_progress').count(),
        'resolved': user_reports.filter(status='resolved').count(),
    }
    
    # Derniers signalements
    recent_reports = user_reports[:5]
    
    context = {
        'stats': stats,
        'recent_reports': recent_reports,
    }
    return render(request, 'reports/dashboard.html', context)

@admin_required
def admin_dashboard_view(request):
    reports = Report.objects.all().order_by('-created_at')
    users = User.objects.all()
    
    # Filtres
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')
    search = request.GET.get('search')
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    if category_filter:
        reports = reports.filter(category_id=category_filter)
    if priority_filter:
        reports = reports.filter(priority=priority_filter)
    if search:
        reports = reports.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques générales
    stats = {
        'total': Report.objects.count(),
        'pending': Report.objects.filter(status='pending').count(),
        'in_progress': Report.objects.filter(status='in_progress').count(),
        'resolved': Report.objects.filter(status='resolved').count(),
    }
    
    # Données pour les filtres
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'categories': categories,
        'users': users,
        'current_filters': {
            'status': status_filter,
            'category': category_filter,
            'priority': priority_filter,
            'search': search,
        }
    }
    return render(request, 'reports/admin_dashboard.html', context)

@login_required
def create_report_view(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            messages.success(request, 'Votre signalement a été créé avec succès!')
            return redirect('reports:detail', pk=report.pk)
    else:
        form = ReportForm()
    
    return render(request, 'reports/create_report.html', {'form': form})

@login_required
def report_detail_view(request, pk):
    report = get_object_or_404(Report, pk=pk)
    
    # Vérifier les permissions
    if not request.user.is_admin and report.user != request.user:
        messages.error(request, "Vous n'avez pas l'autorisation de voir ce signalement.")
        return redirect('reports:dashboard')
    
    # Formulaires
    comment_form = CommentForm()
    admin_form = None
    
    if request.user.is_admin:
        admin_form = AdminReportForm(instance=report)
    
    # Commentaires
    comments = report.comments.all()
    if not request.user.is_admin:
        comments = comments.filter(is_internal=False)
    
    context = {
        'report': report,
        'comments': comments,
        'comment_form': comment_form,
        'admin_form': admin_form,
    }
    return render(request, 'reports/report_detail.html', context)

@login_required
def my_reports_view(request):
    reports = Report.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    if category_filter:
        reports = reports.filter(category_id=category_filter)
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_filters': {
            'status': status_filter,
            'category': category_filter,
        }
    }
    return render(request, 'reports/my_reports.html', context)

@login_required
@require_POST
def add_comment_view(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.report = report
            if request.user.is_authenticated:
                comment.user = request.user
            # Seuls les admins peuvent créer des notes internes
            if not (request.user.is_authenticated and request.user.is_admin):
                comment.is_internal = False
            comment.save()
            messages.success(request, 'Commentaire ajouté avec succès!')
        else:
            messages.error(request, 'Erreur lors de l\'ajout du commentaire.')
        return redirect('reports:detail', pk=pk)
    else:
        form = CommentForm(user=request.user if request.user.is_authenticated else None)
    return redirect('reports:detail', pk=pk)

@admin_required
@require_POST
def update_report_admin_view(request, pk):
    report = get_object_or_404(Report, pk=pk)
    form = AdminReportForm(request.POST, instance=report)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Signalement mis à jour avec succès!')
    else:
        messages.error(request, 'Erreur lors de la mise à jour.')
    
    return redirect('reports:detail', pk=pk)

# Nouvelles vues pour l'admin
@admin_required
def admin_reports_list_view(request):
    """Liste des signalements pour l'admin"""
    reports = Report.objects.all().order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')
    search = request.GET.get('search')
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    if category_filter:
        reports = reports.filter(category_id=category_filter)
    if priority_filter:
        reports = reports.filter(priority=priority_filter)
    if search:
        reports = reports.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    categories = Category.objects.all()
    
    context = {
        'reports': reports[:50],  # Limiter pour la démo
        'categories': categories,
        'current_filters': {
            'status': status_filter,
            'category': category_filter,
            'priority': priority_filter,
            'search': search,
        }
    }
    return render(request, 'admin/reports_list.html', context)

@admin_required
def admin_users_list_view(request):
    """Liste des utilisateurs pour l'admin"""
    users = User.objects.all().order_by('-date_joined')
    stats = {
        'total': users.count(),
        'admins': users.filter(role='superadmin').count(),
        'citizens': users.filter(role='citizen').count(),
    }
    return render(request, 'admin/users_list.html', {'users': users, 'stats': stats})

@admin_required
def admin_analytics_view(request):
    """Page d'analytics pour l'admin"""
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    reports_this_month = Report.objects.filter(created_at__gte=month_start)
    total_reports = Report.objects.count()
    resolved = Report.objects.filter(status='resolved').count()
    resolution_rate = (resolved / total_reports * 100) if total_reports else 0
    avg_time = Report.objects.filter(status='resolved').aggregate(avg=Avg('updated_at'))['avg']
    users_count = User.objects.count()
    categories_count = Category.objects.count()
    context = {
        'reports_this_month': reports_this_month.count(),
        'resolution_rate': round(resolution_rate, 1),
        'avg_time': avg_time,
        'users_count': users_count,
        'categories_count': categories_count,
        'total_reports': total_reports,
    }
    return render(request, 'admin/analytics.html', context)

@admin_required
def add_category_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect('reports:admin_dashboard')
        else:
            messages.error(request, "Erreur dans le formulaire. Merci de corriger les champs.")
    else:
        form = CategoryForm()
    return render(request, 'reports/add_category.html', {'form': form})


def public_report_detail_view(request, pk):
    from django.shortcuts import get_object_or_404, redirect
    from .models import Report
    from .forms import CommentForm
    from django.contrib import messages
    report = get_object_or_404(Report, pk=pk)  # Affiche tous les statuts
    # Afficher uniquement les commentaires publics
    comments = report.comments.filter(is_internal=False).order_by('created_at')
    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.report = report
            if request.user.is_authenticated:
                comment.user = request.user
            comment.is_internal = False
            comment.save()
            messages.success(request, 'Commentaire ajouté avec succès!')
            return redirect('reports:public_report_detail', pk=pk)
    else:
        form = CommentForm(user=request.user if request.user.is_authenticated else None)
    context = {
        'report': report,
        'comments': comments,
        'comment_form': form,
    }
    return render(request, 'reports/public_report_detail.html', context)

@login_required
@require_http_methods(["POST"])
def edit_comment_view(request, pk, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, report_id=pk)
    if comment.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    form = CommentForm(request.POST, instance=comment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Commentaire modifié avec succès!')
    else:
        messages.error(request, 'Erreur lors de la modification du commentaire.')
    return redirect('reports:detail', pk=pk)

@login_required
@require_http_methods(["POST"])
def delete_comment_view(request, pk, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, report_id=pk)
    if comment.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    comment.delete()
    messages.success(request, 'Commentaire supprimé avec succès!')
    return redirect('reports:detail', pk=pk)