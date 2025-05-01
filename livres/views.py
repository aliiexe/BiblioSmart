from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from biblio_smart.models import Livre
from biblio_smart.models import Emprunt, Lecteur, Utilisateur
from django.shortcuts import get_object_or_404, redirect
from django.db import models
from .forms import BookForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now
from .decorators import custom_login_required

def index(request):
    books = Livre.objects.all()
    return render(request, 'index.html', {'books': books})

# def add_book(request):
#     if request.method == 'POST':
#         titre = request.POST.get('titre')
#         auteur = request.POST.get('auteur')
#         ISBN = request.POST.get('ISBN')
#         categorie = request.POST.get('categorie')
#         disponibilite = request.POST.get('disponibilite') == 'on'
#         image = request.FILES.get('image')  

#         new_book = Livre(
#             titre=titre,
#             auteur=auteur,
#             ISBN=ISBN,
#             categorie=categorie,
#             disponibilite=disponibilite,
#             image=image  
#         )
#         new_book.save()

#         return render(request, 'books.html', {'books': Livre.objects.all()})
#     else:
#         return render(request, 'book_form.html')

def add_book(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        auteur = request.POST.get('auteur')
        ISBN = request.POST.get('ISBN')
        
        categorie = request.POST.get('categorie')
        if categorie == 'other':
            categorie = request.POST.get('custom_categorie')

        image = request.FILES.get('image')
        description = request.POST.get('description') 

        new_book = Livre(
            titre=titre,
            auteur=auteur,
            ISBN=ISBN,
            categorie=categorie,
            disponibilite=True, 
            image=image,
            description=description
        )
        new_book.save()

        messages.success(request, f"Book '{new_book.titre}' added successfully.")
        return redirect('book_management')
    else:
        categories = Livre.objects.values_list('categorie', flat=True).distinct()
        return render(request, 'book_form.html', {'categories': categories})

def home(request):
    recent_books = Livre.objects.order_by('-date_ajout')[:4]
    
    categories = Livre.objects.values('categorie').annotate(count=models.Count('categorie'))
    
    return render(request, 'home.html', {
        'recent_books': recent_books,
        'categories': categories,
    })

def books(request):
    books = Livre.objects.all()
    categories = Livre.objects.values_list('categorie', flat=True).distinct()

    category = request.GET.get('category')
    if category:
        books = books.filter(categorie=category)

    availability = request.GET.get('availability')
    if availability == 'available':
        books = books.filter(disponibilite=True)
    elif availability == 'borrowed':
        books = books.filter(disponibilite=False)

    search_query = request.GET.get('search')
    if search_query:
        books = books.filter(
            models.Q(titre__icontains=search_query) |
            models.Q(auteur__icontains=search_query) |
            models.Q(ISBN__icontains=search_query)
        )

    sort = request.GET.get('sort')
    if sort == 'title_asc':
        books = books.order_by('titre')
    elif sort == 'title_desc':
        books = books.order_by('-titre')
    elif sort == 'author_asc':
        books = books.order_by('auteur')
    elif sort == 'recent':
        books = books.order_by('-date_ajout')

    return render(request, 'books.html', {'books': books, 'categories': categories})

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

# @login_required
def borrow_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Livre, id=book_id)
        
        if not book.disponibilite:
            messages.error(request, "Ce livre n'est pas disponible actuellement.")
            return redirect('book_detail', book_id=book_id)
        
        utilisateur_id = request.session.get('utilisateur_id')
        if not utilisateur_id:
            messages.error(request, "Vous devez être connecté pour emprunter un livre.")
            return redirect('connexion')
        
        try:
            lecteur = Lecteur.objects.get(id=utilisateur_id)
        except Lecteur.DoesNotExist:
            messages.error(request, "Votre profil de lecteur n'existe pas.")
            return redirect('book_detail', book_id=book_id)
        
        # Use timezone.now() instead of now()
        start_date = timezone.now().date()

        end_date = request.POST.get('end_date')
        
        if not end_date:
            messages.error(request, "Veuillez fournir une date de fin valide.")
            return redirect('book_detail', book_id=book_id)

        try:
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "La date de fin fournie n'est pas valide.")
            return redirect('book_detail', book_id=book_id)

        if end_date <= start_date:
            messages.error(request, "La date de fin doit être après la date de début.")
            return redirect('book_detail', book_id=book_id)
        
        # Create the loan with the correct timezone-aware date
        Emprunt.objects.create(
            livre=book,
            lecteur=lecteur,
            date_emprunt=start_date,
            date_retour_prevue=end_date,
            date_retour=None,
            returned=False
        )
        
        book.disponibilite = False
        book.save()
        
        messages.success(request, f"Vous avez emprunté '{book.titre}' du {start_date} au {end_date}.")
        return redirect('book_detail', book_id=book_id)
    
    return redirect('book_detail', book_id=book_id)

