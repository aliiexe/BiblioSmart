from django import forms
from django.contrib.auth.forms import UserCreationForm
from biblio_smart.models import Utilisateur

class CustomUserCreationForm(UserCreationForm):
    nom = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
    )
    role = forms.ChoiceField(
        label="Rôle",
        choices=[('lecteur', 'Lecteur'), ('bibliothecaire', 'Bibliothécaire')],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
    )

    class Meta:
        model = Utilisateur
        fields = ['nom', 'email', 'role', 'password1', 'password2']