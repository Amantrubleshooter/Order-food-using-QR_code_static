from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib import messages
from cafe.models import *
from django.core.files.storage import FileSystemStorage
from datetime import date, datetime, timedelta
import json, ast
from itertools import groupby
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils import timezone
from itertools import groupby
import os
import json
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, timedelta


User = get_user_model()

# ==================== CORE VIEWS ====================

def menu(request):
    context = {}
    table_number = request.GET.get('table')
    
    if table_number and table_number != 'take away':
        try:
            table = Table.objects.get(table_number=table_number)
            table.is_occupied = True
            table.save()
            request.session['table_number'] = table_number
            
            if not table.qr_code:
                messages.warning(request, f'Table {table_number} exists but QR code is not generated. Please contact staff.')
                
        except Table.DoesNotExist:
            messages.error(request, f'Table {table_number} does not exist. Please scan a valid QR code.')
            return redirect('/')

    menu_items = menu_item.objects.all().order_by('list_order')
    items_by_category = {}

    for key, group in groupby(menu_items, key=lambda x: x.category):
        items_by_category[key] = list(group)

    context = {
        'items_by_category': items_by_category,
        'table_number': table_number
    }

    return render(request, 'menu.html', context)


from datetime import date, datetime, timedelta

def all_orders(request):
    """Owner view - all orders sorted by ID with daily numbering"""
    from datetime import timedelta, datetime
    from django.utils import timezone
    import pytz
    
    if not request.user.is_superuser:
        messages.error(request, 'Only admin users can access this page!')
        return redirect('menu')
    
    # Get current IST time
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = timezone.now().astimezone(ist)
    today = now_ist.date()
    yesterday = today - timedelta(days=1)
    
    # Create IST date boundaries
    today_start = ist.localize(datetime.combine(today, datetime.min.time()))
    today_end = ist.localize(datetime.combine(today, datetime.max.time()))
    
    yesterday_start = ist.localize(datetime.combine(yesterday, datetime.min.time()))
    yesterday_end = ist.localize(datetime.combine(yesterday, datetime.max.time()))
    
    # Get orders for today (comparing with IST boundaries)
    today_orders_raw = order.objects.filter(
        order_time__gte=today_start,
        order_time__lte=today_end
    ).order_by('order_time')
    
    yesterday_orders_raw = order.objects.filter(
        order_time__gte=yesterday_start,
        order_time__lte=yesterday_end
    ).order_by('order_time')
    
    # Process today's orders
    today_orders = list(today_orders_raw)
    for idx, o in enumerate(today_orders, start=1):
        o.daily_order_number = idx
        # Convert to IST (not adding 5:30, just converting timezone)
        o.ist_time = o.order_time.astimezone(ist)
        try:
            o.items_json = json.loads(o.items_json)
        except:
            o.items_json = {}
    
    # Process yesterday's orders
    yesterday_orders = list(yesterday_orders_raw)
    for idx, o in enumerate(yesterday_orders, start=1):
        o.daily_order_number = idx
        o.ist_time = o.order_time.astimezone(ist)
        try:
            o.items_json = json.loads(o.items_json)
        except:
            o.items_json = {}
    
    # Reverse for display
    today_orders.reverse()
    yesterday_orders.reverse()
    
    # Calculate earnings
    today_earnings = sum(float(o.price) if o.price else 0 for o in today_orders)
    yesterday_earnings = sum(float(o.price) if o.price else 0 for o in yesterday_orders)
    
    context = {
        'today_orders': today_orders,
        'today_count': len(today_orders),
        'today_earnings': today_earnings,
        'today_date': today,
        
        'yesterday_orders': yesterday_orders,
        'yesterday_count': len(yesterday_orders),
        'yesterday_earnings': yesterday_earnings,
        'yesterday_date': yesterday,
    }
    
    return render(request, 'all_orders.html', context)


def offers(request):
    return render(request, 'offers.html')


def reviews(request):
    if request.method == 'POST':
        fname = request.user.first_name
        lname = request.user.last_name
        cmt = request.POST.get('comment')
        date_today = date.today()

        review = rating(name=fname + ' ' + lname,
                        comment=cmt,
                        r_date=date_today)
        review.save()

    all_reviews = rating.objects.all().order_by('-r_date')
    context = {}
    context['reviews'] = all_reviews

    return render(request, 'reviews.html', context)


def profile(request):
    if request.user.is_anonymous:
        messages.error(request, 'Please Login first!!')
        return redirect('login')
    return render(request, 'profile.html')