# @login_required
def join_waitlist(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Livre, id=book_id)
        
        if book.disponibilite:
            messages.info(request, "Ce livre est disponible, vous pouvez l'emprunter directement.")
            return redirect('book_detail', book_id=book_id)
        
        utilisateur_id = request.session.get('utilisateur_id')
        try:
            lecteur = Lecteur.objects.get(id=utilisateur_id)
        except Lecteur.DoesNotExist:
            messages.error(request, "Votre profil de lecteur n'existe pas.")
            return redirect('book_detail', book_id=book_id)
        
        if book.liste_attente.filter(id=lecteur.id).exists():
            messages.info(request, "Vous êtes déjà sur la liste d'attente pour ce livre.")
            return redirect('book_detail', book_id=book_id)
        
        book.liste_attente.add(lecteur)
        
        messages.success(request, f"Vous avez été ajouté à la liste d'attente pour '{book.titre}'.")
        return redirect('book_detail', book_id=book_id)
    
    return redirect('book_detail', book_id=book_id)

def book_management(request):
    books = Livre.objects.all().order_by('-id')
    for book in books:
        print(f"Book ID: {book.id}, Title: {book.titre}")
    return render(request, 'book_management.html', {'books': books})

# def add_book(request):
#     if request.method == 'POST':
#         form = BookForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Book added successfully.')
#             return redirect('book_management')
#     else:
#         form = BookForm()
    
#     return render(request, 'book_form.html', {'form': form})

def edit_book(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        auteur = request.POST.get('auteur')
        ISBN = request.POST.get('ISBN')
        
        categorie = request.POST.get('categorie')
        if categorie == 'other':
            categorie = request.POST.get('custom_categorie')

        new_disponibilite = request.POST.get('disponibilite') == 'on'

        if not book.disponibilite and new_disponibilite:
            active_emprunts = Emprunt.objects.filter(livre=book, returned=False)
            for emprunt in active_emprunts:
                emprunt.returned = True
                emprunt.date_retour = now().date()
                emprunt.save()
                print(f"Updated emprunt {emprunt.id} to returned=True")

        book.titre = titre
        book.auteur = auteur
        book.ISBN = ISBN
        book.categorie = categorie
        book.disponibilite = new_disponibilite
        book.description = request.POST.get('description')

        if 'image' in request.FILES:
            book.image = request.FILES.get('image')

        book.save()

        messages.success(request, f"Book '{book.titre}' updated successfully.")
        return redirect('book_management')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'book_form.html', {'form': form, 'book': book})

# def edit_book(request, book_id):
#     book = get_object_or_404(Livre, id=book_id)

    # if request.method == 'POST':
    #     titre = request.POST.get('titre')
    #     auteur = request.POST.get('auteur')
    #     ISBN = request.POST.get('ISBN')
        
    #     categorie = request.POST.get('categorie')
    #     if categorie == 'other':
    #         categorie = request.POST.get('custom_categorie')


    #     disponibilite = request.POST.get('disponibilite') == 'on'

    #     image = request.FILES.get('image')
    #     description = request.POST.get('description')

    #     book.titre = titre
    #     book.auteur = auteur
    #     book.ISBN = ISBN
    #     book.categorie = categorie
    #     book.disponibilite = disponibilite
    #     book.description = description

    #     if image:
    #         book.image = image

#         book.save()

#         messages.success(request, f"Book '{book.titre}' updated successfully.")
#         return redirect('book_management')
    # else:
    #     categories = Livre.objects.values_list('categorie', flat=True).distinct()
    #     return render(request, 'book_form.html', {'book': book, 'categories': categories})

def delete_book(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('book_management')
    
    return render(request, 'book_delete.html', {'book': book})


def toggle_favorite(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    utilisateur = get_object_or_404(Utilisateur, id=request.session.get('utilisateur_id'))

    if book in utilisateur.favorites.all():
        utilisateur.favorites.remove(book)
        messages.success(request, f"'{book.titre}' has been removed from your favorites.")
    else:
        utilisateur.favorites.add(book)
        messages.success(request, f"'{book.titre}' has been added to your favorites.")

    return redirect('book_detail', book_id=book_id)

# @custom_login_required
def return_book(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    utilisateur_id = request.session.get('utilisateur_id')

    if not utilisateur_id:
        messages.error(request, "You must be logged in to return a book.")
        return redirect('connexion')

    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)

    print(f"User: {utilisateur.nom}, Book: {book.titre}")

    emprunt = Emprunt.objects.filter(livre=book, lecteur=utilisateur).order_by('-id').first()

    if emprunt:
        print(f"Emprunt found: ID={emprunt.id}, Start Date={emprunt.date_emprunt}, Current Return Date={emprunt.date_retour}")

        emprunt.date_retour = now().date()
        emprunt.returned = True
        emprunt.save()

        print(f"Updated Emprunt: ID={emprunt.id}, New Return Date={emprunt.date_retour}")

        book.disponibilite = True
        book.save()

        messages.success(request, f"You have successfully returned '{book.titre}'. The return date has been updated.")
    else:
        print("No active borrowing record found for this user and book.")
        messages.error(request, "You cannot return a book that you haven't borrowed.")

    return redirect('book_detail', book_id=book_id)


def logout(request):
    request.session.flush()
    messages.success(request, 'Vous êtes déconnecté avec succès.')
    return redirect('connexion')