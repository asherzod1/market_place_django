import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()


class JwtAuthMiddleware(BaseMiddleware):

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope['query_string'].decode('utf8'))
        token = query_string.get('token', [None])[0]
        if token:
            try:
                decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user = await self.get_user(decoded_data['user_id'])
                scope['user'] = user if user else None
            except jwt.ExpiredSignatureError:
                scope['user'] = None
            except jwt.DecodeError:
                scope['user'] = None
            except Exception as e:
                scope['user'] = None
                print(f"JWT decode error: {e}")
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))
