from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from biblio_smart.models import Livre
from biblio_smart.models import Emprunt, Lecteur, Utilisateur, Notification, BookComment, BookRating
from django.shortcuts import get_object_or_404, redirect
from django.db import models
from .forms import BookForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now
import re
from .decorators import custom_login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import JsonResponse

def index(request):
    books_list = Livre.objects.all().order_by('-id')
    paginator = Paginator(books_list, 8)  # 8 livres par page
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)
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

# def add_book(request):
#     if request.method == 'POST':
#         titre = request.POST.get('titre')
#         auteur = request.POST.get('auteur')
#         ISBN = request.POST.get('ISBN')
        
#         categorie = request.POST.get('categorie')
#         if categorie == 'other':
#             categorie = request.POST.get('custom_categorie')

#         image = request.FILES.get('image')
#         description = request.POST.get('description') 

#         new_book = Livre(
#             titre=titre,
#             auteur=auteur,
#             ISBN=ISBN,
#             categorie=categorie,
#             disponibilite=True, 
#             image=image,
#             description=description
#         )
#         new_book.save()

#         messages.success(request, f"Book '{new_book.titre}' added successfully.")
#         return redirect('book_management')
#     else:
#         categories = Livre.objects.values_list('categorie', flat=True).distinct()
#         return render(request, 'book_form.html', {'categories': categories})

def add_book(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        auteur = request.POST.get('auteur')
        ISBN = request.POST.get('ISBN')
        
        categorie = request.POST.get('categorie')
        if categorie == 'other':
            categorie = request.POST.get('custom_categorie')

        disponibilite = request.POST.get('disponibilite', 'True') == 'True'
        description = request.POST.get('description') 

        # Create book object first without saving to DB
        new_book = Livre(
            titre=titre,
            auteur=auteur,
            ISBN=ISBN,
            categorie=categorie,
            disponibilite=disponibilite,
            description=description
        )

        # Handle user-uploaded image
        if 'image' in request.FILES:
            new_book.image = request.FILES.get('image')
        # If no direct upload but URL provided, download from URL
        elif 'cover_image_url' in request.POST and request.POST.get('cover_image_url'):
            cover_url = request.POST.get('cover_image_url')
            try:
                import requests
                from django.core.files.base import ContentFile
                from urllib.parse import urlparse
                
                response = requests.get(cover_url)
                if response.status_code == 200:
                    # Extract filename from URL or create one based on ISBN
                    image_name = urlparse(cover_url).path.split('/')[-1]
                    if not image_name or not image_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        image_name = f"cover_{ISBN}.jpg"
                    
                    # Save the image content to the model field
                    new_book.image.save(image_name, ContentFile(response.content), save=False)
                    messages.success(request, "Cover image was downloaded automatically.")
            except Exception as e:
                messages.warning(request, f"Could not download cover image: {str(e)}")
        
        # Save the book with the image attached
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
    books_qs = Livre.objects.all()
    categories = Livre.objects.values_list('categorie', flat=True).distinct()

    category = request.GET.get('category')
    if category:
        books_qs = books_qs.filter(categorie=category)

    availability = request.GET.get('availability')
    if availability == 'available':
        books_qs = books_qs.filter(disponibilite=True)
    elif availability == 'borrowed':
        books_qs = books_qs.filter(disponibilite=False)

    search_query = request.GET.get('search')
    if search_query:
        books_qs = books_qs.filter(
            models.Q(titre__icontains=search_query) |
            models.Q(auteur__icontains=search_query) |
            models.Q(ISBN__icontains=search_query)
        )

    sort = request.GET.get('sort')
    if sort == 'title_asc':
        books_qs = books_qs.order_by('titre')
    elif sort == 'title_desc':
        books_qs = books_qs.order_by('-titre')
    elif sort == 'author_asc':
        books_qs = books_qs.order_by('auteur')
    elif sort == 'recent':
        books_qs = books_qs.order_by('-date_ajout')

    paginator = Paginator(books_qs, 10) 
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)

    return render(request, 'books.html', {'books': books, 'categories': categories})

