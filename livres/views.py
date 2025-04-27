from django.shortcuts import render
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

        new_book = Livre(
            titre=titre,
            auteur=auteur,
            ISBN=ISBN,
            categorie=categorie,
            disponibilite=disponibilite
        )
        new_book.save()

        return render(request, 'index.html', {'books': Livre.objects.all()})
    else:
        return render(request, 'add.html')