from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from itertools import groupby
import itertools


def _hour_label(dt):
    """Return a cross-platform hour string like '9:00 AM' from an aware datetime."""
    local = timezone.localtime(dt)
    # %-I is Linux, %#I is Windows; fall back gracefully
    try:
        return local.strftime('%-I:00 %p')
    except ValueError:
        return local.strftime('%#I:00 %p')


def _date_label(dt):
    """Return a date string like 'March 11, 2026'."""
    return timezone.localtime(dt).strftime('%B %d, %Y')

from .models import Activity, Student, Attendance, DailyReport, Notification, StudentClass as Class
from .forms import (
    ActivityForm, AttendanceForm, DailyReportForm,
    TeacherProfileForm, StudentProfilePictureForm,
    ParentRegistrationForm,
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def teacher_required(view_func):
    """Decorator: only allows users with role == 'teacher'."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'teacher':
            messages.error(request, "Access denied. Teachers only.")
            return redirect('/')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def parent_required(view_func):
    """Decorator: only allows users with role == 'parent'."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'parent':
            messages.error(request, "Access denied. Parents only.")
            return redirect('/')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _create_notification(parent_user, message, notif_type='activity'):
    """Helper to create a notification for a parent."""
    Notification.objects.create(
        recipient=parent_user,
        message=message,
        notification_type=notif_type,
    )


# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────

def home(request):
    return render(request, 'nursery/home.html')


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user, request)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return _redirect_by_role(user, request)
        else:
            return render(request, "nursery/login.html", {"error": "Invalid credentials."})

    return render(request, "nursery/login.html")


def _redirect_by_role(user, request=None):
    if user.role == "admin":
        return redirect('/admin/')
    elif user.role == "teacher":
        return redirect('teacher_dashboard')
    elif user.role == "parent":
        return redirect('parent_dashboard')
    # Unknown role — log out to clear the session, then back to home
    if request is not None:
        logout(request)
    return redirect('home')


def logout_view(request):
    logout(request)
    return redirect('home')


def register_view(request):
    """Parent self-registration — with optional child enrollment."""
    import json
    from .models import StudentClass as NurseryClass
    from .forms import validate_children_data

    if request.user.is_authenticated:
        return _redirect_by_role(request.user, request)

    classes = NurseryClass.objects.all().order_by('name')
    child_errors = []
    posted_children_json = '[]'

    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        children, child_errors = validate_children_data(request.POST)

        # Build posted_children list for re-population on error
        posted = []
        i = 1
        while True:
            name = request.POST.get(f'child_name_{i}', '').strip()
            age  = request.POST.get(f'child_age_{i}', '').strip()
            cls  = request.POST.get(f'child_class_{i}', '').strip()
            if not name and not age and not cls:
                break
            posted.append({'name': name, 'age': age, 'cls': cls})
            i += 1
        posted_children_json = json.dumps(posted)

        if form.is_valid() and not child_errors:
            user = form.save()
            for child in children:
                Student.objects.create(
                    name=child['name'],
                    age=child['age'],
                    student_class=child['student_class'],
                    parent=user,
                )
            login(request, user)
            messages.success(request, f"Welcome to TinyTrack, {user.first_name or user.username}! Your account is ready.")
            return redirect('parent_dashboard')
    else:
        form = ParentRegistrationForm()

    return render(request, 'nursery/register.html', {
        'form': form,
        'classes': classes,
        'child_errors': child_errors,
        'posted_children_json': posted_children_json,
    })


def register_teacher_view(request):
    """Teacher self-registration."""
    from .forms import TeacherRegistrationForm
    
    if request.user.is_authenticated:
        return _redirect_by_role(request.user, request)

    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to TinyTrack, Teacher {user.first_name or user.username}! Your account is ready.")
            return redirect('teacher_dashboard')
    else:
        form = TeacherRegistrationForm()

    return render(request, 'nursery/register_teacher.html', {'form': form})



# ─────────────────────────────────────────────
# TEACHER DASHBOARD
# ─────────────────────────────────────────────

