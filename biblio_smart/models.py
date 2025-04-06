from django.db import models

class Utilisateur(models.Model):
    nom = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=[('lecteur', 'Lecteur'), ('bibliothecaire', 'Bibliothecaire')])

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
    liste_attente = models.ManyToManyField('Lecteur', blank=True)

    def mettre_a_jour_disponibilite(self):
        pass


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
    date_retour = models.DateField()
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE)
    lecteur = models.ForeignKey(Lecteur, on_delete=models.CASCADE)

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