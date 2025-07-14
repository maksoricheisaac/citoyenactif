from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Report, Comment, ContactMessage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon', 'color', 'created_at')
    list_filter = ('color', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status_badge', 'priority_badge', 'user', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'description', 'location', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CommentInline]

    def status_badge(self, obj):
        color = {
            'pending': '#fde68a',  # jaune
            'in_progress': '#bfdbfe',  # bleu
            'resolved': '#bbf7d0',  # vert
            'rejected': '#fecaca',  # rouge
        }.get(obj.status, '#e5e7eb')
        text_color = {
            'pending': '#b45309',
            'in_progress': '#1d4ed8',
            'resolved': '#15803d',
            'rejected': '#b91c1c',
        }.get(obj.status, '#374151')
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
            color, text_color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    status_badge.allow_tags = True

    def priority_badge(self, obj):
        color = {
            'low': '#bbf7d0',
            'medium': '#fde68a',
            'high': '#fdba74',
            'urgent': '#fecaca',
        }.get(obj.priority, '#e5e7eb')
        text_color = {
            'low': '#15803d',
            'medium': '#b45309',
            'high': '#b45309',
            'urgent': '#b91c1c',
        }.get(obj.priority, '#374151')
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
            color, text_color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priorité'
    priority_badge.allow_tags = True

    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'description', 'category', 'photo')
        }),
        ('Localisation', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Gestion', {
            'fields': ('status', 'priority', 'assigned_to', 'admin_notes')
        }),
        ('Métadonnées', {
            'fields': ('user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('report', 'user', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('content', 'report__title', 'user__first_name')
    readonly_fields = ('created_at',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'subject', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'subject', 'message')
    list_filter = ('created_at',)