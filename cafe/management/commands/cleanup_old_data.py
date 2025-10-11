from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from cafe.models import order, bill  # use lowercase as per your models

class Command(BaseCommand):
    help = "Deletes cafe data older than 48 hours"

    def handle(self, *args, **kwargs):
        time_threshold = timezone.now() - timedelta(hours=48)

        # Use actual field names from your models
        order.objects.filter(order_time__lt=time_threshold).delete()
        bill.objects.filter(bill_time__lt=time_threshold).delete()  # change field name as per your model

        self.stdout.write(self.style.SUCCESS("✅ Deleted old order and bill records older than 48 hours"))