# def manage_menu(request):
#     if request.method == 'POST' and request.FILES['img']:
#         if (request.user.is_anonymous):
#             messages.error(request, 'Please Login to continue!')
#             return redirect('login')
#         if not ((request.user.is_superuser) or (request.user.cafe_manager)):
#             messages.error(request, 'Only Staff members are allowed!')
#             return redirect('menu')
#         else:
#             name = request.POST.get('name')
#             price = request.POST.get('price')
#             desc = request.POST.get('desc')
#             cat = request.POST.get('cat')
#             img = request.FILES['img']
#             listing_order = 0
#             if cat.lower() == 'pizza':
#                 listing_order = 1
#             elif cat.lower() == 'momos':
#                 listing_order = 2
#             elif cat.lower() == 'sandwich':
#                 listing_order = 3
#             elif cat.lower() == 'manchurian':
#                 listing_order = 4
#             elif cat.lower() == 'french fries':
#                 listing_order = 5
#             elif cat.lower() == 'noodles':
#                 listing_order = 6
#             elif cat.lower() == 'combo':
#                 listing_order = 7
#             elif cat.lower() == 'beverage':
#                 listing_order = 8


#             dish = menu_item(name=name,
#                              price=price,
#                              desc=desc,
#                              category=cat.lower(),
#                              pic=img,
#                              list_order=listing_order)
#             dish.save()
#             messages.success(request, 'Dish added successfully!')
#             return redirect('menu')

#     return render(request, 'manage_menu.html')

def manage_menu(request):
              # Dictionary mapping categories to static images
    category_images = {
        'pizza': 'menu_images/pizza.jpg',
        'momos': 'menu_images/momos.jpg',
        'sandwich': 'menu_images/sandwich.jpg',
        'manchurian': 'menu_images/manchurian.jpg',
        'french fries': 'menu_images/french-fries.jpg',
        'noodles': 'menu_images/noodles.jpg',
        'combo': 'menu_images/combo.jpg',
        'beverage': 'menu_images/beverage.jpg',
    }
    
    if request.method == 'POST':
        if request.user.is_anonymous:
            messages.error(request, 'Please Login to continue!')
            return redirect('login')
        if not ((request.user.is_superuser) or (request.user.cafe_manager)):
            messages.error(request, 'Only Staff members are allowed!')
            return redirect('menu')
        else:
            name = request.POST.get('name')
            price = request.POST.get('price')
            desc = request.POST.get('desc')
            cat = request.POST.get('cat')
            selected_img = request.POST.get('selected_img')  # Get selected image
            listing_order = 0
            if cat.lower() == 'pizza':
                listing_order = 1
            elif cat.lower() == 'momos':
                listing_order = 2
            elif cat.lower() == 'sandwich':
                listing_order = 3
            elif cat.lower() == 'manchurian':
                listing_order = 4
            elif cat.lower() == 'french fries':
                listing_order = 5
            elif cat.lower() == 'noodles':
                listing_order = 6
            elif cat.lower() == 'combo':
                listing_order = 7
            elif cat.lower() == 'beverage':
                listing_order = 8
            # Use selected image or default to category image
            img_path = selected_img if selected_img else category_images.get(cat, 'menu_images/default.jpg')
            dish = menu_item(
                name=name,
                price=price,
                desc=desc,
                category=cat.lower(),
                pic=img_path,  # Save the static image path
                list_order=listing_order
            )
            dish.save()
            messages.success(request, 'Dish added successfully!')
            return redirect('menu')  
        # Pass category_images to template
    return render(request, 'manage_menu.html', {'category_images': category_images})
def delete_dish(request, item_id):
    dish = get_object_or_404(menu_item, id=item_id)
    if request.user.is_superuser:
        if request.method == 'POST':
            dish.delete()
            messages.success(request, 'Dish removed successfully!')
            return redirect('menu')
    else:
        messages.error(request, 'Only admins are allowed!')
        return redirect('menu')


