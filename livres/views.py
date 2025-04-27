from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from biblio_smart.models import Livre
from biblio_smart.models import Emprunt, Lecteur
from django.shortcuts import get_object_or_404, redirect
from django.db import models
from .forms import BookForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta


def index(request):
    books = Livre.objects.all()
    return render(request, 'index.html', {'books': books})

def add_book(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        auteur = request.POST.get('auteur')
        ISBN = request.POST.get('ISBN')
        categorie = request.POST.get('categorie')
        disponibilite = request.POST.get('disponibilite') == 'on'

        new_book = Livre(
            titre=titre,
            auteur=auteur,
            ISBN=ISBN,
            categorie=categorie,
            disponibilite=disponibilite
        )
        new_book.save()

        return render(request, 'books.html', {'books': Livre.objects.all()})
    else:
        return render(request, 'book_form.html')

def home(request):
    # Get the 4 most recently added books
    recent_books = Livre.objects.order_by('-date_ajout')[:4]
    
    # Get unique categories and their book counts
    categories = Livre.objects.values('categorie').annotate(count=models.Count('categorie'))
    
    return render(request, 'home.html', {
        'recent_books': recent_books,
        'categories': categories,
    })

def books(request):
    books = Livre.objects.all()
    categories = Livre.objects.values_list('categorie', flat=True).distinct()

    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        books = books.filter(categorie=category)

    # Filter by availability if provided
    availability = request.GET.get('availability')
    if availability == 'available':
        books = books.filter(disponibilite=True)
    elif availability == 'borrowed':
        books = books.filter(disponibilite=False)

    # Filter by search query if provided
    search_query = request.GET.get('search')
    if search_query:
        books = books.filter(
            models.Q(titre__icontains=search_query) |
            models.Q(auteur__icontains=search_query) |
            models.Q(ISBN__icontains=search_query)
        )

    # Sort books if provided
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
    
    # Get similar books (same category)
    similar_books = Livre.objects.filter(categorie=book.categorie).exclude(id=book.id)[:5]
    
    return render(request, 'book_detail.html', {
        'book': book,
        'similar_books': similar_books
    })

# @login_required
def borrow_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Livre, id=book_id)
        
        # Check if book is available
        if not book.disponibilite:
            messages.error(request, "Ce livre n'est pas disponible actuellement.")
            return redirect('book_detail', book_id=book_id)
        
        # Get the current user as a Lecteur
        try:
            lecteur = Lecteur.objects.get(user=request.user)
        except Lecteur.DoesNotExist:
            messages.error(request, "Votre profil de lecteur n'existe pas.")
            return redirect('book_detail', book_id=book_id)
        
        # Create a new Emprunt
        date_retour = timezone.now().date() + timedelta(days=14)  # 2 weeks loan period
        Emprunt.objects.create(
            livre=book,
            lecteur=lecteur,
            date_retour_prevue=date_retour
        )
        
        # Update book availability
        book.disponibilite = False
        book.save()
        
        messages.success(request, f"Vous avez emprunté '{book.titre}'. Date de retour: {date_retour.strftime('%d/%m/%Y')}")
        return redirect('book_detail', book_id=book_id)
    
    return redirect('book_detail', book_id=book_id)

# @login_required
def join_waitlist(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Livre, id=book_id)
        
        # Check if book is already available
        if book.disponibilite:
            messages.info(request, "Ce livre est disponible, vous pouvez l'emprunter directement.")
            return redirect('book_detail', book_id=book_id)
        
        # Get the current user as a Lecteur
        try:
            lecteur = Lecteur.objects.get(user=request.user)
        except Lecteur.DoesNotExist:
            messages.error(request, "Votre profil de lecteur n'existe pas.")
            return redirect('book_detail', book_id=book_id)
        
        # Check if user is already in the waiting list
        if book.liste_attente.filter(id=lecteur.id).exists():
            messages.info(request, "Vous êtes déjà sur la liste d'attente pour ce livre.")
            return redirect('book_detail', book_id=book_id)
        
        # Add user to waiting list
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
    
    return render(request, 'book_form.html', {'form': form})

def edit_book(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            # Handle image removal if checkbox is checked
            if request.POST.get('remove_image') and book.image:
                book.image.delete()
                book.image = None
            
            form.save()
            messages.success(request, 'Book updated successfully.')
            return redirect('book_management')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'book_form.html', {'form': form, 'book': book})

def delete_book(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('book_management')
    
    return render(request, 'book_delete.html', {'book': book})