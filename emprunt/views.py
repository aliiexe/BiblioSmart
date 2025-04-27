from django.shortcuts import get_object_or_404, render, redirect
from biblio_smart.models import Livre, Emprunt
from django import forms
from biblio_smart.models import Livre, Emprunt, Lecteur
# Formulaire pour gérer les emprunts
class EmpruntForm(forms.ModelForm):
    class Meta:
        model = Emprunt
        fields = ['date_emprunt', 'date_retour', 'lecteur']

def emprunt_livre(request, livre_id):
    livre = get_object_or_404(Livre, id=livre_id)  # Récupérer le livre par son ID
    lecteurs = Lecteur.objects.all()
    if request.method == 'POST':
        form = EmpruntForm(request.POST)
        if form.is_valid():
            emprunt = form.save(commit=False)
            emprunt.livre = livre  # Associer le livre automatiquement
            emprunt.save()
            return redirect('index')  # Rediriger vers la page d'index ou un autre endroit
    else:
        form = EmpruntForm()

        return render(request, 'emprunt_form.html', {'form': form, 'livre': livre, 'lecteurs': lecteurs})