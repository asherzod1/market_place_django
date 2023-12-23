from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with phone number'

    def handle(self, *args, **options):
        phone_number = input("Enter phone number: ")
        password = input("Enter password: ")
        User.objects.create_superuser(phone_number=phone_number, password=password, email=None, is_superuser=True, is_staff=True, is_active=True)
        self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
