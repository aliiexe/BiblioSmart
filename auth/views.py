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
        role = request.POST.get('role', 'lecteur')  # Default role is 'lecteur'

        # Check if the email already exists
        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, 'Un utilisateur avec cet email existe déjà.')
            return render(request, 'inscription.html')

        # Create a new Utilisateur instance
        utilisateur = Utilisateur(
            nom=nom,
            email=email,
            mot_de_passe=mot_de_passe,  # Store the raw password (consider hashing it)
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
            # Check if a user with the given email exists
            utilisateur = Utilisateur.objects.get(email=email)
            
            # Verify the password
            if utilisateur.mot_de_passe == password:
                # Store user information in the session
                request.session['utilisateur_id'] = utilisateur.id
                request.session['utilisateur_nom'] = utilisateur.nom
                request.session['utilisateur_role'] = utilisateur.role
                
                # Redirect to the main path in the livres app
                return redirect('/livres')  # 'home' is the name of the main path in the livres app
            else:
                messages.error(request, 'Mot de passe incorrect.')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Aucun utilisateur trouvé avec cet email.')
    
    # Render the login page for GET requests or if login fails
    return render(request, 'connexion.html')