@teacher_required
def teacher_dashboard(request):
    # Get the class managed by this teacher
    teacher_class = getattr(request.user, 'managed_class', None)
    if not teacher_class:
        messages.error(request, "You are not assigned to any class.")
        return redirect('home')
    
    class_type = teacher_class.class_type
    students = Student.objects.filter(student_class=teacher_class).select_related(
        'student_class', 'parent'
    )

    form = ActivityForm(teacher=request.user)

    if request.method == "POST":
        form = ActivityForm(request.POST, request.FILES, teacher=request.user)

        if form.is_valid():
            activity = form.save(commit=False)
            activity.teacher = request.user
            activity.save()

            # Notify the parent
            student = activity.student
            _create_notification(
                student.parent,
                f"📸 New activity posted for {student.name} by {request.user.get_full_name() or request.user.username}.",
                notif_type='activity'
            )
            messages.success(request, "Activity posted successfully!")
            return redirect('teacher_dashboard')

    # Today's activities grouped by hour (ascending AM→PM)
    today = timezone.localdate()
    todays_activities = Activity.objects.filter(
        teacher=request.user,
        timestamp__date=today
    ).order_by('timestamp')

    activities_by_hour = [
        (hour, list(group))
        for hour, group in groupby(todays_activities, key=lambda a: _hour_label(a.timestamp))
    ]

    recent_reports = DailyReport.objects.filter(teacher=request.user).order_by('-date')[:5]

    current_tab = request.GET.get('tab', 'overview')
    all_activities = []
    if current_tab == 'activities':
        all_activities = Activity.objects.filter(teacher=request.user).order_by('-timestamp')
        # Group all activities by date
        activities_by_day = [
            (date_label, list(group))
            for date_label, group in groupby(all_activities, key=lambda a: _date_label(a.timestamp))
        ]
    else:
        activities_by_day = []

    return render(request, "nursery/teacher_dashboard.html", {
        'form': form,
        'activities_by_hour': activities_by_hour,
        'today_activity_count': todays_activities.count(),
        'recent_reports': recent_reports,
        'student_count': students.count(),
        'teacher_class': teacher_class,
        'class_type': class_type,
        'current_tab': current_tab,
        'activities_by_day': activities_by_day,
    })


# ─────────────────────────────────────────────
# TEACHER – MY STUDENTS
# ─────────────────────────────────────────────

@teacher_required
def my_students(request):
    students = Student.objects.filter(
        student_class__teacher=request.user
    ).select_related('student_class', 'parent')

    return render(request, 'nursery/student_list.html', {
        'students': students,
    })


# ─────────────────────────────────────────────
# TEACHER – MARK ATTENDANCE
# ─────────────────────────────────────────────

@teacher_required
def mark_attendance(request):
    from datetime import date as date_cls
    students = Student.objects.filter(student_class__teacher=request.user).order_by('name')

    if request.method == "POST":
        attendance_date_str = request.POST.get('attendance_date')
        try:
            from datetime import datetime
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date. Please try again.")
            return redirect('mark_attendance')

        # Checkboxes: present_<student_id> is in POST only when checked
        for student in students:
            key = f'present_{student.pk}'
            status = 'Present' if key in request.POST else 'Absent'
            Attendance.objects.update_or_create(
                student=student, date=attendance_date,
                defaults={'status': status}
            )
            # Notify parents
            _create_notification(
                student.parent,
                f"📋 Attendance for {student.name} on {attendance_date}: {status}.",
                notif_type='attendance'
            )

        messages.success(request, f"Attendance for {attendance_date.strftime('%B %d, %Y')} saved successfully!")
        return redirect('mark_attendance')

    today = date_cls.today()
    attendance_records = Attendance.objects.filter(
        student__student_class__teacher=request.user
    ).select_related('student').order_by('-date')[:30]

    return render(request, "nursery/attendance.html", {
        'students': students,
        'today': today,
        'attendance_records': attendance_records,
    })


# ─────────────────────────────────────────────
# TEACHER – DAILY REPORT
# ─────────────────────────────────────────────

@teacher_required
def daily_report(request):
    students = Student.objects.filter(student_class__teacher=request.user)

    teacher_class = getattr(request.user, 'managed_class', None)
    class_type = teacher_class.class_type if teacher_class else 'nursery'
    form = DailyReportForm(class_type=class_type)
    form.fields['student'].queryset = students

    teacher_class = getattr(request.user, 'managed_class', None)
    class_type = teacher_class.class_type if teacher_class else 'nursery'
    
    if request.method == "POST":
        form = DailyReportForm(request.POST, class_type=class_type)
        form.fields['student'].queryset = students

        if form.is_valid():
            report = form.save(commit=False)
            report.teacher = request.user
            report.save()

            # Notify parent
            student = report.student
            _create_notification(
                student.parent,
                f"📝 Daily report for {student.name} ({report.date}) is ready. Mood: {report.mood}.",
                notif_type='report'
            )
            messages.success(request, "Daily report submitted!")
            return redirect('daily_report')

    reports = DailyReport.objects.filter(teacher=request.user).order_by('-date')[:10]

    return render(request, 'nursery/daily_report.html', {
        'form': form,
        'reports': reports,
    })