def book_detail(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    similar_books = Livre.objects.filter(categorie=book.categorie).exclude(id=book.id)[:5]

    utilisateur_id = request.session.get('utilisateur_id')
    utilisateur_role = request.session.get('utilisateur_role')
    is_in_waitlist = False
    
    try:
        utilisateur = Utilisateur.objects.get(id=utilisateur_id)
    except (Utilisateur.DoesNotExist, TypeError):
        utilisateur = None

    # Let's be very explicit with the query to find the emprunt record
    emprunt = None
    if utilisateur:
        try:
            # Use the exact values we know exist in the database
            emprunt = Emprunt.objects.filter(
                livre_id=book.id,
                lecteur_id=utilisateur.id,
                returned=0  # Explicitly use 0 instead of False
            ).first()
            
            # Check if the user is in the waitlist (only for readers)
            if utilisateur_role == 'lecteur':
                try:
                    lecteur = Lecteur.objects.get(id=utilisateur.id)
                    is_in_waitlist = book.liste_attente.filter(id=lecteur.id).exists()
                except Lecteur.DoesNotExist:
                    pass
                
        except Exception as e:
            print(f"Error fetching emprunt: {e}")

    # Get all comments with their associated ratings in one go
    comments = book.comments.all().select_related('lecteur')
    comment_data = []
    
    for comment in comments:
        # Get the rating for this comment's author on this book
        rating = BookRating.objects.filter(lecteur=comment.lecteur, livre=book).first()
        comment_data.append({
            'comment': comment,
            'rating': rating
        })
    
    return render(request, 'book_detail.html', {
        'book': book,
        'similar_books': similar_books,
        'utilisateur': utilisateur,
        'emprunt': emprunt,
        'active_emprunt': emprunt is not None,
        'is_in_waitlist': is_in_waitlist,
        'comment_data': comment_data,  # Add this to the context
    })

# @login_required
def borrow_book(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Livre, id=book_id)
        
        utilisateur_id = request.session.get('utilisateur_id')
        if not utilisateur_id:
            messages.error(request, "Vous devez être connecté pour emprunter un livre.")
            return redirect('connexion')
        
        try:
            lecteur = Lecteur.objects.get(id=utilisateur_id)
        except Lecteur.DoesNotExist:
            messages.error(request, "Votre profil de lecteur n'existe pas.")
            return redirect('book_detail', book_id=book_id)
        
        # Check waiting list logic
        waiting_list = list(book.liste_attente.all())
        
        if not book.disponibilite:
            messages.error(request, "Ce livre n'est pas disponible actuellement.")
            return redirect('book_detail', book_id=book_id)
        elif waiting_list:
            # Someone is on the waiting list
            first_in_line = waiting_list[0] if waiting_list else None
            
            if first_in_line and first_in_line.id == lecteur.id:
                # Current user is first in line, remove from waiting list
                book.liste_attente.remove(lecteur)
                messages.info(request, "Vous étiez premier(e) sur la liste d'attente et pouvez maintenant emprunter ce livre.")
            else:
                # Someone else is first in line
                is_in_waitlist = book.liste_attente.filter(id=lecteur.id).exists()
                if is_in_waitlist:
                    position = waiting_list.index(lecteur) + 1
                    messages.error(request, f"Vous êtes en position {position} sur la liste d'attente. Veuillez attendre votre tour.")
                else:
                    messages.error(request, "Il y a des personnes sur la liste d'attente qui ont priorité pour emprunter ce livre.")
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

        # Create notification about borrowed book
        try:
            # Get the Utilisateur object for the lecteur
            utilisateur = Utilisateur.objects.get(id=lecteur.id)
            
            # Format dates for better readability
            formatted_start = start_date.strftime('%d %b %Y')
            formatted_end = end_date.strftime('%d %b %Y')
            
            # Create the notification
            Notification.objects.create(
                user=utilisateur,
                message=f"You borrowed '{book.titre}'. Return by: {formatted_end}",
                type='book_borrowed',
                link=f'/livres/book/{book.id}/',
                read=False
            )
        except Exception as e:
            print(f"Failed to create notification: {e}")
        
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
    books_list = Livre.objects.all().order_by('-id')
    search_query = request.GET.get('search')
    category = request.GET.get('category')
    availability = request.GET.get('availability')

    if search_query:
        books_list = books_list.filter(
            models.Q(titre__icontains=search_query) |
            models.Q(auteur__icontains=search_query) |
            models.Q(ISBN__icontains=search_query)
        )
    if category:
        books_list = books_list.filter(categorie=category)
    if availability == 'available':
        books_list = books_list.filter(disponibilite=True)
    elif availability == 'borrowed':
        books_list = books_list.filter(disponibilite=False)

    paginator = Paginator(books_list, 8)
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)
    categories = Livre.objects.values_list('categorie', flat=True).distinct()
    return render(request, 'book_management.html', {
        'books': books,
        'categories': categories,
    })
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

        new_disponibilite = request.POST.get('disponibilite') == 'True'

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
    
    # Find the latest active loan for this book and user
    emprunt = Emprunt.objects.filter(
        livre=book,         
        lecteur=utilisateur,
        returned=False
    ).order_by('-id').first()

    if emprunt:
        # Current date for return
        today = timezone.now().date()
        emprunt.date_retour = today
        emprunt.returned = True
        
        # Check if the book is returned late
        is_late = today > emprunt.date_retour_prevue
        days_late = 0
        fee_amount = 0
        
        if is_late:
            # Calculate days late and fees (€0.50 per day)
            days_late = (today - emprunt.date_retour_prevue).days
            fee_amount = days_late * 0.50
            emprunt.fee = fee_amount
            
            # Create notification about late return
            Notification.objects.create(
                user=utilisateur,
                message=f"You returned '{book.titre}' {days_late} days late. Fee: €{fee_amount:.2f}",
                type='book_returned_late',
                link=f'/emprunt/fees/{utilisateur.id}/',
                read=False
            )
            
            messages.warning(
                request, 
                f"You have returned '{book.titre}' {days_late} days late. A fee of €{fee_amount:.2f} has been added to your account."
            )
        else:
            # Create notification about on-time return
            Notification.objects.create(
                user=utilisateur,
                message=f"You returned '{book.titre}' on time. Thank you!",
                type='book_returned',
                link=f'/livres/book/{book.id}/',
                read=False
            )
            
            messages.success(
                request, 
                f"You have successfully returned '{book.titre}' on time. Thank you!"
            )
        
        emprunt.save()
        
        # Make the book available again
        book.disponibilite = True
        book.save()
        
        # Check if anyone is on the waiting list
        waiting_list = list(book.liste_attente.all())
        if waiting_list:
            next_reader = waiting_list[0]
            
            # Notify the next reader
            try:
                next_user = Utilisateur.objects.get(id=next_reader.id)
                
                Notification.objects.create(
                    user=next_user,
                    message=f"The book '{book.titre}' you were waiting for is now available! You can borrow it now.",
                    type='book_available',
                    link=f'/livres/book/{book.id}/',
                    read=False
                )
                
                print(f"Notified next reader {next_reader.nom} about book availability")
            except Exception as e:
                print(f"Failed to notify next reader: {e}")
        
        # Save the emprunt ID in session for the review process
        request.session['pending_review_emprunt_id'] = emprunt.id
        
        # Redirect to the review page instead of book detail
        return redirect('review_book', book_id=book_id)
    else:
        print("No active borrowing record found for this user and book.")
        messages.error(request, "You cannot return a book that you haven't borrowed.")

    return redirect('book_detail', book_id=book_id)


