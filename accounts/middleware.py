from django.shortcuts import redirect
from django.urls import reverse


class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and not request.user.is_authenticated and not request.path.startswith('/accounts/'):
            return redirect(reverse('accounts:login'))

        response = self.get_response(request)
        return response
