from django import forms
from .models import Activity, Attendance, DailyReport, User, Student, StudentClass as NurseryClass


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['student', 'description', 'image', 'file']
        widgets = {
            'student': forms.Select(attrs={'class': 'tt-select'}),
            'description': forms.Textarea(attrs={
                'class': 'tt-textarea',
                'rows': 3,
                'placeholder': 'Describe the activity or assignment...',
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'tt-file-input'}),
            'file': forms.ClearableFileInput(attrs={'class': 'tt-file-input'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['student'].queryset = Student.objects.filter(student_class__teacher=teacher)


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'tt-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'tt-input'}),
            'status': forms.Select(attrs={'class': 'tt-select'}),
        }


class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ['student', 'date', 'mood', 'food', 'sleep', 'activity_notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'tt-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'tt-input'}),
            'mood': forms.Select(attrs={'class': 'tt-select'}),
            'food': forms.Select(attrs={'class': 'tt-select'}),
            'sleep': forms.Select(attrs={'class': 'tt-select'}),
            'activity_notes': forms.Textarea(attrs={
                'class': 'tt-textarea',
                'rows': 3,
                'placeholder': 'Add notes about the day...',
            }),
        }

    def __init__(self, *args, **kwargs):
        class_type = kwargs.pop('class_type', 'nursery')
        super().__init__(*args, **kwargs)
        
        if class_type == 'lkg':
            self.fields.pop('food')
            self.fields.pop('sleep')
        elif class_type == 'ukg':
            self.fields.pop('mood')
            self.fields.pop('food')
            self.fields.pop('sleep')


class AddChildForm(forms.ModelForm):
    """Form for parents to add an additional child."""
    class Meta:
        model = Student
        fields = ['name', 'age', 'student_class']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Full Name'}),
            'age': forms.NumberInput(attrs={'class': 'tt-input', 'placeholder': 'Age'}),
            'student_class': forms.Select(attrs={'class': 'tt-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_class'].queryset = NurseryClass.objects.all().order_by('name')
        self.fields['student_class'].empty_label = "— Select Class —"


class StudentNameEditForm(forms.ModelForm):
    """Form for parents to edit a child's name."""
    class Meta:
        model = Student
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Full Name'}),
        }


class TeacherProfileForm(forms.ModelForm):
    """Allows a teacher to update their personal details and profile picture."""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'tt-input', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Last name'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'tt-file-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class StudentProfilePictureForm(forms.ModelForm):
    """Update a student's profile picture."""
    class Meta:
        model = Student
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'tt-file-input'}),
        }


class TeacherRegistrationForm(forms.Form):
    """Self-registration form for teacher accounts."""
    first_name = forms.CharField(
        max_length=50, label='First Name',
        widget=forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'First name', 'autofocus': True}),
    )
    last_name = forms.CharField(
        max_length=50, label='Last Name',
        widget=forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Last name'}),
    )
    username = forms.CharField(
        max_length=150, label='Username',
        widget=forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Choose a username', 'autocomplete': 'username'}),
    )
    email = forms.EmailField(
        required=False, label='Email (optional)',
        widget=forms.EmailInput(attrs={'class': 'tt-input', 'placeholder': 'your@email.com'}),
    )
    student_class = forms.ModelChoiceField(
        queryset=NurseryClass.objects.filter(teacher__isnull=True).order_by('name'),
        label='Your Class',
        empty_label='— Select your class —',
        widget=forms.Select(attrs={'class': 'tt-select'}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'tt-input', 'placeholder': 'Min 8 characters', 'autocomplete': 'new-password'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'tt-input', 'placeholder': 'Repeat your password', 'autocomplete': 'new-password'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned

    def save(self):
        data   = self.cleaned_data
        klass  = data['student_class']
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='teacher',
        )
        # Assign teacher to the selected class
        klass.teacher = user
        klass.save()
        return user


class ParentRegistrationForm(forms.Form):
    """Self-registration form for parent accounts."""
    first_name = forms.CharField(
        max_length=50, label='First Name',
        widget=forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'First name', 'autofocus': True}),
    )
    last_name = forms.CharField(
        max_length=50, label='Last Name',
        widget=forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Last name'}),
    )
    username = forms.CharField(
        max_length=150, label='Username',
        widget=forms.TextInput(attrs={'class': 'tt-input', 'placeholder': 'Choose a username', 'autocomplete': 'username'}),
    )
    email = forms.EmailField(
        required=False, label='Email (optional)',
        widget=forms.EmailInput(attrs={'class': 'tt-input', 'placeholder': 'your@email.com'}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'tt-input', 'placeholder': 'Min 8 characters', 'autocomplete': 'new-password'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'tt-input', 'placeholder': 'Repeat your password', 'autocomplete': 'new-password'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return username

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='parent',
        )
        return user


def validate_children_data(post_data):
    """
    Parse and validate children from POST data.
    Expects fields: child_name_1, child_age_1, child_class_1, child_name_2, …
    Returns (children_list, errors_list).
    Each item in children_list is a dict: {name, age, class_obj}.
    """
    from .models import StudentClass as NurseryClass
    children = []
    errors = []
    i = 1
    while True:
        name = post_data.get(f'child_name_{i}', '').strip()
        age_str = post_data.get(f'child_age_{i}', '').strip()
        class_id = post_data.get(f'child_class_{i}', '').strip()
        if not name and not age_str and not class_id:
            break  # no more children rows
        row_errors = []
        if not name:
            row_errors.append(f'Child {i}: name is required.')
        age = None
        if not age_str:
            row_errors.append(f'Child {i}: age is required.')
        else:
            try:
                age = int(age_str)
                if age < 0 or age > 18:
                    row_errors.append(f'Child {i}: age must be between 0 and 18.')
            except ValueError:
                row_errors.append(f'Child {i}: age must be a number.')
        klass = None
        if not class_id:
            row_errors.append(f'Child {i}: class is required.')
        else:
            try:
                klass = NurseryClass.objects.get(pk=class_id)
            except NurseryClass.DoesNotExist:
                row_errors.append(f'Child {i}: selected class does not exist.')
        if row_errors:
            errors.extend(row_errors)
        else:
            children.append({'name': name, 'age': age, 'student_class': klass})
        i += 1
    return children, errors