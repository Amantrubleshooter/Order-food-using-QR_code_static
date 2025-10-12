from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser with phone number'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get credentials from environment variables
        phone = os.environ.get('DJANGO_SUPERUSER_PHONE')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not phone:
            self.stdout.write(self.style.ERROR('❌ DJANGO_SUPERUSER_PHONE not set!'))
            return
        
        if not password:
            self.stdout.write(self.style.ERROR('❌ DJANGO_SUPERUSER_PASSWORD not set!'))
            return
        
        # Check if user already exists
        if User.objects.filter(phone=phone).exists():
            self.stdout.write(self.style.WARNING(f'⚠️ User with phone {phone} already exists'))
            return
        
        try:
            # Create superuser
            user = User.objects.create(
                phone=phone,
                phone_verified=True,
                cafe_manager=True,
                order_count=0,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            # Set password
            user.set_password(password)
    
            
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser created successfully!'))
            self.stdout.write(self.style.SUCCESS(f'   Phone: {phone}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))