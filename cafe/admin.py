from django.contrib import admin
from cafe.models import User, menu_item, rating, order, bill, Table, ItemRating
from django.utils.html import format_html

# Register your models here.

admin.site.register(User)
admin.site.register(menu_item)
admin.site.register(rating)

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'occupancy_status', 'qr_code_status']
    list_filter = ['is_occupied']
    search_fields = ['table_number']
    actions = ['mark_as_available', 'mark_as_occupied']
    
    def occupancy_status(self, obj):
        if obj.is_occupied:
            return format_html('<span style="color: red;">● Occupied</span>')
        return format_html('<span style="color: green;">● Available</span>')
    occupancy_status.short_description = 'Status'
    
    def qr_code_status(self, obj):
        if obj.qr_code:
            return format_html('<span style="color: green;">✓ Generated</span>')
        return format_html('<span style="color: orange;">⚠ Not generated</span>')
    qr_code_status.short_description = 'QR Code'
    
    def mark_as_available(self, request, queryset):
        queryset.update(is_occupied=False)
    mark_as_available.short_description = "Mark selected tables as available"
    
    def mark_as_occupied(self, request, queryset):
        queryset.update(is_occupied=True)
    mark_as_occupied.short_description = "Mark selected tables as occupied"


@admin.register(order)
class OrderAdmin(admin.ModelAdmin):
    # SAFE VERSION - Only basic fields
    list_display = ['order_id', 'table_display', 'customer_name', 'phone', 'total_price', 
                    'status', 'order_status', 'order_time_short', 'bill_status']
    list_filter = ['status', 'table', 'bill_clear', 'order_time']
    search_fields = ['name', 'phone', 'table', 'order_id']
    list_editable = ['status']
    readonly_fields = ['order_time', 'order_id']
    date_hierarchy = 'order_time'
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically build fieldsets based on available fields"""
        basic_fieldsets = [
            ('Order Information', {
                'fields': ('order_id', 'name', 'phone', 'table', 'order_time')
            }),
            ('Items & Price', {
                'fields': ('items_json', 'price')
            }),
            ('Status', {
                'fields': ('status', 'bill_clear')
            }),
        ]
        
        # Check if special_instructions field exists
        if hasattr(obj, 'special_instructions'):
            basic_fieldsets.insert(2, ('Special Instructions', {
                'fields': ('special_instructions',),
                'classes': ('wide',),
            }))
        
        # Check if payment fields exist
        if hasattr(obj, 'payment_status'):
            payment_fields = ['payment_status']
            if hasattr(obj, 'payment_screenshot'):
                payment_fields.extend(['payment_screenshot', 'payment_screenshot_preview'])
            
            basic_fieldsets.insert(-1, ('Payment', {
                'fields': tuple(payment_fields),
                'classes': ('wide',)
            }))
        
        return basic_fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        """Dynamically add readonly fields"""
        readonly = ['order_time', 'order_id']
        if hasattr(obj, 'payment_screenshot') and obj and obj.payment_screenshot:
            readonly.append('payment_screenshot_preview')
        return readonly
    
    def payment_screenshot_preview(self, obj):
        if hasattr(obj, 'payment_screenshot') and obj.payment_screenshot:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 300px; max-height: 300px; border: 2px solid #ddd; border-radius: 8px;"/></a>',
                obj.payment_screenshot.url,
                obj.payment_screenshot.url
            )
        return "No payment screenshot uploaded"
    payment_screenshot_preview.short_description = 'Payment Screenshot'
    
    def table_display(self, obj):
        if obj.table == 'take away' or obj.table == 'Take Away':
            return format_html('<span style="color: blue;">🚶 Take Away</span>')
        return format_html(f'<span style="color: green;">🍽 Table {obj.table}</span>')
    table_display.short_description = 'Table'
    
    def customer_name(self, obj):
        return obj.name if obj.name else "No Name"
    customer_name.short_description = 'Customer'
    
    def total_price(self, obj):
        return f"₹{obj.price}"
    total_price.short_description = 'Total'
    
    def order_status(self, obj):
        status_colors = {
            'pending': 'orange',
            'preparing': 'blue', 
            'ready': 'green',
            'completed': 'gray'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(f'<span style="color: {color}; font-weight: bold;">{obj.status.upper()}</span>')
    order_status.short_description = 'Status'
    
    def order_time_short(self, obj):
        return obj.order_time.strftime("%H:%M")
    order_time_short.short_description = 'Time'
    
    def bill_status(self, obj):
        if obj.bill_clear:
            return format_html('<span style="color: green;">✓ Paid</span>')
        return format_html('<span style="color: red;">● Unpaid</span>')
    bill_status.short_description = 'Bill'


@admin.register(ItemRating)
class ItemRatingAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'rating_stars', 'customer_name', 'customer_phone', 'created_at_short', 'order_link']
    list_filter = ['rating', 'created_at', 'menu_item']
    search_fields = ['menu_item__name', 'customer_name', 'customer_phone', 'review']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(f'<span style="font-size: 1.2em;">{stars}</span>')
    rating_stars.short_description = 'Rating'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime("%b %d, %Y")
    created_at_short.short_description = 'Date'
    
    def order_link(self, obj):
        if obj.order:
            return format_html(
                '<a href="/admin/cafe/order/{}/change/">Order #{}</a>',
                obj.order.order_id,
                obj.order.order_id
            )
        return "N/A"
    order_link.short_description = 'Order'


admin.site.register(bill)