def logout(request):
    request.session.flush()
    messages.success(request, 'Vous êtes déconnecté avec succès.')
    return redirect('connexion')

def review_book(request, book_id):
    book = get_object_or_404(Livre, id=book_id)
    utilisateur_id = request.session.get('utilisateur_id')
    emprunt_id = request.session.get('pending_review_emprunt_id')
    
    if not utilisateur_id:
        messages.error(request, "You must be logged in to review a book.")
        return redirect('connexion')
    
    if not emprunt_id:
        messages.error(request, "No pending review found.")
        return redirect('book_detail', book_id=book_id)
    
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    emprunt = get_object_or_404(Emprunt, id=emprunt_id)
    
    # Only allow reviewing if the loan is complete and belongs to this user
    if not emprunt.returned or emprunt.lecteur.id != utilisateur_id or emprunt.livre.id != book_id:
        messages.error(request, "You cannot review this book at this time.")
        return redirect('book_detail', book_id=book_id)
    
    return render(request, 'review_book.html', {
        'book': book,
        'emprunt': emprunt
    })

def submit_review(request, book_id):
    if request.method != 'POST':
        return redirect('book_detail', book_id=book_id)
    
    book = get_object_or_404(Livre, id=book_id)
    utilisateur_id = request.session.get('utilisateur_id')
    emprunt_id = request.session.get('pending_review_emprunt_id')
    
    if not utilisateur_id or not emprunt_id:
        messages.error(request, "Invalid review submission.")
        return redirect('book_detail', book_id=book_id)
    
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    lecteur = get_object_or_404(Lecteur, id=utilisateur_id)
    emprunt = get_object_or_404(Emprunt, id=emprunt_id)
    
    rating_value = request.POST.get('rating')
    comment_text = request.POST.get('comment')
    
    # Save rating if provided
    if rating_value:
        try:
            rating_value = int(rating_value)
            if 1 <= rating_value <= 5:
                # Update existing rating or create new one
                BookRating.objects.update_or_create(
                    livre=book,
                    lecteur=lecteur,
                    defaults={
                        'value': rating_value,
                        'emprunt': emprunt
                    }
                )
        except ValueError:
            messages.error(request, "Invalid rating value.")
    
    # Save comment if provided
    if comment_text and comment_text.strip():
        BookComment.objects.create(
            livre=book,
            lecteur=lecteur,
            emprunt=emprunt,
            text=comment_text
        )
    
    # Clear the pending review from session
    if 'pending_review_emprunt_id' in request.session:
        del request.session['pending_review_emprunt_id']
    
    messages.success(request, "Thank you for your review!")
    return redirect('book_detail', book_id=book_id)


from django.http import JsonResponse
import json

# Bulk Actions
def bulk_delete_books(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_ids = data.get('book_ids', [])
            
            # Delete the selected books
            deleted_count = Livre.objects.filter(id__in=book_ids).delete()[0]
            
            messages.success(request, f"{deleted_count} books were successfully deleted.")
            return JsonResponse({'status': 'success', 'deleted_count': deleted_count})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def bulk_update_availability(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_ids = data.get('book_ids', [])
            availability = data.get('availability', True)  # Default to available
            
            # Update the availability of selected books
            updated_count = Livre.objects.filter(id__in=book_ids).update(disponibilite=availability)
            
            status = "available" if availability else "borrowed"
            messages.success(request, f"{updated_count} books were marked as {status}.")
            return JsonResponse({'status': 'success', 'updated_count': updated_count})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)



