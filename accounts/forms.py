from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import Profile


class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError('No existe ninguna cuenta registrada con ese correo.')
        return email


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este email.')
        return email


class ProfileForm(forms.ModelForm):
    # Campos del modelo User
    username = forms.CharField(max_length=150, label='Nombre de usuario')
    first_name = forms.CharField(max_length=150, required=False, label='Nombre')
    last_name = forms.CharField(max_length=150, required=False, label='Apellidos')
    email = forms.EmailField(required=False, label='Email')
    remove_avatar = forms.BooleanField(required=False, label='Eliminar foto de perfil')

    class Meta:
        model = Profile
        fields = ('avatar', 'bio')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            user = self.instance.user
            self.fields['username'].initial = user.username
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user = self.instance.user
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            raise forms.ValidationError('Ese nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance.user
        if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese email.')
        return email
