from django.shortcuts import redirect, render
from biblio_smart.models import Livre

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
        image = request.FILES.get('image')  

        new_book = Livre(
            titre=titre,
            auteur=auteur,
            ISBN=ISBN,
            categorie=categorie,
            disponibilite=disponibilite,
            image=image  
        )
        new_book.save()

        return render(request, 'index.html', {'books': Livre.objects.all()})
    else:
        return render(request, 'add.html')
    

def delete_book(request, book_id):
    book = Livre.objects.get(id=book_id)
    if request.method == 'POST':
        book.delete()
        return render(request, 'index.html', {'books': Livre.objects.all()})
    else:
        return render(request, 'delete.html', {'book': book})
    
def edit_book(request, book_id):
    book = Livre.objects.get(id=book_id)
    return render(request, 'edit.html', {'book': book})




def update_book(request, book_id):
    try:
        book = Livre.objects.get(id=book_id)
    except Livre.DoesNotExist:
        return render(request, 'error.html', {'message': 'Book not found.'})

    if request.method == 'POST':
        book.titre = request.POST.get('titre')
        book.auteur = request.POST.get('auteur')
        book.ISBN = request.POST.get('ISBN')
        book.categorie = request.POST.get('categorie')
        book.disponibilite = request.POST.get('disponibilite') == 'on'

        # Update the image if a new one is provided
        if request.FILES.get('image'):
            book.image = request.FILES.get('image')  # Update image if a new one is provided

        book.save()

        return render(request, 'index.html', {'books': Livre.objects.all()})  # Render the index page after update
    else:
        return render(request, 'edit.html', {'book': book})



def details_book(request, book_id):
    try:
        book = Livre.objects.get(id=book_id)
    except Livre.DoesNotExist:
        return render(request, 'error.html', {'message': 'Book not found.'})

    return render(request, 'details.html', {'book': book})

