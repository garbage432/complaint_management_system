from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Complaint, ComplaintImage
from departments.models import Department


class DepartmentChoiceField(forms.ModelChoiceField):
    """
    A ModelChoiceField that shows the department's language-aware
    display_name (Nepali or English) instead of the raw .name field.
    """
    def label_from_instance(self, obj):
        return f"{obj.icon} {obj.display_name}" if obj.icon else obj.display_name


class ComplaintForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'form-input'}),
        required=False,
        help_text=_('You can upload multiple images (max 5MB each)')
    )

    class Meta:
        model = Complaint
        fields = ['title', 'description', 'department', 'location_name', 'latitude', 'longitude', 'is_anonymous']
        field_classes = {
            'department': DepartmentChoiceField,
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Brief title of your complaint')}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': _('Describe the issue in detail...')}),
            'department': forms.Select(attrs={'class': 'form-input'}),
            'location_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Location name (e.g. New Baneshwor, Kathmandu)')}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].empty_label = _('Select a department...')


class ComplaintFilterForm(forms.Form):
    department = DepartmentChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Departments'),
        widget=forms.Select(attrs={'class': 'form-input-sm'})
    )
    status = forms.ChoiceField(
        choices=[('', _('All Status'))] + Complaint.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-input-sm'})
    )
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', _('Newest')),
            ('created_at', _('Oldest')),
            ('-view_count', _('Most Viewed')),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-input-sm'})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input-sm', 'placeholder': _('Search complaints...')})
    )