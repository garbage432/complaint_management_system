from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_("Email"))
    first_name = forms.CharField(max_length=50, required=True, label=_("First name"))
    last_name = forms.CharField(max_length=50, required=True, label=_("Last name"))
    district = forms.CharField(max_length=100, required=False, label=_("District"))
    ward = forms.CharField(max_length=100, required=False, label=_("Ward"))
    phone = forms.CharField(max_length=15, required=False, label=_("Phone"))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'district', 'ward', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'avatar', 'district', 'ward', 'phone']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'bio':
                field.widget.attrs['class'] = 'form-input'