from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, fields
from datetime import timedelta
from biblio_smart.models import Utilisateur, Lecteur, Bibliothecaire, Livre, Emprunt, Amende

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
    ).order_by('date_retour_prevue')
    
    # CURRENT overdue loans (not yet returned but past due date)
    overdue_loans = current_loans.filter(date_retour_prevue__lt=today)
    
    # RETURNED LATE loans (already returned but returned after the due date)
    returned_late = Emprunt.objects.filter(
        returned=True,
        date_retour__gt=F('date_retour_prevue')
    )
    
    print(f"DEBUG: Found {overdue_loans.count()} current overdue loans")
    print(f"DEBUG: Found {returned_late.count()} returned late loans")
    
    # DIRECT QUERY to get all fees from the Amende model
    all_amendes = Amende.objects.all()
    print(f"DEBUG: Total amendes in database: {all_amendes.count()}")
    
    # Calculate fees (€0.50 per day overdue) for current overdue loans
    fee_per_day = 0.50
    calculated_fees = 0
    
    for loan in overdue_loans:
        days_overdue = (today - loan.date_retour_prevue).days
        loan.fee = days_overdue * fee_per_day
        calculated_fees += loan.fee
    
    # Calculate fees for RETURNED LATE loans too!
    for loan in returned_late:
        # For returned loans, use actual return date instead of today
        days_overdue = (loan.date_retour - loan.date_retour_prevue).days
        loan.fee = days_overdue * fee_per_day
        calculated_fees += loan.fee
        print(f"DEBUG: Calculated fee for returned late loan {loan.id}: €{loan.fee:.2f}")
    
    # Get total from database directly
    existing_fees = all_amendes.aggregate(total=Sum('montant'))['total'] or 0
    
    # Use the sum of both calculated and existing fees
    total_fees = existing_fees if existing_fees > 0 else calculated_fees
    
    # Attach Amende records to each loan
    for loan in overdue_loans:
        try:
            amende = Amende.objects.get(emprunt=loan)
            loan.amende = amende
            loan.fee = amende.montant
            print(f"DEBUG: Found amende for loan {loan.id}: €{amende.montant}")
        except Amende.DoesNotExist:
            # No amende record exists - use calculated fee
            loan.amende = None
            print(f"DEBUG: No amende found for loan {loan.id}, using calculated fee: €{loan.fee}")
    
    # Attach Amende records to returned late loans too
    for loan in returned_late:
        try:
            amende = Amende.objects.get(emprunt=loan)
            loan.amende = amende
            loan.fee = amende.montant
            print(f"DEBUG: Found amende for returned late loan {loan.id}: €{amende.montant}")
        except Amende.DoesNotExist:
            # Keep the calculated fee we set earlier
            loan.amende = None
            print(f"DEBUG: No amende found for returned late loan {loan.id}, using calculated fee: €{loan.fee}")
    
    # Rest of your function remains the same...
    
    # Recent returns
    recent_returns = Emprunt.objects.filter(
        returned=True
    ).order_by('-date_retour')[:10]
    
    # Loans due today
    due_today = current_loans.filter(date_retour_prevue=today)
    
    # Loans due soon
    due_soon = current_loans.filter(
        date_retour_prevue__gt=today,
        date_retour_prevue__lte=today + timedelta(days=7)
    )
    
    print(f"DEBUG: Total calculated fees: €{calculated_fees:.2f}")
    print(f"DEBUG: Total existing fees from database: €{existing_fees:.2f}")
    print(f"DEBUG: Final total fees: €{total_fees:.2f}")
    
    context = {
        'current_loans': current_loans,
        'overdue_loans': overdue_loans,
        'returned_late': returned_late,
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

def user_fees(request, user_id):
    # Security check
    current_user_id = request.session.get('utilisateur_id')
    current_user_role = request.session.get('utilisateur_role')
    
    if current_user_id is None:
        messages.error(request, 'You need to be logged in to view fees.')
        return redirect('connexion')
    
    # Only the user themselves or a librarian can view fees
    if int(current_user_id) != int(user_id) and current_user_role != 'bibliothecaire':
        messages.error(request, 'You do not have permission to view these fees.')
        return redirect('dashboard')
    
    # Get the user
    try:
        user = Lecteur.objects.get(id=user_id)
    except Lecteur.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('dashboard')
    
    # Get all fines for the user
    amendes = Amende.objects.filter(
        emprunt__lecteur=user
    ).select_related('emprunt', 'emprunt__livre').order_by('-emprunt__date_retour_prevue')
    
    # Calculate totals
    unpaid_amendes = amendes.filter(statut=False)
    total_unpaid = sum(amende.montant for amende in unpaid_amendes)
    
    context = {
        'user': user,
        'amendes': amendes,
        'unpaid_amendes': unpaid_amendes,
        'total_unpaid': total_unpaid,
    }
    
    return render(request, 'emprunts/user_fees.html', context)

# ========

from django.db.models import Sum

def pay_fees(request, user_id):
    # Vérifiez si l'utilisateur est connecté
    current_user_id = request.session.get('utilisateur_id')
    if current_user_id is None:
        messages.error(request, "Vous devez être connecté pour payer vos frais.")
        return redirect('connexion')

    # Vérifiez si l'utilisateur a la permission
    if int(current_user_id) != user_id and request.session.get('utilisateur_role') != 'bibliothecaire':
        messages.error(request, "Vous n'avez pas la permission de payer ces frais.")
        return redirect('dashboard')

    # Récupérez les amendes impayées pour l'utilisateur
    user = get_object_or_404(Lecteur, id=user_id)
    unpaid_amendes = Amende.objects.filter(emprunt__lecteur=user, statut=False)
    total_unpaid = sum(amende.montant for amende in unpaid_amendes)

    if request.method == 'POST':
        # Simuler un paiement réussi
        payment_method = request.POST.get('payment_method')
        if payment_method and total_unpaid > 0:
            # Marquer toutes les amendes comme payées
            unpaid_amendes.update(statut=True)

            # Mettre à jour le total des frais dans la session
            remaining_fees = Amende.objects.filter(emprunt__lecteur=user, statut=False).aggregate(total=Sum('montant'))['total'] or 0
            request.session['total_fees'] = float(remaining_fees) if remaining_fees is not None else 0.0

            # Sauvegarder la session
            request.session.modified = True

            # Debug line to check the value
            print(f"Updated session total_fees: {request.session['total_fees']}")

            messages.success(request, f"Paiement de {total_unpaid:.2f} € effectué avec succès via {payment_method}.")
            return redirect('user_fees', user_id=user_id)
        else:
            messages.error(request, "Une erreur s'est produite lors du paiement. Veuillez réessayer.")

    return render(request, 'emprunts/pay_fees.html', {
        'user': user,
        'unpaid_amendes': unpaid_amendes,
        'total_unpaid': total_unpaid,
    })