def cart(request):
    """Place order with correct timezone"""
    if request.method == 'POST':
        if request.user.is_anonymous:
            name = request.POST.get('name', 'Guest')
            phone = request.POST.get('phone', 'Unknown')
        else:
            name = request.user.first_name + ' ' + request.user.last_name
            phone = request.user.phone
            
        items_json = request.POST.get('items_json')
        table_number = request.POST.get('table_value') or request.session.get('table_number', 'take away')
        total = request.POST.get('price')
        special_instructions = request.POST.get('special_instructions', '')

        if table_number and table_number != 'take away':
            try:
                table = Table.objects.get(table_number=table_number)
                if not table.qr_code:
                    messages.error(request, f'Cannot place order for Table {table_number}.')
                    return redirect('/')
            except Table.DoesNotExist:
                messages.error(request, f'Table {table_number} does not exist.')
                return redirect('/')

        # Use timezone-aware datetime
        now_ist = timezone.now()

        if table_number == 'null' or not table_number:
            table_number = 'take away'

        new_order = order(
            name=name,
            phone=phone,
            items_json=items_json,
            table=table_number,
            order_time=now_ist,  # Use timezone-aware time
            price=total,
            special_instructions=special_instructions
        )
        new_order.save()

        request.session['last_order_id'] = new_order.order_id

        if request.user.is_anonymous:
            messages.success(request, 'Order Placed!! Thanks for ordering.')
            if 'table_number' in request.session:
                del request.session['table_number']
            return redirect('order_confirmation', order_id=new_order.order_id)
        else:
            usr = User.objects.get(phone=phone)
            usr.order_count += 1
            usr.save()
            messages.success(request, 'Order Placed!! Thanks for ordering')
            return redirect('order_confirmation', order_id=new_order.order_id)

    return render(request, 'cart.html')


# NEW: Order confirmation with rating
def order_confirmation(request, order_id):
    """Show order confirmation with rating form"""
    order_obj = get_object_or_404(order, order_id=order_id)
    
    # Parse items JSON
    try:
        items_dict = json.loads(order_obj.items_json)
        # Convert to list of items for template
        order_items = []
        for item_key, item_data in items_dict.items():
            quantity, name, price = item_data
            menu_item_id = int(item_key.replace('pr', ''))
            try:
                item_obj = menu_item.objects.get(id=menu_item_id)
                order_items.append({
                    'menu_item': item_obj,
                    'quantity': quantity,
                    'subtotal': price * quantity
                })
            except menu_item.DoesNotExist:
                continue
    except:
        order_items = []
    
    context = {
        'order': order_obj,
        'order_items': order_items
    }
    return render(request, 'order_confirmation.html', context)


# NEW: Submit ratings
def submit_ratings(request, order_id):
    """Submit ratings for order items"""
    if request.method == 'POST':
        order_obj = get_object_or_404(order, order_id=order_id)
        
        # Get customer info
        customer_name = order_obj.name
        customer_phone = order_obj.phone
        
        # Parse order items
        try:
            items_dict = json.loads(order_obj.items_json)
            
            for item_key, item_data in items_dict.items():
                menu_item_id = int(item_key.replace('pr', ''))
                
                rating_key = f'rating_{menu_item_id}'
                review_key = f'review_{menu_item_id}'
                
                rating_value = request.POST.get(rating_key)
                review_text = request.POST.get(review_key, '')
                
                if rating_value:
                    try:
                        item_obj = menu_item.objects.get(id=menu_item_id)
                        
                        # Create or update rating
                        ItemRating.objects.update_or_create(
                            order=order_obj,
                            menu_item=item_obj,
                            defaults={
                                'rating': int(rating_value),
                                'review': review_text,
                                'customer_name': customer_name,
                                'customer_phone': customer_phone
                            }
                        )
                    except menu_item.DoesNotExist:
                        continue
        except:
            pass
        
        messages.success(request, 'Thank you for your ratings!')
        return redirect('menu')
    
    return redirect('order_confirmation', order_id=order_id)


def my_orders(request):
    phone = request.user.phone

    context = {}
    orders = order.objects.filter(phone=phone)
    order_by_table = {}

    for key, group in groupby(orders, key=lambda x: x.table):
        order_by_table[key] = list(group)
    for table, orders in order_by_table.items():
        for ord in orders:
            items_json_str = ord.items_json
            ord.items_json = json.loads(items_json_str)

    context = {'order_by_table': order_by_table}

    return render(request, 'my_orders.html', context)