# ─────────────────────────────────────────────
# TEACHER – PROFILE PICTURE UPLOAD
# ─────────────────────────────────────────────

@teacher_required
def teacher_profile(request):
    form = TeacherProfileForm(instance=request.user)

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('teacher_profile')

    return render(request, 'nursery/teacher_profile.html', {'form': form})


# ─────────────────────────────────────────────
# PARENT DASHBOARD
# ─────────────────────────────────────────────

@parent_required
def parent_dashboard(request):
    children = Student.objects.filter(parent=request.user).select_related(
        'student_class', 'student_class__teacher'
    )

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    return render(request, "nursery/parent_dashboard.html", {
        'children': children,
        'unread_notif_count': unread_count,
    })


@parent_required
def add_child_view(request):
    """Allow parents to add another child from their dashboard."""
    from .forms import AddChildForm
    if request.method == 'POST':
        form = AddChildForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user
            child.save()
            messages.success(request, f"{child.name} has been successfully registered!")
            return redirect('parent_dashboard')
    else:
        form = AddChildForm()
    
    return render(request, 'nursery/add_child.html', {'form': form})


@parent_required
def edit_child_name_view(request, child_id):
    """Allow parents to edit their child's name."""
    from .forms import StudentNameEditForm
    student = get_object_or_404(Student, pk=child_id, parent=request.user)
    
    if request.method == 'POST':
        form = StudentNameEditForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Child's name updated to {student.name}!")
            return redirect('parent_dashboard')
    else:
        form = StudentNameEditForm(instance=student)
    
    return render(request, 'nursery/edit_child_name.html', {'form': form, 'student': student})


# ─────────────────────────────────────────────
# PARENT – STUDENT PROFILE
# ─────────────────────────────────────────────

@parent_required
def student_profile(request):
    # Support multiple children – default to first; ?child=<id> to switch
    child_id = request.GET.get('child')
    if child_id:
        student = get_object_or_404(Student, pk=child_id, parent=request.user)
    else:
        student = Student.objects.filter(parent=request.user).first()
        if not student:
            raise Http404("No student found for this parent.")

    # Latest daily report
    latest_report = DailyReport.objects.filter(student=student).first()

    return render(request, 'nursery/student_profile.html', {
        'student': student,
        'latest_report': latest_report,
    })


# ─────────────────────────────────────────────
# PARENT – ATTENDANCE HISTORY
# ─────────────────────────────────────────────

@parent_required
def attendance_history(request):
    child_id = request.GET.get('child')
    children = Student.objects.filter(parent=request.user)

    if child_id:
        student = get_object_or_404(Student, pk=child_id, parent=request.user)
    else:
        student = children.first()

    records = Attendance.objects.none()
    if student:
        records = Attendance.objects.filter(student=student).order_by('-date')

    present_count = records.filter(status='Present').count()
    absent_count = records.filter(status='Absent').count()

    return render(request, 'nursery/attendance_history.html', {
        'student': student,
        'records': records,
        'children': children,
        'present_count': present_count,
        'absent_count': absent_count,
    })


# ─────────────────────────────────────────────
# PARENT – TIMELINE FEED
# ─────────────────────────────────────────────

