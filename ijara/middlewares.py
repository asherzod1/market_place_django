import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from urllib.parse import parse_qs

from django.conf import settings



@database_sync_to_async
def get_user(user_id):
    from django.contrib.auth.models import AnonymousUser
    from users.models import User

    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


def get_anonymous_user():
    from django.contrib.auth.models import AnonymousUser
    return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope['query_string'].decode('utf8'))
        token = query_string.get('token', [None])[0]
        if token:
            try:
                decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user = await get_user(decoded_data['user_id'])
                scope['user'] = user if user else {}
            except jwt.ExpiredSignatureError:
                scope['user'] = get_anonymous_user()
            except jwt.DecodeError:
                scope['user'] = get_anonymous_user()
            except Exception as e:
                scope['user'] = get_anonymous_user()
                print(f"JWT decode error: {e}")
        return await super().__call__(scope, receive, send)



def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))
