from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import UserCreatedQuiz, Category, QuizUploadRequest


class UserQuizForm(forms.ModelForm):
    class Meta:
        model = UserCreatedQuiz
        fields = ['title', 'description', 'category', 'difficulty', 'time_limit', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Test sarlavhasi')}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': _('Ixtiyoriy tavsif')}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'difficulty': forms.Select(attrs={'class': 'form-input'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 180}),
            'is_published': forms.CheckboxInput(),
        }


class JsonImportForm(forms.Form):
    json_file = forms.FileField(
        label="JSON fayl",
        help_text="Faqat .json formatidagi fayl yuklang",
        widget=forms.FileInput(attrs={'accept': '.json'})
    )


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        label=_("Ism"),
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Ismingiz')})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        label=_("Familiya"),
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Familiyangiz')})
    )
    email = forms.EmailField(
        required=False,
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@example.com'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Foydalanuvchi nomi')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Parol')})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': _('Parolni tasdiqlang')})
        for field in self.fields.values():
            field.error_messages = {k: str(v) for k, v in field.error_messages.items()}


class QuizUploadRequestForm(forms.ModelForm):
    class Meta:
        model = QuizUploadRequest
        fields = ['quiz_title', 'category', 'time_limit', 'upload_file', 'note', 'user_email']
        widgets = {
            'quiz_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': _('Test nomi')}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 180}),
            'upload_file': forms.FileInput(attrs={'class': 'form-input', 'accept': '.json,.xlsx,.xls,.docx,.doc,.pdf'}),
            'note': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': _('Qo\'shimcha izoh...')}),
            'user_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@example.com'}),
        }
        labels = {
            'quiz_title': _("Test nomi"),
            'category': _("Kategoriya"),
            'time_limit': _("Vaqt limiti (daqiqa)"),
            'upload_file': _("Fayl (JSON, Excel, Word, PDF)"),
            'note': _("Izoh"),
            'user_email': _("Sizning emailingiz (javob uchun)"),
        }
