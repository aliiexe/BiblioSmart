from emprunt.utils import check_overdue_loans
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from biblio_smart.models import Utilisateur
from django.urls import reverse
from biblio_smart.models import Lecteur, Bibliothecaire

def inscription(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        mot_de_passe = request.POST.get('mot_de_passe')
        role = request.POST.get('role', 'lecteur')

        # Check if a user with the same email already exists
        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, 'Un utilisateur avec cet email existe déjà.')
            return render(request, 'inscription.html')

        # Create a Lecteur or Bibliothecaire based on the role
        if role == 'lecteur':
            utilisateur = Lecteur(
                nom=nom,
                email=email,
                mot_de_passe=mot_de_passe,
                role=role
            )
        elif role == 'bibliothecaire':
            utilisateur = Bibliothecaire(
                nom=nom,
                email=email,
                mot_de_passe=mot_de_passe,
                role=role
            )
        else:
            messages.error(request, 'Rôle invalide.')
            return render(request, 'inscription.html')

        # Save the user instance
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
                # Basic session setup
                request.session['utilisateur_id'] = utilisateur.id
                request.session['utilisateur_nom'] = utilisateur.nom
                request.session['utilisateur_role'] = utilisateur.role
                request.session['utilisateur_email'] = utilisateur.email
                
                # Check for overdue loans if user is a lecteur
                if utilisateur.role == 'lecteur':
                    # Call our comprehensive check function
                    stats = check_overdue_loans(utilisateur.id)
                    
                    # Store stats in session for UI display
                    request.session['overdue_count'] = stats['total_overdue_count']
                    request.session['current_overdue_count'] = stats['current_overdue_count']
                    request.session['past_overdue_count'] = stats['past_overdue_count']
                    request.session['total_fees'] = float(stats['total_fees'])
                    
                    # Show message if there are overdue books
                    if stats['current_overdue_count'] > 0:
                        messages.warning(
                            request, 
                            f"Vous avez {stats['current_overdue_count']} livre(s) en retard avec des frais de {stats['current_overdue_fees']:.2f}€. "
                            f"Veuillez les retourner dès que possible."
                        )
                    
                    # If there are past overdue books with unpaid fees
                    if stats['past_overdue_count'] > 0:
                        messages.info(
                            request,
                            f"Vous avez {stats['past_overdue_count']} livre(s) retournés en retard avec des frais de {stats['past_overdue_fees']:.2f}€. "
                            f"Veuillez payer ces frais à votre prochaine visite."
                        )
                
                messages.success(request, f"Bienvenue, {utilisateur.nom}!")
                return redirect('dashboard')
            else:
                messages.error(request, 'Mot de passe incorrect.')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Aucun utilisateur trouvé avec cet email.')
    
    return render(request, 'connexion.html')