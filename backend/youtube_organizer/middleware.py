# Middleware to support JWT in HttpOnly cookies for DRF SimpleJWT
# If 'access_token' cookie is present, set the Authorization header for DRF SimpleJWT.

class JWTAuthCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.COOKIES.get('access_token')
        if token and 'HTTP_AUTHORIZATION' not in request.META:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.get_response(request)