def Login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(phone=phone, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully !')
            return redirect('profile')

        else:
            messages.error(request, 'Login failed, Invalid Credentials!')
            return redirect('login')

    return render(request, 'login.html')


def Logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully !')
    return redirect('login')


def signup(request):
    if request.method == "POST":
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        phone = request.POST.get('number')
        pass_word = request.POST.get('password')
        c_pass_word = request.POST.get('cpassword')

        if User.objects.filter(phone=phone).exists():
            messages.error(
                request,
                'Mobile number already regestired. Please Login to continue')
            return redirect('login')

        my_user = User.objects.create_user(phone=phone, password=pass_word)
        my_user.first_name = fname
        my_user.last_name = lname
        my_user.save()
        messages.success(request, 'User created successfully !!')

        return redirect('login')

    return render(request, 'signup.html')


def generate_bill(request):
    t_number = request.GET.get('table')
    order_for_table = order.objects.filter(table=t_number, bill_clear=False)
    total_bill = 0
    now = datetime.now()

    bill_items = []
    c_name = ''
    c_phone = ''
    
    # Get shop details from static files
    def read_static_file(filename):
        try:
            file_path = os.path.join(settings.BASE_DIR, 'static', 'bill_var', filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return "Not Available"

    shop_name = read_static_file('shop_name.txt')
    gst_number = read_static_file('gst_number.txt')
    shop_address = read_static_file('shop_address.txt')

    # Generate QR Code
    website_url = "https://order-food-using-qr-code-static.onrender.com/"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(website_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    for o in order_for_table:
        try:
            total_bill += int(o.price) if o.price else 0
            o.bill_clear = True
            o.save()
            
            bill_items.append({
                'order_items': o.items_json,
                'special_instructions': o.special_instructions
            })
        except (ValueError, TypeError) as e:
            print(f"Error processing order {o.order_id}: Invalid price '{o.price}' - {e}")
            continue
        c_name = o.name
        c_phone = o.phone

    if t_number and t_number != 'take away':
        try:
            table = Table.objects.get(table_number=t_number)
            table.is_occupied = False
            table.save()
        except Table.DoesNotExist:
            pass

    # Process order items - FIXED VERSION
    order_dict = {}
    all_items = []
    
    for item in bill_items:
        order_data = item['order_items']
        
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                continue
        
        if isinstance(order_data, dict):
            for pr_key, pr_value in order_data.items():
                try:
                    # Use original item name (don't convert to lowercase to avoid grouping different items)
                    item_name = str(pr_value[1])
                    quantity = int(pr_value[0])
                    price_per_item = float(pr_value[2])
                    total_price = quantity * price_per_item
                    
                    # Don't group items - show each item separately
                    order_dict[f"{item_name}_{pr_key}"] = [quantity, total_price, price_per_item]
                    
                    all_items.append({
                        'name': item_name,
                        'quantity': quantity,
                        'price_per_item': price_per_item,
                        'total_price': total_price
                    })
                    
                except (IndexError, ValueError, TypeError) as e:
                    print(f"Error processing item {pr_key}: {e}")
                    continue

    # Save to bill model
    new_bill = bill(
        order_items=json.dumps(order_dict),
        name=c_name,
        bill_total=total_bill,
        phone=c_phone,
        bill_time=now
    )
    new_bill.save()

    context = {
        'order_dict': order_dict,
        'all_items': all_items,
        'bill_total': total_bill,
        'name': c_name,
        'phone': c_phone,
        'inv_id': new_bill.id,
        'table_number': t_number,
        'current_date': now.strftime('%d-%m-%Y'),
        'current_time': now.strftime('%I:%M %p'),
        'shop_name': shop_name,
        'gst_number': gst_number,
        'shop_address': shop_address,
        'qr_code': qr_base64,
        'website_url': website_url,
        'bill_items': bill_items,
    }

    return render(request, 'generate_bill.html', context)


def view_bills(request):
    if request.user.is_anonymous:
        messages.error(request, 'You Must be an admin user to view this!')
        return redirect('')

    all_bills = bill.objects.all().order_by('-bill_time')

    for b in all_bills:
        b.order_items = ast.literal_eval(b.order_items)

    context = {'bills': all_bills}

    return render(request, 'bills.html', context)


# ==================== TABLE MANAGEMENT VIEWS ====================

def generate_table_qr(request):
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        table, created = Table.objects.get_or_create(table_number=table_number)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr_data = f"http://{request.get_host()}/?table={table.table_number}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        table.qr_code.save(f'qr_table_{table.table_number}.png', File(buffer), save=False)
        table.save()
        
        messages.success(request, f'QR Code generated for Table {table.table_number}!')
        return redirect('table_list')
    
    return render(request, 'generate_qr.html')

def table_list(request):
    tables = Table.objects.all()
    return render(request, 'table_list.html', {'tables': tables})

def admin_orders(request):
    """Kitchen view - all orders sorted by ID with daily numbering"""
    from datetime import timedelta, datetime
    from django.utils import timezone
    import pytz
    
    # Get current IST time
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = timezone.now().astimezone(ist)
    today = now_ist.date()
    
    # IST date boundaries
    today_start = ist.localize(datetime.combine(today, datetime.min.time()))
    today_end = ist.localize(datetime.combine(today, datetime.max.time()))
    
    # Get all orders for today
    all_today_orders = order.objects.filter(
        order_time__gte=today_start,
        order_time__lte=today_end
    ).order_by('order_time')
    
    # Add daily order number
    all_orders_list = list(all_today_orders)
    for idx, o in enumerate(all_orders_list, start=1):
        o.daily_order_number = idx
    
    # Filter for active orders
    active_orders = [o for o in all_orders_list if o.status in ['pending', 'preparing', 'ready']]
    active_orders.reverse()
    
    # Add IST time
    for order_obj in active_orders:
        order_obj.ist_time = order_obj.order_time.astimezone(ist)
        try:
            order_obj.items_dict = json.loads(order_obj.items_json)
        except:
            order_obj.items_dict = {}
    
    context = {'orders': active_orders}
    return render(request, 'admin_orders.html', context)

@csrf_exempt
def update_order_status(request, order_id):
    """Update order status and redirect back to same page"""
    if request.method == 'POST':
        status = request.POST.get('status')
        try:
            order_obj = order.objects.get(order_id=order_id)
            order_obj.status = status
            order_obj.save()
            
            # If completed, mark table as available
            if status == 'completed' and order_obj.table != 'take away':
                try:
                    table = Table.objects.get(table_number=order_obj.table)
                    other_pending = order.objects.filter(
                        table=order_obj.table, 
                        status__in=['pending', 'preparing', 'ready']
                    ).exclude(order_id=order_id).exists()
                    
                    if not other_pending:
                        table.is_occupied = False
                        table.save()
                        messages.success(request, f'Order #{order_id} completed! Table {order_obj.table} is now available.')
                    else:
                        messages.success(request, f'Order #{order_id} marked as {status}!')
                except Table.DoesNotExist:
                    messages.success(request, f'Order #{order_id} marked as {status}!')
            else:
                messages.success(request, f'Order #{order_id} marked as {status}!')
            
        except order.DoesNotExist:
            messages.error(request, 'Order not found!')
    
    # Redirect back to referring page (stay on same page)
    return redirect(request.META.get('HTTP_REFERER', 'admin_orders'))

def table_management(request):
    """View for managing all tables and their status"""
    tables = Table.objects.all().order_by('table_number')
    
    for table in tables:
        table.pending_orders = order.objects.filter(
            table=table.table_number, 
            status__in=['pending', 'preparing']
        ).count()
        
        total_tables = tables.count()
        available_tables = tables.filter(is_occupied=False).count()
        occupied_tables = tables.filter(is_occupied=True).count()
        qr_generated_tables = tables.filter(qr_code__isnull=False).count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_table':
            table_number = request.POST.get('table_number')
            if table_number and not Table.objects.filter(table_number=table_number).exists():
                Table.objects.create(table_number=table_number)
                messages.success(request, f'Table {table_number} created successfully!')
                return redirect('table_management')
            else:
                messages.error(request, 'Table number already exists or is invalid!')
                
        elif action == 'delete_table':
            table_id = request.POST.get('table_id')
            try:
                table = Table.objects.get(id=table_id)
                table_number = table.table_number
                table.delete()
                messages.success(request, f'Table {table_number} deleted successfully!')
                return redirect('table_management')
            except Table.DoesNotExist:
                messages.error(request, 'Table not found!')
    
    context = {
        'tables': tables,
        'total_tables': total_tables,
        'available_tables': available_tables,
        'occupied_tables': occupied_tables,
        'qr_generated_tables': qr_generated_tables,
    }
    return render(request, 'table_management.html', context)

# Add this function at the end
def upload_payment(request, order_id):
    """Upload payment screenshot"""
    if request.method == 'POST' and request.FILES.get('payment_screenshot'):
        order_obj = get_object_or_404(order, order_id=order_id)
        
        # Save payment screenshot
        order_obj.payment_screenshot = request.FILES['payment_screenshot']
        order_obj.save()
        
        messages.success(request, 'Payment screenshot uploaded! Waiting for admin confirmation.')
        return redirect('menu')
    
    return redirect('order_confirmation', order_id=order_id)


def mark_payment_paid(request, order_id):
    """Admin marks order as paid"""
    if not request.user.is_superuser:
        messages.error(request, 'Only admin can mark payment as paid!')
        return redirect('menu')
    
    order_obj = get_object_or_404(order, order_id=order_id)
    order_obj.payment_status = 'paid'
    order_obj.save()
    
    messages.success(request, f'Order #{order_id} marked as PAID!')
    return redirect('all_orders')