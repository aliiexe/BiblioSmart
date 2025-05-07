from django.shortcuts import render
from django.db.models import Count
from biblio_smart.models import Livre, Utilisateur, Emprunt

def index(request):
    # Get the most borrowed books
    most_borrowed_books = Livre.objects.annotate(
        borrow_count=Count('emprunt')
    ).order_by('-borrow_count')[:10]
    
    # Get the newest books
    new_books = Livre.objects.order_by('-date_ajout')[:4]
    
    # Get featured books
    featured_books = Livre.objects.all()[:5]  # Replace with your logic for featured books
    
    # Get categories with counts
    categories = []
    category_icons = {
        'Fiction': 'fas fa-book',
        'Science': 'fas fa-flask',
        'History': 'fas fa-landmark',
        'Biography': 'fas fa-user-tie',
        'Art': 'fas fa-palette',
        'Technology': 'fas fa-laptop-code',
        # Add more mappings as needed
    }
    
    for category_name in Livre.objects.values_list('categorie', flat=True).distinct():
        count = Livre.objects.filter(categorie=category_name).count()
        icon = category_icons.get(category_name, 'fas fa-book')
        categories.append({
            'name': category_name,
            'count': count,
            'icon': icon
        })
    
    # Get statistics
    stats = {
        'total_books': Livre.objects.count(),
        'total_users': Utilisateur.objects.filter(role='lecteur').count(),
        'total_borrowed': Emprunt.objects.count(),
        'categories': Livre.objects.values('categorie').distinct().count()
    }
    
    # Sample testimonials
    testimonials = [
        {
            'name': 'John Doe',
            'member_since': 'Jan 2023',
            'rating': 5,
            'text': 'BiblioSmart has transformed how I discover and borrow books. The interface is intuitive and the collection is extensive!'
        },
        {
            'name': 'Jane Smith',
            'member_since': 'Mar 2023',
            'rating': 4,
            'text': 'I love being able to track my reading history and find new recommendations based on my interests.'
        },
        {
            'name': 'David Wilson',
            'member_since': 'Nov 2022',
            'rating': 5,
            'text': 'The notification system for due dates is a lifesaver. I never forget to return books on time now!'
        }
    ]
    
    return render(request, 'pgAcc/index.html', {
        'most_borrowed_books': most_borrowed_books,
        'new_books': new_books,
        'featured_books': featured_books,
        'categories': categories,
        'stats': stats,
        'testimonials': testimonials
    })