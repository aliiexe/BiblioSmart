from django.shortcuts import render
from livres.models import Livre
from django.db.models import Count

def index(request):
    most_borrowed_books = (
        Livre.objects.annotate(borrow_count=Count('emprunt'))
        .order_by('-borrow_count')[:3]
    )

    return render(request, 'pgAcc/index.html', {
        'most_borrowed_books': most_borrowed_books,
    })