from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', null=True, blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


# StudentClass Model (Renamed from Class)
class StudentClass(models.Model):
    CLASS_TYPE_CHOICES = (
        ('nursery', 'Nursery'),
        ('lkg', 'LKG'),
        ('ukg', 'UKG'),
    )
    name = models.CharField(max_length=100)
    class_type = models.CharField(max_length=20, choices=CLASS_TYPE_CHOICES, default='nursery')
    teacher = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='managed_class'
    )

    def __str__(self):
        return f"{self.name} ({self.get_class_type_display()})"


# Student Model
class Student(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    parent = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={'role': 'parent'},
        related_name='children'
    )
    student_class = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to='student_pictures/', null=True, blank=True
    )

    def __str__(self):
        return self.name


# Activity Model
class Activity(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'}
    )
    description = models.TextField()
    image = models.ImageField(upload_to='activity_images/', null=True, blank=True)
    file = models.FileField(upload_to='activity_files/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Activity for {self.student.name}"


# Attendance Model
class Attendance(models.Model):
    STATUS_CHOICES = [('Present', 'Present'), ('Absent', 'Absent')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        ordering = ['-date']
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"


# Daily Report Model
class DailyReport(models.Model):
    MOOD_CHOICES = [('Happy', 'Happy'), ('Neutral', 'Neutral'), ('Sad', 'Sad')]
    FOOD_CHOICES = [
        ('Ate Well', 'Ate Well'),
        ('Ate Little', 'Ate Little'),
        ('Did Not Eat', 'Did Not Eat'),
    ]
    SLEEP_CHOICES = [
        ('Slept Well', 'Slept Well'),
        ('Short Nap', 'Short Nap'),
        ('No Sleep', 'No Sleep'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, null=True, blank=True)
    food = models.CharField(max_length=20, choices=FOOD_CHOICES, null=True, blank=True)
    sleep = models.CharField(max_length=20, choices=SLEEP_CHOICES, null=True, blank=True)
    activity_notes = models.TextField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.name} - {self.date}"


# Chat Message Model
class ChatMessage(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages'
    )
    body = models.TextField(blank=True)
    voice = models.FileField(upload_to='chat_voice/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.body[:40]}"


# Notification Model
class Notification(models.Model):
    TYPE_CHOICES = [
        ('activity', 'New Activity'),
        ('report', 'Daily Report'),
        ('attendance', 'Attendance Update'),
    ]
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    message = models.CharField(max_length=300)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='activity')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"