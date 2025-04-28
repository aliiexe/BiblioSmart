from django import forms
from .models import Livre

class BookForm(forms.ModelForm):
    class Meta:
        model = Livre
        fields = ['titre', 'auteur', 'ISBN', 'categorie', 'image', 'disponibilite', "description"] 
        
    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        # Make all fields not required in the form since we handle validation in the template
        for field in self.fields:
            self.fields[field].required = False
            
    def clean(self):
        cleaned_data = super().clean()
        # Required fields validation
        required_fields = ['titre', 'auteur', 'ISBN', 'categorie']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')
        
        return cleaned_data