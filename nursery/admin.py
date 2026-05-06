from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentClass, Student, Activity, Attendance, DailyReport, Notification


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role & Profile", {"fields": ("role", "profile_picture")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role & Profile", {"fields": ("role", "profile_picture")}),
    )
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'student_class', 'parent', 'profile_picture']
    list_filter = ['student_class']
    search_fields = ['name', 'parent__username']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher', 'timestamp']
    list_filter = ['teacher', 'timestamp']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    list_filter = ['status', 'date']


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher', 'date', 'mood', 'food', 'sleep']
    list_filter = ['mood', 'date']


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_type', 'teacher']
    # Exclude teacher from the form since teachers self-assign during registration
    exclude = ['teacher']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']


admin.site.register(User, CustomUserAdmin)