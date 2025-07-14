from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Pages publiques
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('reports/', views.public_reports_view, name='public_reports'),
    path('reports/<int:pk>/', views.public_report_detail_view, name='public_report_detail'),
    path('contact/', views.contact_view, name='contact'),
    
    # Pages authentifiées
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('create/', views.create_report_view, name='create'),
    path('my-reports/', views.my_reports_view, name='my_reports'),
    path('report/<int:pk>/', views.report_detail_view, name='detail'),
    path('report/<int:pk>/comment/', views.add_comment_view, name='add_comment'),
    path('report/<int:pk>/comment/<int:comment_id>/edit/', views.edit_comment_view, name='edit_comment'),
    path('report/<int:pk>/comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
    path('report/<int:pk>/update-admin/', views.update_report_admin_view, name='update_admin'),
    
    # Pages admin supplémentaires
    path('admin/reports/', views.admin_reports_list_view, name='admin_reports_list'),
    path('admin/users/', views.admin_users_list_view, name='admin_users_list'),
    path('admin/analytics/', views.admin_analytics_view, name='admin_analytics'),
    path('admin/categories/add/', views.add_category_view, name='add_category'),
    # Suppression des routes custom admin catégories
]