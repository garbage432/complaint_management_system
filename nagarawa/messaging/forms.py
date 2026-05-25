from django import forms


class MessageForm(forms.Form):
    body = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={
            'class': 'msg-input',
            'placeholder': 'Type your message...',
            'rows': 3,
        }),
        label=''
    )


class StartConversationForm(forms.Form):
    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Subject (optional)',
        }),
        label='Subject'
    )
    body = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Write your message to the support team...',
            'rows': 4,
        }),
        label='Message'
    )
