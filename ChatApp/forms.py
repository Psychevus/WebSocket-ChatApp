from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm

from .models import Conversation, CustomUser


class StartConversationForm(forms.Form):
    participants = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        label="Select Participant",
        required=False,
        empty_label="---------",
    )

    def clean_user2(self):
        user2 = self.cleaned_data['user2']
        user1 = self._request.user

        if user2 is not None:
            existing_conversation = Conversation.objects.filter(user1=user1, user2=user2) | \
                                    Conversation.objects.filter(user1=user2, user2=user1)
            if existing_conversation.exists():
                raise forms.ValidationError("A conversation with this participant already exists.")
        return user2

    def __init__(self, *args, **kwargs):
        self._request = kwargs.pop('request', None)
        super(StartConversationForm, self).__init__(*args, **kwargs)


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        error_messages={
            'required': 'First name: This field is required.',
        }
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        error_messages={
            'required': 'Last name: This field is required.',
        }
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        error_messages={
            'required': 'First password: This field is required.',
        }
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        error_messages={
            'required': 'Second password: This field is required.',
            'password_mismatch': 'The two password fields didn’t match.',
        }
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'first_name', 'last_name', 'password1', 'password2')


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.TextInput(attrs={'autofocus': True}))

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        error_messages={
            'required': 'Password: This field is required.',
        }
    )

    class Meta:
        fields = ['email', 'password']
