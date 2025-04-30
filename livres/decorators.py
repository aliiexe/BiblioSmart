from django.shortcuts import redirect
from django.contrib import messages

def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        utilisateur_id = request.session.get('utilisateur_id')
        if not utilisateur_id:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('connexion')  # Redirect to your custom login page
        return view_func(request, *args, **kwargs)
    return wrapper