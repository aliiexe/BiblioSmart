from biblio_smart.models import Livre

def categories_processor(request):
    categories = Livre.objects.values_list('categorie', flat=True).distinct()
    return {'categories': categories}