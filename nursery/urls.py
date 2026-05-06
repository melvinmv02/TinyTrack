from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Core
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('register-teacher/', views.register_teacher_view, name='register_teacher'),

    # Teacher views
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('daily-report/', views.daily_report, name='daily_report'),
    path('my-students/', views.my_students, name='my_students'),
    path('teacher-profile/', views.teacher_profile, name='teacher_profile'),

    # Parent views
    path('dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('dashboard/add-child/', views.add_child_view, name='add_child'),
    path('dashboard/edit-child-name/<int:child_id>/', views.edit_child_name_view, name='edit_child_name'),
    path('student-profile/', views.student_profile, name='student_profile'),
    path('attendance-history/', views.attendance_history, name='attendance_history'),
    path('timeline/', views.timeline_feed, name='timeline'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),

    # Chat
    path('messages/', views.chat_inbox, name='chat_inbox'),
    path('messages/<int:user_id>/', views.chat_thread, name='chat_thread'),
    path('messages/<int:user_id>/voice/', views.chat_send_voice, name='chat_send_voice'),
    path('messages/<int:user_id>/poll/', views.chat_poll, name='chat_poll'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
