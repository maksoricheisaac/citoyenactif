from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm
from .models import User
from .forms import AdminEmailLoginForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def login_view(request):
    if request.user.is_authenticated:
        # Redirige selon le rôle
        if hasattr(request.user, 'role') and request.user.role == 'superadmin':
            return redirect('reports:admin_dashboard')
        else:
            return redirect('reports:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name}!')
            # Redirige selon le rôle
            if hasattr(user, 'role') and user.role == 'superadmin':
                return redirect('reports:admin_dashboard')
            else:
                return redirect('reports:dashboard')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('reports:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Votre compte a été créé avec succès!')
            return redirect('reports:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    password_form = PasswordChangeForm(user=request.user)
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil mis à jour avec succès.')
                return redirect('accounts:profile')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            form = ProfileUpdateForm(instance=request.user)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mot de passe changé avec succès.')
                return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form, 'user': request.user, 'password_form': password_form})

def admin_login_view(request):
    if request.user.is_authenticated and getattr(request.user, 'is_admin', False):
        return redirect('reports:admin_dashboard')
    
    form = AdminEmailLoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.cleaned_data['user']
            # Promotion automatique pour accès admin Django natif
            if not user.is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])
            login(request, user)
            messages.success(request, f"Bienvenue {user.first_name} ! Vous êtes connecté en tant qu'administrateur.")
            return redirect('reports:admin_dashboard')
        else:
            # Ajout d'un message d'erreur global si le formulaire n'est pas valide
            messages.error(request, "Email ou mot de passe incorrect, ou accès non autorisé.")
    return render(request, 'admin/login.html', {'form': form})