@parent_required
def timeline_feed(request):
    from datetime import datetime, date as date_cls
    child_id = request.GET.get('child')
    selected_date_str = request.GET.get('date')  # format: YYYY-MM-DD
    children = Student.objects.filter(parent=request.user)

    if child_id:
        student = get_object_or_404(Student, pk=child_id, parent=request.user)
    else:
        student = children.first()

    activities = []
    reports = []
    available_dates = []  # list of date objects that have any entry

    if student:
        activities = list(
            Activity.objects.filter(student=student).order_by('-timestamp')
        )
        reports = list(
            DailyReport.objects.filter(student=student).order_by('-date')
        )
        # Collect every date that has at least one entry
        date_set = set()
        for a in activities:
            date_set.add(timezone.localtime(a.timestamp).date())
        for r in reports:
            date_set.add(r.date)
        available_dates = sorted(date_set, reverse=True)

    # Determine the selected date (default: most recent)
    selected_date = None
    if selected_date_str:
        try:
            selected_date = date_cls.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = None
    if selected_date is None and available_dates:
        selected_date = available_dates[0]

    # Combine and sort by datetime, filtering to selected_date only
    timeline = []
    for a in activities:
        a_date = timezone.localtime(a.timestamp).date()
        if selected_date is None or a_date == selected_date:
            timeline.append({'type': 'activity', 'obj': a, 'dt': a.timestamp})
    for r in reports:
        if selected_date is None or r.date == selected_date:
            dt = timezone.make_aware(datetime.combine(r.date, datetime.min.time()))
            timeline.append({'type': 'report', 'obj': r, 'dt': dt})

    timeline.sort(key=lambda x: x['dt'], reverse=True)

    # Group by date → then by hour within each date
    timeline_by_day = []
    for date_label, day_items in groupby(timeline, key=lambda x: _date_label(x['dt'])):
        day_list = list(day_items)
        hours = [
            (hour, list(group))
            for hour, group in groupby(day_list, key=lambda x: _hour_label(x['dt']))
        ]
        timeline_by_day.append((date_label, hours))

    # Build calendar context — respect ?cal=YYYY-MM for month browsing
    import calendar as cal_mod
    cal_param = request.GET.get('cal', '')  # e.g. "2026-04"
    cal_year = None
    cal_month = None
    if cal_param:
        try:
            cal_parts = cal_param.split('-')
            cal_year = int(cal_parts[0])
            cal_month = int(cal_parts[1])
        except (IndexError, ValueError):
            cal_year = cal_month = None
    if not cal_year or not cal_month:
        # Default: show the month of the selected date (or current month)
        if selected_date:
            cal_year, cal_month = selected_date.year, selected_date.month
        else:
            today = timezone.localdate()
            cal_year, cal_month = today.year, today.month
    # Weeks for the calendar grid
    cal_weeks = cal_mod.monthcalendar(cal_year, cal_month)
    cal_month_name = date_cls(cal_year, cal_month, 1).strftime('%B %Y')
    available_dates_iso = [d.isoformat() for d in available_dates]

    return render(request, 'nursery/timeline.html', {
        'timeline_by_day': timeline_by_day,
        'student': student,
        'children': children,
        'selected_date': selected_date,
        'selected_date_iso': selected_date.isoformat() if selected_date else '',
        'available_dates_iso': available_dates_iso,
        'cal_year': cal_year,
        'cal_month': cal_month,
        'cal_month_name': cal_month_name,
        'cal_weeks': cal_weeks,
        'child_id': child_id or '',
    })


# ─────────────────────────────────────────────
# PARENT – NOTIFICATIONS
# ─────────────────────────────────────────────

@parent_required
def notifications_view(request):
    notifs = Notification.objects.filter(recipient=request.user)
    # Mark all as read on visit
    notifs.filter(is_read=False).update(is_read=True)

    return render(request, 'nursery/notifications.html', {
        'notifications': notifs,
    })


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notifications')


# ─────────────────────────────────────────────
# CHAT – INBOX
# ─────────────────────────────────────────────

@login_required
def chat_inbox(request):
    from .models import ChatMessage
    from django.db.models import Q, Max

    if request.user.role == 'teacher':
        # Find all parents whose child is in this teacher's class
        students = Student.objects.filter(
            student_class__teacher=request.user
        ).select_related('parent')
        # Unique parents (dedup in case multiple children)
        seen = set()
        contacts = []
        for s in students:
            if s.parent_id not in seen:
                seen.add(s.parent_id)
                contacts.append(s.parent)

    elif request.user.role == 'parent':
        # Parent's contact is their child(ren)'s teacher(s)
        students = Student.objects.filter(parent=request.user).select_related(
            'student_class__teacher'
        )
        seen = set()
        contacts = []
        for s in students:
            t = s.student_class.teacher
            if t and t.id not in seen:
                seen.add(t.id)
                contacts.append(t)
    else:
        contacts = []

    # Annotate with last message and unread count
    conversation_list = []
    for contact in contacts:
        last_msg = ChatMessage.objects.filter(
            Q(sender=request.user, recipient=contact) |
            Q(sender=contact, recipient=request.user)
        ).last()
        unread = ChatMessage.objects.filter(
            sender=contact, recipient=request.user, is_read=False
        ).count()
        conversation_list.append({
            'contact': contact,
            'last_msg': last_msg,
            'unread': unread,
        })

    # Sort: conversations with messages first (by last message time)
    from datetime import datetime
    conversation_list.sort(
        key=lambda x: x['last_msg'].timestamp if x['last_msg'] else timezone.make_aware(datetime.min),
        reverse=True
    )

    return render(request, 'nursery/chat_inbox.html', {
        'conversation_list': conversation_list,
    })


