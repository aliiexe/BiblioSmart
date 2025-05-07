from itertools import count
from django.utils import timezone  # Assurez-vous d'importer timezone
from django.db.models import Count
from django.db.models.functions import ExtractYear, ExtractMonth
from django.shortcuts import render
from django.http import HttpResponse
from biblio_smart.models import Amende, Lecteur,Livre,Emprunt
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import xlsxwriter



import matplotlib.pyplot as plt
import base64
from io import BytesIO



def generate_graph(data, title, xlabel, ylabel):
    plt.figure(figsize=(6, 4))
    plt.bar(data.keys(), data.values(), color='skyblue')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graph_url = base64.b64encode(image_png).decode('utf-8')
    plt.close()
    return f"data:image/png;base64,{graph_url}"


def index(request):
    # Récupérer les données nécessaires
    books_data = {
        "Total_Livres": Livre.objects.count(),
        "Livres_Disponibles": Livre.objects.filter(disponibilite=True).count(),
        "Livres_Empruntés": Livre.objects.filter(disponibilite=False).count(),
    }

    users_data = {
        "Total_Utilisateurs": Lecteur.objects.count(),
        "Membres_Actifs": Lecteur.objects.filter(
            emprunt__date_emprunt__gte=timezone.now() - timezone.timedelta(days=365)
        ).distinct().count(),
        "Membres_Inactifs": Lecteur.objects.count() - Lecteur.objects.filter(
            emprunt__date_emprunt__gte=timezone.now() - timezone.timedelta(days=365)
        ).distinct().count(),
    }

    # Livre le plus et le moins emprunté
    most_borrowed = Livre.objects.annotate(emprunts_count=Count('emprunt')).order_by('-emprunts_count').first()
    least_borrowed = Livre.objects.annotate(emprunts_count=Count('emprunt')).order_by('emprunts_count').first()

    context = {
        "books_data": books_data,
        "users_data": users_data,
        "most_borrowed": most_borrowed,
        "least_borrowed": least_borrowed,
    }
    return render(request, 'rapports/index.html', context)
    # Récupérer les données nécessaires
    total_books = Livre.objects.count()
    total_users = Lecteur.objects.count()

    # Livre le plus emprunté
    most_borrowed = Livre.objects.annotate(emprunts_count=Count('emprunt')).order_by('-emprunts_count').first()
    least_borrowed = Livre.objects.annotate(emprunts_count=Count('emprunt')).order_by('emprunts_count').first()

    # Préparer les données pour les graphiques
    books_data = {
        "Total Livres": total_books,
        "Livres Disponibles": Livre.objects.filter(disponibilite=True).count(),
        "Livres Empruntés": Livre.objects.filter(disponibilite=False).count(),
    }

    users_data = {
        "Total Utilisateurs": total_users,
        "Membres Actifs": Lecteur.objects.filter(emprunt__date_emprunt__gte=timezone.now() - timezone.timedelta(days=365)).distinct().count(),
        "Membres Inactifs": total_users - Lecteur.objects.filter(emprunt__date_emprunt__gte=timezone.now() - timezone.timedelta(days=365)).distinct().count(),
    }

    # Générer les graphiques
    books_graph = generate_graph(books_data, "Statistiques des Livres", "Catégorie", "Nombre")
    users_graph = generate_graph(users_data, "Statistiques des Utilisateurs", "Catégorie", "Nombre")

    # Passer les données au template
    context = {
        "books_graph": books_graph,
        "users_graph": users_graph,
        "most_borrowed": most_borrowed,
        "least_borrowed": least_borrowed,
    }
    return render(request, 'rapports/index.html', context)


