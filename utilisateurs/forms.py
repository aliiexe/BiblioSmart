from django import forms
from django.contrib.auth.hashers import make_password
from biblio_smart.models import Utilisateur, Lecteur, Bibliothecaire

class UtilisateurForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = Utilisateur
        fields = ['nom', 'email', 'mot_de_passe', 'role']
        widgets = {
            'mot_de_passe': forms.PasswordInput(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields not required in the form since we handle validation in the template
        for field in self.fields:
            self.fields[field].required = False
            
        # If we're editing an existing user, don't require password fields
        if self.instance.pk:
            self.fields['mot_de_passe'].required = False
            self.fields['confirm_password'].required = False
            
    def clean(self):
        cleaned_data = super().clean()
        # Required fields validation
        required_fields = ['nom', 'email', 'role']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')
        
        # Password validation
        password = cleaned_data.get('mot_de_passe')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Only validate password if it's a new user or if password is being changed
        if not self.instance.pk or (password and len(password) > 0):
            if not password:
                self.add_error('mot_de_passe', 'Password is required.')
            elif not confirm_password:
                self.add_error('confirm_password', 'Please confirm your password.')
            elif password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Hash password if provided
        password = self.cleaned_data.get('mot_de_passe')
        if password:
            user.mot_de_passe = make_password(password)
            
        if commit:
            user.save()
            
        return user

class LecteurForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = Lecteur
        fields = ['nom', 'email', 'mot_de_passe']
        widgets = {
            'mot_de_passe': forms.PasswordInput(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we're editing an existing user, don't require password fields
        if self.instance.pk:
            self.fields['mot_de_passe'].required = False
            self.fields['confirm_password'].required = False
            
    def clean(self):
        cleaned_data = super().clean()
        # Required fields validation
        required_fields = ['nom', 'email']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')
        
        # Password validation
        password = cleaned_data.get('mot_de_passe')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Only validate password if it's a new user or if password is being changed
        if not self.instance.pk or (password and len(password) > 0):
            if not password:
                self.add_error('mot_de_passe', 'Password is required.')
            elif not confirm_password:
                self.add_error('confirm_password', 'Please confirm your password.')
            elif password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'lecteur'
        
        # Hash password if provided
        password = self.cleaned_data.get('mot_de_passe')
        if password:
            user.mot_de_passe = make_password(password)
            
        if commit:
            user.save()
            
        return user

class BibliothecaireForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = Bibliothecaire
        fields = ['nom', 'email', 'mot_de_passe']
        widgets = {
            'mot_de_passe': forms.PasswordInput(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we're editing an existing user, don't require password fields
        if self.instance.pk:
            self.fields['mot_de_passe'].required = False
            self.fields['confirm_password'].required = False
            
    def clean(self):
        cleaned_data = super().clean()
        # Required fields validation
        required_fields = ['nom', 'email']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')
        
        # Password validation
        password = cleaned_data.get('mot_de_passe')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Only validate password if it's a new user or if password is being changed
        if not self.instance.pk or (password and len(password) > 0):
            if not password:
                self.add_error('mot_de_passe', 'Password is required.')
            elif not confirm_password:
                self.add_error('confirm_password', 'Please confirm your password.')
            elif password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'bibliothecaire'
        
        # Hash password if provided
        password = self.cleaned_data.get('mot_de_passe')
        if password:
            user.mot_de_passe = make_password(password)
            
        if commit:
            user.save()
            
        return user

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())