# ─────────────────────────────────────────────
# CHAT – THREAD
# ─────────────────────────────────────────────

@login_required
def chat_thread(request, user_id):
    from .models import ChatMessage
    from django.http import JsonResponse
    from django.db.models import Q

    other_user = get_object_or_404(
        __import__('nursery.models', fromlist=['User']).User,
        pk=user_id
    )
    # Access guard
    _assert_chat_allowed(request.user, other_user)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            ChatMessage.objects.create(
                sender=request.user,
                recipient=other_user,
                body=body,
            )
        return redirect('chat_thread', user_id=user_id)

    # Mark incoming messages as read
    ChatMessage.objects.filter(
        sender=other_user, recipient=request.user, is_read=False
    ).update(is_read=True)

    messages_qs = ChatMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')

    return render(request, 'nursery/chat_thread.html', {
        'other_user': other_user,
        'messages': messages_qs,
    })


# ─────────────────────────────────────────────
# CHAT – SEND VOICE
# ─────────────────────────────────────────────

@login_required
def chat_send_voice(request, user_id):
    from .models import ChatMessage
    from django.http import JsonResponse
    from django.core.files.base import ContentFile

    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    other_user = get_object_or_404(
        __import__('nursery.models', fromlist=['User']).User,
        pk=user_id
    )
    _assert_chat_allowed(request.user, other_user)

    audio_blob = request.FILES.get('audio')
    if not audio_blob:
        return JsonResponse({'error': 'No audio'}, status=400)

    msg = ChatMessage.objects.create(
        sender=request.user,
        recipient=other_user,
        voice=audio_blob,
    )
    return JsonResponse({
        'ok': True,
        'id': msg.pk,
        'voice_url': msg.voice.url,
        'timestamp': msg.timestamp.isoformat(),
        'sender_id': request.user.pk,
        'sender_name': request.user.get_full_name() or request.user.username,
    })


# ─────────────────────────────────────────────
# CHAT – POLL (AJAX)
# ─────────────────────────────────────────────

@login_required
def chat_poll(request, user_id):
    from .models import ChatMessage
    from django.http import JsonResponse
    from django.db.models import Q
    import datetime

    other_user = get_object_or_404(
        __import__('nursery.models', fromlist=['User']).User,
        pk=user_id
    )

    after_str = request.GET.get('after', '')
    try:
        after_dt = datetime.datetime.fromisoformat(after_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        after_dt = None

    qs = ChatMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')

    if after_dt:
        qs = qs.filter(timestamp__gt=after_dt)

    # Mark polled incoming messages as read
    qs.filter(sender=other_user, recipient=request.user).update(is_read=True)

    data = []
    for m in qs:
        data.append({
            'id': m.pk,
            'sender_id': m.sender_id,
            'sender_name': m.sender.get_full_name() or m.sender.username,
            'body': m.body,
            'voice_url': m.voice.url if m.voice else None,
            'timestamp': m.timestamp.isoformat(),
        })

    return JsonResponse({'messages': data})


# ─────────────────────────────────────────────
# CHAT – HELPER
# ─────────────────────────────────────────────

def _assert_chat_allowed(me, other):
    """Raise 403 if me is not allowed to chat with other."""
    from django.core.exceptions import PermissionDenied
    from django.db.models import Q

    if me.role == 'teacher' and other.role == 'parent':
        allowed = Student.objects.filter(
            student_class__teacher=me, parent=other
        ).exists()
    elif me.role == 'parent' and other.role == 'teacher':
        allowed = Student.objects.filter(
            parent=me, student_class__teacher=other
        ).exists()
    else:
        allowed = False

    if not allowed:
        raise PermissionDenied("You are not allowed to chat with this user.")