def rapport_livres(request):
    if request.method == 'POST':
        format_rapport = request.POST.get('format')

        # Récupérer les données des livres
        livres_disponibles = Livre.objects.filter(disponibilite=True)
        livres_empruntes = Livre.objects.filter(disponibilite=False)
        livres_en_retard = Livre.objects.filter(
            emprunt__returned=False,
            emprunt__date_retour_prevue__lt=timezone.now()  # Utilisez timezone.now()
        )
        livres_populaires = Livre.objects.annotate(
            emprunts_count=Count('emprunt')
        ).order_by('-emprunts_count')[:10]

        if format_rapport == 'pdf':
            return generate_books_pdf(livres_disponibles, livres_empruntes, livres_en_retard, livres_populaires)
        elif format_rapport == 'excel':
            return generate_books_excel(livres_disponibles, livres_empruntes, livres_en_retard, livres_populaires)

    return render(request, 'rapports/livres.html')

def generate_books_pdf(livres_disponibles, livres_empruntes, livres_en_retard, livres_populaires):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Rapport des Livres")

    # Ajouter un titre
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Rapport des Livres")

    # Ajouter les sections
    y = 700
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Livres Disponibles")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for livre in livres_disponibles:
        pdf.drawString(50, y, f"{livre.titre} - {livre.auteur}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Livres Empruntés")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for livre in livres_empruntes:
        pdf.drawString(50, y, f"{livre.titre} - {livre.auteur}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_livres.pdf"'
    return response


def generate_books_excel(livres_disponibles, livres_empruntes, livres_en_retard, livres_populaires):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Rapport des Livres")

    # Ajouter les colonnes
    worksheet.write(0, 0, "Titre")
    worksheet.write(0, 1, "Auteur")
    worksheet.write(0, 2, "Statut")

    row = 1
    for livre in livres_disponibles:
        worksheet.write(row, 0, livre.titre)
        worksheet.write(row, 1, livre.auteur)
        worksheet.write(row, 2, "Disponible")
        row += 1

    for livre in livres_empruntes:
        worksheet.write(row, 0, livre.titre)
        worksheet.write(row, 1, livre.auteur)
        worksheet.write(row, 2, "Emprunté")
        row += 1

    workbook.close()
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rapport_livres.xlsx"'
    return response



def rapport_adherents(request):
    if request.method == 'POST':
        format_rapport = request.POST.get('format')

        # Récupérer les données des adhérents
        membres_actifs = Lecteur.objects.filter(emprunt__date_emprunt__gte=timezone.now() - timezone.timedelta(days=365)).distinct()
        membres_inactifs = Lecteur.objects.exclude(id__in=membres_actifs.values_list('id', flat=True))
        utilisateurs_en_retard = Lecteur.objects.filter(
            emprunt__returned=False,
            emprunt__date_retour_prevue__lt=timezone.now()
        ).distinct()

        if format_rapport == 'pdf':
            return generate_adherents_pdf(membres_actifs, membres_inactifs, utilisateurs_en_retard)
        elif format_rapport == 'excel':
            return generate_adherents_excel(membres_actifs, membres_inactifs, utilisateurs_en_retard)

    return render(request, 'rapports/adherents.html')
    if request.method == 'POST':
        format_rapport = request.POST.get('format')

        # Récupérer les données des adhérents
        membres_actifs = Lecteur.objects.filter(emprunt__date_emprunt__gte=timezone.now() - timezone.timedelta(days=365)).distinct()
        utilisateurs_en_retard = Lecteur.objects.filter(
            emprunt__returned=False,
            emprunt__date_retour_prevue__lt=timezone.now()
        ).distinct()

        if format_rapport == 'pdf':
            return generate_adherents_pdf(membres_actifs, utilisateurs_en_retard)
        elif format_rapport == 'excel':
            return generate_adherents_excel(membres_actifs, utilisateurs_en_retard)

    return render(request, 'rapports/adherents.html')


def generate_adherents_pdf(membres_actifs, membres_inactifs, utilisateurs_en_retard):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Rapport des Adhérents")

    # Ajouter un titre
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Rapport des Adhérents")

    # Membres actifs
    y = 700
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Membres Actifs")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for membre in membres_actifs:
        pdf.drawString(50, y, f"{membre.nom} - {membre.email}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    # Membres inactifs
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Membres Inactifs")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for membre in membres_inactifs:
        pdf.drawString(50, y, f"{membre.nom} - {membre.email}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    # Utilisateurs en retard
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Utilisateurs en Retard")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for utilisateur in utilisateurs_en_retard:
        pdf.drawString(50, y, f"{utilisateur.nom} - {utilisateur.email}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_adherents.pdf"'
    return response
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Rapport des Adhérents")

    # Ajouter un titre
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Rapport des Adhérents")

    # Membres actifs
    y = 700
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Membres Actifs")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for membre in membres_actifs:
        pdf.drawString(50, y, f"{membre.nom} - {membre.email}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    # Utilisateurs en retard
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Utilisateurs en Retard")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for utilisateur in utilisateurs_en_retard:
        pdf.drawString(50, y, f"{utilisateur.nom} - {utilisateur.email}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_adherents.pdf"'
    return response


def generate_adherents_excel(membres_actifs, membres_inactifs, utilisateurs_en_retard):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Rapport des Adhérents")

    # Ajouter les colonnes
    worksheet.write(0, 0, "Nom")
    worksheet.write(0, 1, "Email")
    worksheet.write(0, 2, "Statut")

    row = 1
    for membre in membres_actifs:
        worksheet.write(row, 0, membre.nom)
        worksheet.write(row, 1, membre.email)
        worksheet.write(row, 2, "Actif")
        row += 1

    for membre in membres_inactifs:
        worksheet.write(row, 0, membre.nom)
        worksheet.write(row, 1, membre.email)
        worksheet.write(row, 2, "Inactif")
        row += 1

    for utilisateur in utilisateurs_en_retard:
        worksheet.write(row, 0, utilisateur.nom)
        worksheet.write(row, 1, utilisateur.email)
        worksheet.write(row, 2, "En retard")
        row += 1

    workbook.close()
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rapport_adherents.xlsx"'
    return response
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Rapport des Adhérents")

    # Ajouter les colonnes
    worksheet.write(0, 0, "Nom")
    worksheet.write(0, 1, "Email")
    worksheet.write(0, 2, "Statut")

    row = 1
    for membre in membres_actifs:
        worksheet.write(row, 0, membre.nom)
        worksheet.write(row, 1, membre.email)
        worksheet.write(row, 2, "Actif")
        row += 1

    for utilisateur in utilisateurs_en_retard:
        worksheet.write(row, 0, utilisateur.nom)
        worksheet.write(row, 1, utilisateur.email)
        worksheet.write(row, 2, "En retard")
        row += 1

    workbook.close()
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rapport_adherents.xlsx"'
    return response
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Rapport des Adhérents")

    # Ajouter un titre
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Rapport des Adhérents")

    # Membres actifs
    y = 700
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Membres Actifs")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for membre in membres_actifs:
        pdf.drawString(50, y, f"{membre.nom} {membre.prenom} - {membre.email}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    # Utilisateurs en retard
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Utilisateurs en Retard")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for utilisateur in utilisateurs_en_retard:
        pdf.drawString(50, y, f"{utilisateur.nom} {utilisateur.prenom} - {utilisateur.email}")
        y -= 15
        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_adherents.pdf"'
    return response


 
def rapport_activite(request):
    if request.method == 'POST':
        format_rapport = request.POST.get('format')
        periode = request.POST.get('periode')  # 'mensuel' ou 'annuel'

        # Récupérer les données des emprunts
        if periode == 'mensuel':
            emprunts = Emprunt.objects.annotate(
                mois=ExtractMonth('date_emprunt')
            ).values('mois').annotate(total=Count('id')).order_by('mois')
        elif periode == 'annuel':
            emprunts = Emprunt.objects.annotate(
                annee=ExtractYear('date_emprunt')
            ).values('annee').annotate(total=Count('id')).order_by('annee')

        if format_rapport == 'pdf':
            return generate_activity_pdf(emprunts, periode)
        elif format_rapport == 'excel':
            return generate_activity_excel(emprunts, periode)

    return render(request, 'rapports/activite.html')

def generate_activity_pdf(emprunts, periode):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Rapport d'Activité")

    # Ajouter un titre
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Rapport d'Activité")

    # Ajouter les colonnes
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Période")
    pdf.drawString(200, 700, "Nombre d'Emprunts")

    # Ajouter les données
    y = 680
    pdf.setFont("Helvetica", 10)
    for emprunt in emprunts:
        periode_label = emprunt['mois'] if 'mois' in emprunt else emprunt['annee']
        pdf.drawString(50, y, str(periode_label))
        pdf.drawString(200, y, str(emprunt['total']))
        y -= 20

        if y < 50:  # Ajouter une nouvelle page si nécessaire
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = 750

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_activite.pdf"'
    return response


def generate_activity_excel(emprunts, periode):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Rapport d'Activité")

    # Ajouter les colonnes
    worksheet.write(0, 0, "Période")
    worksheet.write(0, 1, "Nombre d'Emprunts")

    # Ajouter les données
    row = 1
    for emprunt in emprunts:
        periode_label = emprunt['mois'] if 'mois' in emprunt else emprunt['annee']
        worksheet.write(row, 0, periode_label)
        worksheet.write(row, 1, emprunt['total'])
        row += 1

    workbook.close()
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rapport_activite.xlsx"'
    return response

# ================================================
def rapport_financier(request):
    if request.method == 'POST':
        format_rapport = request.POST.get('format')

        # Récupérer les données des amendes impayées
        amendes = Amende.objects.filter(statut=False)
        print(f"Nombre d'amendes récupérées : {amendes.count()}")
        for amende in amendes:
            print(f"Lecteur : {amende.emprunt.lecteur.nom}, Livre : {amende.emprunt.livre.titre}, Montant : {amende.montant}")

        if format_rapport == 'pdf':
            return generate_pdf(amendes)

    return render(request, 'rapports/financier.html')
def generate_pdf(amendes):
    # Création du buffer et du PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Rapport Financier - Amendes Impayées")

    # Variables globales pour la mise en page
    page_width, page_height = letter
    margin = 50
    line_height = 20

    def draw_header():
        # Titre du rapport
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(margin, page_height - margin, "Rapport Financier - Amendes Impayées")
        
        # En-têtes des colonnes
        y = page_height - margin - 40
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, y, "Nom Lecteur")
        pdf.drawString(margin + 200, y, "Livre")
        pdf.drawString(margin + 400, y, "Montant (€)")
        return y - line_height

    # Position initiale
    y = draw_header()
    total_amendes = 0

    # Boucle sur les amendes
    for amende in amendes:
        try:
            # Nouvelle page si nécessaire
            if y < margin + line_height:
                pdf.showPage()
                y = draw_header()

            # Écriture des données
            pdf.setFont("Helvetica", 10)
            pdf.drawString(margin, y, str(amende.emprunt.lecteur.nom)[:30])
            pdf.drawString(margin + 200, y, str(amende.emprunt.livre.titre)[:30])
            pdf.drawString(margin + 400, y, f"{amende.montant:.2f} €")

            total_amendes += amende.montant
            y -= line_height

        except Exception as e:
            print(f"Erreur avec l'amende {amende.id}: {str(e)}")

    # Ajout du total
    if y < margin + 40:  # S'il ne reste pas assez de place pour le total
        pdf.showPage()
        y = page_height - margin - 40

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y - 20, "Total des amendes impayées:")
    pdf.drawString(margin + 400, y - 20, f"{total_amendes:.2f} €")

    # Finalisation du PDF
    pdf.save()
    buffer.seek(0)
    
    # Retour de la réponse
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_financier.pdf"'
    return response