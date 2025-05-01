from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, fields
from datetime import timedelta
from biblio_smart.models import Utilisateur, Lecteur, Bibliothecaire, Livre, Emprunt

def loans_dashboard(request):
    
    # Redirect based on user role
    utilisateur_role = request.session.get('utilisateur_role')
    if utilisateur_role == 'lecteur':
        return redirect('user_loans', user_id=request.session.get('utilisateur_id'))
    elif utilisateur_role == 'bibliothecaire':
        return redirect('all_loans')
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('dashboard')

def user_loans(request, user_id):
    
    # Check if the logged-in user is viewing their own loans
    current_user_id = request.session.get('utilisateur_id')
    if current_user_id is None:
        messages.error(request, 'You need to be logged in to view loans.')
        return redirect('connexion')
        
    if int(current_user_id) != int(user_id):
        messages.error(request, 'You can only view your own loans.')
        return redirect('dashboard')
    
    try:
        if request.session.get('utilisateur_role') == 'lecteur':
            user = Lecteur.objects.get(id=user_id)
        else:
            user = Bibliothecaire.objects.get(id=user_id)
    except (Lecteur.DoesNotExist, Bibliothecaire.DoesNotExist):
        messages.error(request, 'User not found.')
        return redirect('dashboard')
    
    # Get current date for calculations
    today = timezone.now().date()
    
    # Current loans (books not returned yet)
    current_loans = Emprunt.objects.filter(
        lecteur=user,
        returned=False
    ).order_by('date_retour')
    
    # Overdue loans
    overdue_loans = current_loans.filter(date_retour__lt=today)
    
    # Calculate fees (€0.50 per day overdue)
    fee_per_day = 0.50
    
    for loan in overdue_loans:
        days_overdue = (today - loan.date_retour).days
        loan.fee = days_overdue * fee_per_day
    
    # Total fees
    total_fees = sum(loan.fee for loan in overdue_loans if hasattr(loan, 'fee'))
    
    # Loan history (returned books)
    loan_history = Emprunt.objects.filter(
        lecteur=user,
        returned=True
    ).order_by('-date_retour')
    
    context = {
        'user': user,
        'current_loans': current_loans,
        'overdue_loans': overdue_loans,
        'loan_history': loan_history,
        'total_fees': total_fees,
        'today': today,
    }
    
    return render(request, 'emprunts/user_loans.html', context)

def all_loans(request):
    
    # Get current date for calculations
    today = timezone.now().date()
    
    # All current loans
    current_loans = Emprunt.objects.filter(
        returned=False
    ).order_by('date_retour')
    
    # Overdue loans
    overdue_loans = current_loans.filter(date_retour__lt=today)
    
    # Calculate fees (€0.50 per day overdue)
    fee_per_day = 0.50
    
    for loan in overdue_loans:
        days_overdue = (today - loan.date_retour).days
        loan.fee = days_overdue * fee_per_day
    
    # Total fees
    total_fees = sum(loan.fee for loan in overdue_loans if hasattr(loan, 'fee'))
    
    # Recent returns
    recent_returns = Emprunt.objects.filter(
        returned=True
    ).order_by('-date_retour')[:10]
    
    # Loans due today
    due_today = current_loans.filter(date_retour=today)
    
    # Loans due in the next 7 days
    due_soon = current_loans.filter(
        date_retour__gt=today,
        date_retour__lte=today + timedelta(days=7)
    )
    
    context = {
        'current_loans': current_loans,
        'overdue_loans': overdue_loans,
        'recent_returns': recent_returns,
        'due_today': due_today,
        'due_soon': due_soon,
        'total_fees': total_fees,
        'today': today,
    }
    
    return render(request, 'emprunts/all_loans.html', context)

def loan_detail(request, loan_id):
    
    loan = get_object_or_404(Emprunt, id=loan_id)
    
    # Check if the logged-in user is the borrower or a librarian
    current_user_id = request.session.get('utilisateur_id')
    current_user_role = request.session.get('utilisateur_role')
    
    if current_user_id is None:
        messages.error(request, 'You need to be logged in to view loans.')
        return redirect('connexion')
    
    # Check if the user has permission to view this loan
    if int(current_user_id) != loan.lecteur.id and current_user_role != 'bibliothecaire':
        messages.error(request, 'You do not have permission to view this loan.')
        return redirect('dashboard')
    
    # Get current date for calculations
    today = timezone.now().date()
    
    # Calculate fee if overdue - using date_retour_prevue instead of date_retour
    fee_per_day = 0.50
    
    # Use date_retour_prevue for checking if loan is overdue
    if not loan.returned and loan.date_retour_prevue and loan.date_retour_prevue < today:
        days_overdue = (today - loan.date_retour_prevue).days
        loan.fee = days_overdue * fee_per_day
    else:
        loan.fee = 0
    
    context = {
        'loan': loan,
        'today': today,
    }
    
    return render(request, 'emprunts/loan_detail.html', context)

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