from django.shortcuts import render
from biblio_smart.models import Livre

def index(request):
    books = Livre.objects.all()
    return render(request, 'index.html', {'books': books})