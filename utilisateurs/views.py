from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from biblio_smart.models import Utilisateur, Lecteur, Bibliothecaire, Livre, Emprunt
from .forms import UtilisateurForm, LecteurForm, BibliothecaireForm, LoginForm

# User Management views
def user_management(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    # Start with all users
    users = Utilisateur.objects.all().order_by('-id')
    
    # Apply search filter if provided
    if search_query:
        users = users.filter(
            Q(nom__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
    
    # Apply role filter if provided
    if role_filter:
        users = users.filter(role=role_filter)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter
    }
    
    return render(request, 'user_management.html', context)

def user_detail(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    
    # Additional context based on user role
    context = {'user': user}
    
    if user.role == 'lecteur':
        # Get the actual Lecteur instance
        try:
            lecteur = Lecteur.objects.get(id=user_id)
            context['user'] = lecteur
        except Lecteur.DoesNotExist:
            pass
    
    elif user.role == 'bibliothecaire':
        # Get the actual Bibliothecaire instance
        try:
            bibliothecaire = Bibliothecaire.objects.get(id=user_id)
            context['user'] = bibliothecaire
        except Bibliothecaire.DoesNotExist:
            pass
    
    return render(request, 'user_detail.html', context)

def add_user(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        
        if role == 'lecteur':
            form = LecteurForm(request.POST)
        elif role == 'bibliothecaire':
            form = BibliothecaireForm(request.POST)
        else:
            form = UtilisateurForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.nom}" has been created successfully.')
            return redirect('user_management')
    else:
        form = UtilisateurForm()
    
    return render(request, 'user_form.html', {'form': form, 'is_edit': False})

# def edit_lecteur(request, user_id):
#     lecteur = get_object_or_404(Lecteur, id=user_id)
#     original_password = lecteur.mot_de_passe  # Store the original password
    
#     if request.method == 'POST':
#         # Handle empty password fields specially
#         post_data = request.POST.copy()  # Make a mutable copy
        
#         # If password field is empty, remove it from the POST data
#         # so the form doesn't process it at all
#         if post_data.get('mot_de_passe') == '':
#             post_data.pop('mot_de_passe')
        
#         form = LecteurForm(post_data, instance=lecteur)
        
#         if form.is_valid():
#             user = form.save(commit=False)
            
#             # If password wasn't in the POST data, restore the original
#             if 'mot_de_passe' not in post_data:
#                 user.mot_de_passe = original_password
            
#             user.save()
#             messages.success(request, f'Reader "{user.nom}" has been updated successfully.')
#             return redirect('user_detail', user_id=user.id)
#     else:
#         form = LecteurForm(instance=lecteur)
#         form.fields['mot_de_passe'].required = False  # Make password optional on edit
    
#     return render(request, 'user_form.html', {'form': form, 'user': lecteur, 'is_edit': True})




def edit_lecteur(request, user_id):
    lecteur = get_object_or_404(Lecteur, id=user_id)
    original_password = lecteur.mot_de_passe

    if request.method == 'POST':
        post_data = request.POST.copy()
        if post_data.get('mot_de_passe') == '':
            post_data.pop('mot_de_passe')

        form = LecteurForm(post_data, instance=lecteur)

        if form.is_valid():
            user = form.save(commit=False)
            # Si le champ mot_de_passe n'est pas dans le POST, on garde l'ancien
            if 'mot_de_passe' not in post_data:
                user.mot_de_passe = original_password
            # Mettre à jour le rôle si présent dans le formulaire
            if 'role' in form.cleaned_data:
                user.role = form.cleaned_data['role']
            user.save()
            messages.success(request, f'Reader "{user.nom}" has been updated successfully.')
            return redirect('user_detail', user_id=user.id)
    else:
        form = LecteurForm(instance=lecteur)
        form.fields['mot_de_passe'].required = False

    return render(request, 'user_form.html', {'form': form, 'user': lecteur, 'is_edit': True})

def edit_bibliothecaire(request, user_id):
    bibliothecaire = get_object_or_404(Bibliothecaire, id=user_id)
    original_password = bibliothecaire.mot_de_passe  # Store the original password
    
    if request.method == 'POST':
        # Handle empty password fields specially
        post_data = request.POST.copy()  # Make a mutable copy
        
        # If password field is empty, remove it from the POST data
        # so the form doesn't process it at all
        if post_data.get('mot_de_passe') == '':
            post_data.pop('mot_de_passe')
        
        form = BibliothecaireForm(post_data, instance=bibliothecaire)
        
        if form.is_valid():
            user = form.save(commit=False)
            
            # If password wasn't in the POST data, restore the original
            if 'mot_de_passe' not in post_data:
                user.mot_de_passe = original_password
            
            user.save()
            messages.success(request, f'Librarian "{user.nom}" has been updated successfully.')
            return redirect('user_detail', user_id=user.id)
    else:
        form = BibliothecaireForm(instance=bibliothecaire)
        form.fields['mot_de_passe'].required = False  # Make password optional on edit
    
    return render(request, 'user_form.html', {'form': form, 'user': bibliothecaire, 'is_edit': True})

def delete_user(request, user_id):
    user = get_object_or_404(Utilisateur, id=user_id)
    
    if request.method == 'POST':
        user_name = user.nom
        user.delete()
        messages.success(request, f'User "{user_name}" has been deleted successfully.')
        return redirect('user_management')
    
    return render(request, 'user_delete.html', {'user': user})

# def login_view(request):
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
            
#             try:
#                 user = Utilisateur.objects.get(email=email)
#                 if check_password(password, user.mot_de_passe):
#                     # Store user ID in session
#                     request.session['user_id'] = user.id
#                     request.session['user_role'] = user.role
                    
#                     # Update last login time
#                     user.derniere_connexion = timezone.now()
#                     user.save()
                    
#                     messages.success(request, f'Welcome back, {user.nom}!')
#                     return redirect('home')
#                 else:
#                     messages.error(request, 'Invalid password.')
#             except Utilisateur.DoesNotExist:
#                 messages.error(request, 'No user found with this email.')
#     else:
#         form = LoginForm()
    
#     return render(request, 'login.html', {'form': form})

# def logout_view(request):
#     if 'user_id' in request.session:
#         del request.session['user_id']
#     if 'user_role' in request.session:
#         del request.session['user_role']
    
#     messages.success(request, 'You have been logged out successfully.')
#     return redirect('login')

def register_view(request):
    if request.method == 'POST':
        role = request.POST.get('role', 'lecteur')
        
        if role == 'lecteur':
            form = LecteurForm(request.POST)
        else:
            form = BibliothecaireForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = LecteurForm()  # Default to reader registration
    
    return render(request, 'register.html', {'form': form})


def user_favorites(request, user_id):
    from biblio_smart.models import Utilisateur, Livre
    
    # Check if the user is logged in and matches the requested user_id
    current_user_id = request.session.get('utilisateur_id')
    if not current_user_id or int(current_user_id) != int(user_id):
        messages.error(request, 'You can only view your own favorites')
        return redirect('login')
    
    # Process removing a favorite if that was requested
    if request.method == 'POST' and 'remove_favorite' in request.POST:
        book_id = request.POST.get('remove_favorite')
        try:
            user = Utilisateur.objects.get(id=user_id)
            book = Livre.objects.get(id=book_id)
            user.favorites.remove(book)
            messages.success(request, f'"{book.titre}" has been removed from your favorites')
        except Exception as e:
            messages.error(request, f'Error removing book from favorites: {str(e)}')
    
    # Get the user and their favorite books
    try:
        user = get_object_or_404(Utilisateur, id=user_id)
        favorite_books = user.favorites.all()
        
        context = {
            'user': user,
            'favorite_books': favorite_books,
        }
        
        return render(request, 'user_favorites.html', context)
    except Exception as e:
        messages.error(request, f'Error loading favorites: {str(e)}')
        return redirect('dashboard')

def book_detail(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    similar_books = Livre.objects.filter(categorie=book.categorie).exclude(id=book.id)[:5]

    utilisateur_id = request.session.get('utilisateur_id')
    utilisateur = Utilisateur.objects.get(id=utilisateur_id)

    # Let's be very explicit with the query to find the emprunt record
    emprunt = None
    try:
        # Use the exact values we know exist in the database
        emprunt = Emprunt.objects.filter(
            livre_id=book.id,
            lecteur_id=utilisateur.id,
            returned=0  # Explicitly use 0 instead of False
        ).first()
        print(f"Emprunt query result: {emprunt}")
    except Exception as e:
        print(f"Error fetching emprunt: {e}")

    return render(request, 'book_detail.html', {
        'book': book,
        'similar_books': similar_books,
        'utilisateur': utilisateur,
        'emprunt': emprunt,
        'active_emprunt': emprunt is not None,
    })