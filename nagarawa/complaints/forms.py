from django import forms
from .models import Complaint, ComplaintImage
from departments.models import Department


class ComplaintForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.ClearableFileInput(attrs={ 'accept': 'image/*', 'class': 'form-input'}),
        required=False,
        help_text='You can upload multiple images (max 5MB each)'
    )

    class Meta:
        model = Complaint
        fields = ['title', 'description', 'department', 'location_name', 'latitude', 'longitude', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Brief title of your complaint'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Describe the issue in detail...'}),
            'department': forms.Select(attrs={'class': 'form-input'}),
            'location_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Location name (e.g. New Baneshwor, Kathmandu)'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].empty_label = 'Select a department...'


class ComplaintFilterForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label='All Departments',
        widget=forms.Select(attrs={'class': 'form-input-sm'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Complaint.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-input-sm'})
    )
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest'),
            ('created_at', 'Oldest'),
            ('-view_count', 'Most Viewed'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-input-sm'})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input-sm', 'placeholder': 'Search complaints...'})
    )
