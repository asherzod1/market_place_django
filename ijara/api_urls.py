from rest_framework.routers import DefaultRouter, SimpleRouter

from announcement.views import TransportViewSet, AnnouncementViewSet, SelfAnnouncementViewSet
from ijara import settings
from images.views import ImageViewSet
from users.views import UserViewSet, UserCreateView, UserLoginView

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet, basename="users")
router.register("transport", TransportViewSet, basename="transports")
router.register("announcement", AnnouncementViewSet, basename="announcements")
router.register("my-announcement", SelfAnnouncementViewSet, basename="my_announcements")
router.register("images", ImageViewSet, basename="image")

urlpatterns = router.urls