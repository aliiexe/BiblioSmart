from django.utils import timezone
from biblio_smart.models import Emprunt, Amende
from datetime import timedelta
from django.db import models

def check_overdue_loans(user_id):
    """
    Comprehensive check of a user's loans:
    - Checks current unreturned overdue loans
    - Checks returned loans that were returned late
    - Calculates and stores fees in Amende model
    - Returns statistics for display
    """
    today = timezone.now().date()
    fee_per_day = 0.50  # €0.50 per day
    
    # Statistics to return
    stats = {
        'current_overdue_count': 0,
        'current_overdue_fees': 0,
        'past_overdue_count': 0,
        'past_overdue_fees': 0,
        'total_overdue_count': 0,
        'total_fees': 0,
    }
    
    # 1. Check current unreturned and overdue loans
    current_overdue = Emprunt.objects.filter(
        lecteur_id=user_id,
        returned=False,
        date_retour_prevue__lt=today
    )
    
    stats['current_overdue_count'] = current_overdue.count()
    
    for loan in current_overdue:
        # First check if the loan already has a paid fine
        existing_paid_amende = Amende.objects.filter(emprunt=loan, statut=True).exists()
        
        # Skip this loan if it already has a paid fine
        if existing_paid_amende:
            continue
            
        days_overdue = (today - loan.date_retour_prevue).days
        fee = days_overdue * fee_per_day
        stats['current_overdue_fees'] += fee
        
        # Create or update fine record (only for unpaid fines)
        amende, created = Amende.objects.get_or_create(
            emprunt=loan,
            defaults={
                'montant': fee,
                'statut': False  # Not paid
            }
        )
        
        # If fine already exists and is unpaid, update the amount
        if not created and not amende.statut:
            amende.montant = fee
            amende.save()
    
    # 2. Check past returned loans that were returned late
    past_overdue = Emprunt.objects.filter(
        lecteur_id=user_id,
        returned=True,
        date_retour__gt=models.F('date_retour_prevue')
    )
    
    stats['past_overdue_count'] = past_overdue.count()
    
    for loan in past_overdue:
        # Check if the loan already has a paid fine
        existing_paid_amende = Amende.objects.filter(emprunt=loan, statut=True).exists()
        
        # Skip this loan if it already has a paid fine
        if existing_paid_amende:
            continue
            
        days_overdue = (loan.date_retour - loan.date_retour_prevue).days
        fee = days_overdue * fee_per_day
        stats['past_overdue_fees'] += fee
        
        # Check if fine already exists
        amende = Amende.objects.filter(emprunt=loan).first()
        
        # If no fine exists, create one
        if not amende:
            Amende.objects.create(
                emprunt=loan,
                montant=fee,
                statut=False  # Not paid
            )
        # If fine exists but is unpaid and amount is different, update it
        elif not amende.statut and amende.montant != fee:
            amende.montant = fee
            amende.save()
    
    # Calculate totals - but only include unpaid fees for the total
    unpaid_fees = Amende.objects.filter(
        emprunt__lecteur_id=user_id, 
        statut=False
    ).aggregate(total=models.Sum('montant'))['total'] or 0
    
    stats['total_overdue_count'] = stats['current_overdue_count'] + stats['past_overdue_count']
    stats['total_fees'] = float(unpaid_fees)
    
    return stats