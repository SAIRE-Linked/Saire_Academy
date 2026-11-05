from django.utils.cache import patch_vary_headers


class PrivateLearningResponses:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(('/api/v1/', '/accounts/')):
            response['Cache-Control'] = 'private, no-store'
            patch_vary_headers(response, ['Cookie', 'Authorization'])
        return response
