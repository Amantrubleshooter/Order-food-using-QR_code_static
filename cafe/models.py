from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager
from django.db.models import Avg

class User(AbstractUser):
    email = None
    username = None
    phone = models.CharField(max_length=10, unique=True)
    phone_verified = models.BooleanField(default=False)
    cafe_manager = models.BooleanField(default=False)
    order_count = models.IntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'cafe_user'


class menu_item(models.Model):
    # Remove item_id = models.AutoField - MongoDB uses _id automatically
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, default='')
    desc = models.CharField(max_length=250)
    pic = models.CharField(max_length=200, default='menu_items/default.jpg')
    price = models.CharField(max_length=4, default='0')
    list_order = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        """Calculate average rating for this item"""
        avg = self.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg) if avg else 0
    
    @property
    def rating_count(self):
        """Count total ratings for this item"""
        return self.ratings.count()


class rating(models.Model):
    name = models.CharField(max_length=30)
    comment = models.CharField(max_length=250)
    r_date = models.DateField()

    def __str__(self):
        return f"{self.name}'s review"


class order(models.Model):
    # MongoDB will use _id, but we can keep order_id for compatibility
    order_id = models.AutoField(primary_key=True)
    items_json = models.TextField()  # Changed from CharField for larger data
    name = models.CharField(max_length=30, default='')
    phone = models.CharField(max_length=10, default='')
    table = models.CharField(max_length=15, default='take away')
    price = models.CharField(max_length=5, default='0')
    order_time = models.DateTimeField()
    bill_clear = models.BooleanField(default=False)
    
    special_instructions = models.TextField(blank=True, default='')
    
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('confirmed', 'Confirmed')  # Added for admin orders
    ], default='pending')
    
    payment_status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid')
    ], default='unpaid')
    payment_screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)
    
    def __str__(self):
        return f"Order #{self.order_id} - {self.name}"


class bill(models.Model):
    order_items = models.TextField()  # Changed from CharField
    name = models.CharField(default='', max_length=50)
    bill_total = models.IntegerField()
    phone = models.CharField(max_length=10)
    bill_time = models.DateTimeField()


class Table(models.Model):
    table_number = models.CharField(max_length=10, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_occupied = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Table {self.table_number}"


class ItemRating(models.Model):
    menu_item = models.ForeignKey(menu_item, on_delete=models.CASCADE, related_name='ratings')
    order = models.ForeignKey(order, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=10, blank=True)
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['order', 'menu_item']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.rating}⭐"