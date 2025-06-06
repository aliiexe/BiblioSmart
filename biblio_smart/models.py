from django.db import models
from django.core.mail import send_mail

class Utilisateur(models.Model):
    nom = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=191)
    mot_de_passe = models.CharField(max_length=255)
    date_inscription = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=50, choices=[('lecteur', 'Lecteur'), ('bibliothecaire', 'Bibliothecaire')])
    favorites = models.ManyToManyField('Livre', blank=True, related_name='favorited_by')
    
    def s_inscrire(self):
        pass

    def se_connecter(self):
        pass


class Livre(models.Model):
    titre = models.CharField(max_length=255)
    auteur = models.CharField(max_length=255)
    ISBN = models.CharField(max_length=13, unique=True)
    categorie = models.CharField(max_length=100)
    disponibilite = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    liste_attente = models.ManyToManyField('Lecteur', blank=True)
    # image = models.ImageField(upload_to='livres/static/images/', blank=True, null=True)
    image = models.ImageField(upload_to='livres/', blank=True, null=True)
    date_ajout = models.DateField(auto_now_add=True)
    date_modification = models.DateField(auto_now=True)

    def mettre_a_jour_disponibilite(self):
        pass
    
    def average_rating(self):
        """Returns the book's average rating as a float."""
        from django.db.models import Avg
        result = self.ratings.aggregate(Avg('value'))
        return result['value__avg'] or 0


class Lecteur(Utilisateur):
    def rechercher_livre(self, titre, auteur, categorie, ISBN):
        pass

    def consulter_disponibilite(self, livre):
        pass

    def reserver_livre(self, livre):
        pass

    def consulter_historique(self):
        pass

    def noter_livre(self, livre, note):
        pass

    def commenter_livre(self, livre, commentaire):
        pass

    def payer_amende(self, amende):
        pass


class Bibliothecaire(Utilisateur):
    def ajouter_livre(self, livre):
        pass

    def modifier_livre(self, livre):
        pass

    def supprimer_livre(self, livre):
        pass

    def gerer_emprunts(self):
        pass

    def enregistrer_utilisateur(self, utilisateur):
        pass

    def envoyer_alerte(self, retard):
        pass

    def generer_rapports(self, type):
        pass

    def enregistrer_retour(self, emprunt):
        pass


class Emprunt(models.Model):
    date_emprunt = models.DateField()
    date_retour = models.DateField(null=True, blank=True)
    date_retour_prevue = models.DateField(null=True, blank=True)
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE)
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE)
    returned = models.BooleanField(default=False)

    def enregistrer_emprunt(self):
        pass

    def enregistrer_retour(self):
        pass


class Amende(models.Model):
    montant = models.FloatField()
    statut = models.BooleanField(default=False)
    emprunt = models.OneToOneField(Emprunt, on_delete=models.CASCADE)

    def calculer_amende(self, retard):
        pass

    def payer_amende(self):
        pass


class Rapport(models.Model):
    type = models.CharField(max_length=100)
    contenu = models.TextField()

    def generer_rapport(self, type):
        pass

    def exporter_rapport(self, format):
        pass


class Evenement(models.Model):
    titre = models.CharField(max_length=255)
    date = models.DateField()
    description = models.TextField()

    def organiser_evenement(self):
        pass

    def annuler_evenement(self):
        pass

class Notification(models.Model):
    TYPE_CHOICES = (
        ('book_available', 'Book Available'),
        ('overdue', 'Overdue Book'),
        ('system', 'System Notification'),
        ('book_borrowed', 'Book Borrowed'),
        ('book_returned', 'Book Returned'),
        ('loan_paid', 'Loan Paid'),
    )
    
    user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    link = models.CharField(max_length=255, blank=True, null=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        # Call the original save method
        super().save(*args, **kwargs)

        # Send email notification for specific notification types
        if self.type in ['book_borrowed', 'book_returned', 'loan_paid']:
            try:
                # Verify user has an email
                if not self.user.email:
                    print(f"No email found for user {self.user.id}")
                    return
                    
                email_subject = ''
                if self.type == 'book_borrowed':
                    email_subject = 'Book Borrowed Notification'
                elif self.type == 'book_returned':
                    email_subject = 'Book Returned Notification'
                elif self.type == 'loan_paid':
                    email_subject = 'Loan Payment Confirmation'

                send_mail(
                    subject=email_subject,
                    message=self.message,
                    from_email='alibusinessbourak@gmail.com',
                    recipient_list=[self.user.email],
                    fail_silently=False,
                )
                print(f"Email sent successfully to {self.user.email}")
            except Exception as e:
                print(f"Failed to send email: {str(e)}")
                # Don't re-raise the exception so notification saves even if email fails

class BookComment(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='comments')
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE)
    emprunt = models.ForeignKey(Emprunt, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Comment by {self.lecteur.nom} on {self.livre.titre}"


class BookRating(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='ratings')
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE)
    emprunt = models.ForeignKey(Emprunt, on_delete=models.SET_NULL, null=True, blank=True)
    value = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Ensure a user can only rate a book once
        unique_together = ('livre', 'lecteur')
    
    def __str__(self):
        return f"{self.value} stars for {self.livre.titre} by {self.lecteur.nom}"