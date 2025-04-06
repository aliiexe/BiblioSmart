from django.contrib import admin
from .models import Utilisateur, Livre, Lecteur, Bibliothecaire, Emprunt, Amende, Rapport, Evenement

admin.site.register(Utilisateur)
admin.site.register(Livre)
admin.site.register(Lecteur)
admin.site.register(Bibliothecaire)
admin.site.register(Emprunt)
admin.site.register(Amende)
admin.site.register(Rapport)
admin.site.register(Evenement)