from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Write a comment...',
            })
        }
        labels = {'body': ''}
