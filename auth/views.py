from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from biblio_smart.models import Utilisateur
from django.urls import reverse

def inscription(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')
        role = request.POST.get('role', 'lecteur')

        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, 'Un utilisateur avec cet email existe déjà.')
            return render(request, 'inscription.html')

        utilisateur = Utilisateur(
            nom=nom,
            email=email,
            mot_de_passe=mot_de_passe,
            role=role
        )
        utilisateur.save()
        messages.success(request, 'Inscription réussie. Vous pouvez maintenant vous connecter.')
        return redirect('connexion')
    return render(request, 'inscription.html')

def connexion(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            utilisateur = Utilisateur.objects.get(email=email)
            
            if utilisateur.mot_de_passe == password:
                request.session['utilisateur_id'] = utilisateur.id
                request.session['utilisateur_nom'] = utilisateur.nom
                request.session['utilisateur_role'] = utilisateur.role
                
                return redirect('/livres')
            else:
                messages.error(request, 'Mot de passe incorrect.')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Aucun utilisateur trouvé avec cet email.')
    
    return render(request, 'connexion.html')