from django.shortcuts import render, redirect
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
import calendar

def dashboard(request):    
    # Redirect based on user role
    user_role = request.session.get('utilisateur_role')
    if user_role == 'lecteur':
        return redirect('reader_dashboard')
    elif user_role == 'bibliothecaire':
        return redirect('librarian_dashboard')
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('home')

def reader_dashboard(request):
    
    user_id = request.session.get('utilisateur_id')
    
    # Import models here to avoid circular imports
    from biblio_smart.models import Utilisateur, Lecteur, Livre, Emprunt
    
    try:
        user = Lecteur.objects.get(id=user_id)
    except Lecteur.DoesNotExist:
        messages.error(request, 'Reader account not found.')
        return redirect('login')

    # Get current date for calculations - DEFINE THIS FIRST
    today = timezone.now().date()
    
    # Current loans (books not returned yet) - DEFINE THESE BEFORE USING
    current_loans = Emprunt.objects.filter(
        lecteur=user,
        returned=False
    ).order_by('date_retour_prevue')  # Use date_retour_prevue instead of date_retour
    
    # Overdue loans - DEFINE THIS BEFORE USING IT
    overdue_loans = current_loans.filter(date_retour_prevue__lt=today)
    
    # Get session values
    overdue_count = request.session.get('overdue_count', 0)
    current_overdue_count = request.session.get('current_overdue_count', 0)
    past_overdue_count = request.session.get('past_overdue_count', 0)
    total_fees = request.session.get('total_fees', 0)
    
    # Display messages about overdue books and fees
    if current_overdue_count > 0:
        messages.warning(
            request, 
            f"You have {current_overdue_count} overdue books with fees of €{total_fees:.2f}. "
            f"Please return them as soon as possible."
        )
    
    # Calculate fees for overdue loans in real-time
    for loan in overdue_loans:
        days_overdue = (today - loan.date_retour_prevue).days
        loan.fee = days_overdue * 0.50
    
    # Books due soon (in the next 3 days)
    due_soon = current_loans.filter(
        date_retour_prevue__gte=today,
        date_retour_prevue__lte=today + timedelta(days=3)
    )
    
    # Reading history (returned books)
    reading_history = Emprunt.objects.filter(
        lecteur=user,
        returned=True
    ).order_by('-date_retour')[:5]
    
    # Favorite books
    favorite_books = user.favorites.all()[:5]
    
    # Book recommendations
    borrowed_categories = Emprunt.objects.filter(
        lecteur=user
    ).values_list('livre__categorie', flat=True).distinct()
    
    recommended_books = Livre.objects.filter(
        categorie__in=borrowed_categories
    ).exclude(
        id__in=Emprunt.objects.filter(lecteur=user).values_list('livre__id', flat=True)
    ).order_by('?')[:4]
    
    # Reading statistics
    total_books_read = Emprunt.objects.filter(
        lecteur=user,
        returned=True
    ).count()
    
    books_this_month = Emprunt.objects.filter(
        lecteur=user,
        date_emprunt__month=today.month,
        date_emprunt__year=today.year
    ).count()
    
    # Create context DICTIONARY first
    context = {
        'user': user,
        'current_loans': current_loans,
        'overdue_loans': overdue_loans,
        'due_soon': due_soon,
        'reading_history': reading_history,
        'favorite_books': favorite_books,
        'recommended_books': recommended_books,
        'total_books_read': total_books_read,
        'books_this_month': books_this_month,
        'today': today,
        'overdue_count': overdue_count,
        'total_fees': total_fees,
    }
    
    return render(request, 'dashboard/reader.html', context)

def librarian_dashboard(request):
    
    user_id = request.session.get('utilisateur_id')
    
    # Import models here to avoid circular imports
    from biblio_smart.models import Utilisateur, Bibliothecaire, Livre, Emprunt, Lecteur
    
    try:
        user = Bibliothecaire.objects.get(id=user_id)
    except Bibliothecaire.DoesNotExist:
        messages.error(request, 'Librarian account not found.')
        return redirect('login')
    
    # Get current date for calculations
    today = timezone.now().date()
    
    # System statistics
    total_books = Livre.objects.count()
    total_users = Utilisateur.objects.count()
    total_readers = Lecteur.objects.count()
    total_librarians = Bibliothecaire.objects.count()
    
    # Books statistics
    available_books = Livre.objects.filter(disponibilite=True).count()
    borrowed_books = total_books - available_books
    
    # Loan statistics
    total_loans = Emprunt.objects.count()
    active_loans = Emprunt.objects.filter(returned=False).count()
    overdue_loans = Emprunt.objects.filter(
        returned=False,
        date_retour__lt=today
    ).count()
    
    # Recent activities
    recent_loans = Emprunt.objects.filter(
        date_emprunt__gte=today - timedelta(days=7)
    ).order_by('-date_emprunt')[:5]
    
    recent_returns = Emprunt.objects.filter(
        returned=True
    ).order_by('-date_retour')[:5]

    # Popular books (most borrowed)
    popular_books = Livre.objects.annotate(
        loan_count=Count('emprunt')
    ).order_by('-loan_count')[:5]

    now = timezone.now()
    year, month = now.year, now.month
    last_day = calendar.monthrange(year, month)[1]  # Get the last day of the month

    first_day_of_month = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
    last_day_of_month = timezone.datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.get_current_timezone())

    # Query for users created in this date range
    new_users = Utilisateur.objects.filter(
        date_inscription__range=(first_day_of_month, last_day_of_month)
    ).count()
    
    context = {
        'user': user,
        'total_books': total_books,
        'total_users': total_users,
        'total_readers': total_readers,
        'total_librarians': total_librarians,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'recent_loans': recent_loans,
        'recent_returns': recent_returns,
        'popular_books': popular_books,
        'new_users': new_users,
        'today': today,
    }
    
    return render(request, 'dashboard/librarian.html', context)