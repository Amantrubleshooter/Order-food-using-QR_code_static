
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

import logging
logger = logging.getLogger(__name__)
User = get_user_model()

# ==================== CORE VIEWS ===================
from datetime import date, datetime, timedelta
def menu(request):
    """Menu page with table booking check"""
    context = {}
    table_number = request.GET.get('table')
    
    if table_number and table_number != 'take away':
        try:
            table = Table.objects.get(table_number=table_number)
            
            # CHECK IF TABLE IS ALREADY OCCUPIED
            if table.is_occupied:
                # Check if there are active orders for this table
                try:
                    active_orders = list(order.objects.filter(
                        table=table_number,
                        status__in=['pending', 'preparing', 'ready']
                    ))
                    
                    if active_orders:
                        messages.error(
                            request, 
                            f'❌ Table {table_number} is currently occupied! Please wait or choose another table.'
                        )
                        # Redirect to home or table selection page
                        return redirect('/')
                except Exception as e:
                    logger.error(f"Error checking table orders: {e}")
            
            # If table is available, mark as occupied
            table.is_occupied = True
            table.save()
            request.session['table_number'] = table_number
            
            if not table.qr_code:
                messages.warning(request, f'Table {table_number} exists but QR code is not generated. Please contact staff.')
                
        except Table.DoesNotExist:
            messages.error(request, f'Table {table_number} does not exist. Please scan a valid QR code.')
            return redirect('/')

    # Get menu items
    try:
        menu_items = list(menu_item.objects.all())
        menu_items.sort(key=lambda x: x.list_order)
    except Exception as e:
        logger.error(f"Error fetching menu items: {e}")
        menu_items = []
    
    items_by_category = {}
    for key, group in groupby(menu_items, key=lambda x: x.category):
        items_by_category[key] = list(group)

    context = {
        'items_by_category': items_by_category,
        'table_number': table_number
    }

    return render(request, 'menu.html', context)
def all_orders(request):
    """Owner view - all orders sorted by ID with daily numbering"""
    from datetime import timedelta, datetime
    from django.utils import timezone
    import pytz
    
    if not request.user.is_superuser:
        messages.error(request, 'Only admin users can access this page!')
        return redirect('menu')
    
    try:
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
        
        # Get orders - FIXED: convert to list immediately
        try:
            today_orders_raw = list(order.objects.filter(
                order_time__gte=today_start,
                order_time__lte=today_end
            ))
            today_orders_raw.sort(key=lambda x: x.order_time)
        except Exception as e:
            logger.error(f"Error fetching today orders: {e}")
            today_orders_raw = []
        
        try:
            yesterday_orders_raw = list(order.objects.filter(
                order_time__gte=yesterday_start,
                order_time__lte=yesterday_end
            ))
            yesterday_orders_raw.sort(key=lambda x: x.order_time)
        except Exception as e:
            logger.error(f"Error fetching yesterday orders: {e}")
            yesterday_orders_raw = []
        
        # Process today's orders
        for idx, o in enumerate(today_orders_raw, start=1):
            o.daily_order_number = idx
            o.ist_time = o.order_time.astimezone(ist)
            try:
                o.items_json = json.loads(o.items_json)
            except:
                o.items_json = {}
        
        # Process yesterday's orders
        for idx, o in enumerate(yesterday_orders_raw, start=1):
            o.daily_order_number = idx
            o.ist_time = o.order_time.astimezone(ist)
            try:
                o.items_json = json.loads(o.items_json)
            except:
                o.items_json = {}
        
        # Reverse for display
        today_orders_raw.reverse()
        yesterday_orders_raw.reverse()
        
        # Calculate earnings
        today_earnings = sum(float(o.price) if o.price else 0 for o in today_orders_raw)
        yesterday_earnings = sum(float(o.price) if o.price else 0 for o in yesterday_orders_raw)
        
        context = {
            'today_orders': today_orders_raw,
            'today_count': len(today_orders_raw),
            'today_earnings': today_earnings,
            'today_date': today,
            
            'yesterday_orders': yesterday_orders_raw,
            'yesterday_count': len(yesterday_orders_raw),
            'yesterday_earnings': yesterday_earnings,
            'yesterday_date': yesterday,
        }
        
        return render(request, 'all_orders.html', context)
        
    except Exception as e:
        logger.error(f"Error in all_orders view: {e}")
        messages.error(request, f'Error loading orders: {str(e)}')
        return render(request, 'all_orders.html', {
            'today_orders': [],
            'today_count': 0,
            'today_earnings': 0,
            'yesterday_orders': [],
            'yesterday_count': 0,
            'yesterday_earnings': 0,
        })


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


# COMPLETE GENERATE_BILL - Saves to Database & Shows in Bills Tab
# Replace your generate_bill function with this

def generate_bill(request):
    """Generate bill, save to database, and show in bills tab"""
    
    print("\n" + "="*60)
    print("GENERATE BILL - START")
    print("="*60)
    
    t_number = request.GET.get('table')
    print(f"Step 1: Table number: '{t_number}'")
    
    if not t_number:
        messages.error(request, 'No table number provided')
        return redirect('all_orders')
    
    # FIX: Get ALL orders for table (including already billed ones)
    order_for_table = []
    try:
        print(f"Step 2: Fetching ALL orders for table '{t_number}'...")
        
        # Get all orders for this table with specific statuses
        all_table_orders = order.objects.filter(
            table=t_number,
            # status__in=['ready', 'completed', 'confirmed']  # Only these statuses
        )
        
        # Filter for unpaid orders in Python
        for o in all_table_orders:
            if not o.bill_clear:
                order_for_table.append(o)
                print(f"  Found unpaid order #{o.order_id}: {o.name}, ₹{o.price}")
        
        # If no unpaid orders, check if there are ANY orders for this table
        if not order_for_table:
            all_orders_check = []
            for o in order.objects.filter(table=t_number):
                all_orders_check.append(o)
                print(f"  All orders check - Order #{o.order_id}: bill_clear={o.bill_clear}, status={o.status}")
        
        print(f"Step 3: Total unpaid orders: {len(order_for_table)}")
        
    except Exception as e:
        print(f"ERROR in Step 2/3: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Database error while fetching orders')
        return redirect('all_orders')
    
    # Check if orders exist
    if not order_for_table:
        print(f"Step 4: No unpaid orders for table '{t_number}'")
        messages.warning(request, f'No unpaid orders found for table {t_number}. All orders may already be billed.')
        return redirect('all_orders')
    
    print(f"Step 5: Processing {len(order_for_table)} orders...")
    
    total_bill = 0
    now = datetime.now()
    bill_items = []
    c_name = ''
    c_phone = ''
    bill_order_items = {}  # For saving to bill table
    
    # Shop details
    def read_static_file(filename):
        try:
            file_path = os.path.join(settings.BASE_DIR, 'static', 'bill_var', filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except:
            return "Not Available"

    shop_name = read_static_file('shop_name.txt')
    gst_number = read_static_file('gst_number.txt')
    shop_address = read_static_file('shop_address.txt')

    # QR Code
    try:
        website_url = "https://order-food-using-qr-code-static.onrender.com/"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(website_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    except:
        qr_base64 = ""

    # Process orders
    for idx, o in enumerate(order_for_table, 1):
        try:
            order_price = int(o.price) if o.price else 0
            total_bill += order_price
            
            # Mark as billed
            # o.bill_clear = True
            # o.save()
            
            bill_items.append({
                'order_items': o.items_json,
                'special_instructions': o.special_instructions
            })
            
            c_name = o.name
            c_phone = o.phone
            
            # Collect items for bill table
            try:
                items = json.loads(o.items_json) if isinstance(o.items_json, str) else o.items_json
                for key, value in items.items():
                    item_name = value[1]
                    if item_name in bill_order_items:
                        bill_order_items[item_name][0] += value[0]  # Add quantity
                    else:
                        bill_order_items[item_name] = list(value)  # [qty, name, price]
            except:
                pass
            
            print(f"  Processed order #{o.order_id}: ₹{order_price}")
            
        except Exception as e:
            print(f"  Error processing order #{o.order_id}: {e}")
            continue

    # Release table
    if t_number and t_number != 'take away':
        try:
            table = Table.objects.get(table_number=t_number)
            table.is_occupied = False
            table.save()
            print(f"Step 6: Table {t_number} released")
        except:
            print(f"Step 6: Could not release table")

    # Process items for display
    order_dict = {}
    
    for item in bill_items:
        order_data = item['order_items']
        
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except:
                continue
        
        if isinstance(order_data, dict):
            for pr_key, pr_value in order_data.items():
                try:
                    item_name = str(pr_value[1])
                    item_qty = int(pr_value[0])
                    item_price = int(pr_value[2])
                    item_total = item_qty * item_price
                    
                    if item_name in order_dict:
                        order_dict[item_name]['quantity'] += item_qty
                        order_dict[item_name]['total'] += item_total
                    else:
                        order_dict[item_name] = {
                            'quantity': item_qty,
                            'price': item_price,
                            'total': item_total
                        }
                except:
                    continue

    all_items = []
    for name, details in order_dict.items():
        all_items.append({
            'name': name,
            'quantity': details['quantity'],
            'price': details['price'],
            'total': details['total']
        })

    # Calculate totals
    subtotal = sum(item['total'] for item in all_items)
    cgst = round(subtotal * 0.025, 2)
    sgst = round(subtotal * 0.025, 2)
    grand_total = subtotal + cgst + sgst
    
    print(f"Step 7: Grand Total: ₹{grand_total}")
    
    # IMPORTANT: Save bill to database
    try:
        new_bill = bill(
            order_items=json.dumps(bill_order_items),
            name=c_name,
            bill_total=int(grand_total),
            phone=c_phone,
            bill_time=now
        )
        new_bill.save()
        print(f"Step 8: Bill saved to database (ID: {new_bill.id})")
        messages.success(request, f'✅ Bill generated successfully for {c_name}! Total: ₹{grand_total}')
    except Exception as e:
        print(f"Step 8: Error saving bill: {e}")
        messages.warning(request, 'Bill displayed but could not save to database')
    
    print("="*60)
    print("GENERATE BILL - SUCCESS")
    print("="*60 + "\n")

    context = {
        'bill_items': all_items,
        'c_name': c_name,
        'c_phone': c_phone,
        'table': t_number,
        'subtotal': subtotal,
        'cgst': cgst,
        'sgst': sgst,
        'grand_total': grand_total,
        'bill_time': now,
        'shop_name': shop_name,
        'gst_number': gst_number,
        'shop_address': shop_address,
        'qr_code': qr_base64,
    }

    return render(request, 'bills.html', context)


# ADD THIS NEW FUNCTION for viewing all bills
def view_bills(request):
    """View all generated bills"""
    if not request.user.is_superuser:
        messages.error(request, 'Only admin can view bills!')
        return redirect('menu')
    
    try:
        # Get all bills
        all_bills = []
        for b in bill.objects.all():
            all_bills.append(b)
        
        # Sort by date (newest first)
        all_bills.sort(key=lambda x: x.bill_time, reverse=True)
        
        # Parse items_json for display
        for b in all_bills:
            try:
                if isinstance(b.order_items, str):
                    b.items_dict = json.loads(b.order_items)
                else:
                    b.items_dict = b.order_items
            except:
                b.items_dict = {}
    except Exception as e:
        print(f"Error fetching bills: {e}")
        all_bills = []
        messages.error(request, 'Error loading bills')
    
    context = {
        'bills': all_bills
    }
    
    return render(request, 'view_bills.html', context)



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
    
    try:
        # Get current IST time
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = timezone.now().astimezone(ist)
        today = now_ist.date()
        
        # IST date boundaries
        today_start = ist.localize(datetime.combine(today, datetime.min.time()))
        today_end = ist.localize(datetime.combine(today, datetime.max.time()))
        
        # Get all orders for today - FIXED: Use list() to evaluate query immediately
        try:
            all_today_orders = list(order.objects.filter(
                order_time__gte=today_start,
                order_time__lte=today_end
            ))
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            all_today_orders = []
        
        # Sort in Python instead of database
        all_today_orders.sort(key=lambda x: x.order_time)
        
        # Add daily order number
        for idx, o in enumerate(all_today_orders, start=1):
            o.daily_order_number = idx
        
        # Filter for active orders in Python
        active_orders = [o for o in all_today_orders if o.status in ['pending', 'preparing', 'ready', 'confirmed']]
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
        
    except Exception as e:
        logger.error(f"Error in admin_orders view: {e}")
        messages.error(request, f'Error loading orders: {str(e)}')
        return render(request, 'admin_orders.html', {'orders': []})
def table_management(request):
    """View for managing all tables and their status"""
    try:
        # Get all tables
        all_tables = list(Table.objects.all())
        
        # Sort by table number
        all_tables.sort(key=lambda x: x.table_number)
        
        # Calculate stats for each table
        for table in all_tables:
            try:
                # Get all orders for this table
                table_orders = list(order.objects.filter(table=table.table_number))
                
                # Count active orders (pending, preparing, ready)
                table.pending_orders = sum(
                    1 for o in table_orders 
                    if o.status in ['pending', 'preparing', 'ready']
                )
                
                # Update occupation status based on active orders
                if table.pending_orders > 0:
                    if not table.is_occupied:
                        table.is_occupied = True
                        table.save()
                else:
                    if table.is_occupied:
                        table.is_occupied = False
                        table.save()
                
            except Exception as e:
                logger.error(f"Error processing table {table.table_number}: {e}")
                table.pending_orders = 0
        
        # Calculate overall stats
        total_tables = len(all_tables)
        occupied_tables = sum(1 for t in all_tables if t.is_occupied)
        available_tables = sum(1 for t in all_tables if not t.is_occupied)
        qr_generated_tables = sum(1 for t in all_tables if t.qr_code)
        
    except Exception as e:
        logger.error(f"Error fetching tables: {e}")
        messages.error(request, f'Error loading tables: {str(e)}')
        all_tables = []
        total_tables = available_tables = occupied_tables = qr_generated_tables = 0
    
    # Handle POST requests (create/delete tables)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_table':
            table_number = request.POST.get('table_number')
            if table_number:
                try:
                    # Check if exists
                    existing = list(Table.objects.filter(table_number=table_number))
                    if not existing:
                        Table.objects.create(table_number=table_number)
                        messages.success(request, f'✅ Table {table_number} created successfully!')
                    else:
                        messages.error(request, f'❌ Table {table_number} already exists!')
                except Exception as e:
                    logger.error(f"Error creating table: {e}")
                    messages.error(request, f'Error creating table: {str(e)}')
                return redirect('table_management')
            else:
                messages.error(request, 'Please enter a table number!')
                
        elif action == 'delete_table':
            table_id = request.POST.get('table_id')
            try:
                table = Table.objects.get(id=table_id)
                table_number = table.table_number
                
                # Check if table has active orders
                active_orders = list(order.objects.filter(
                    table=table_number,
                    status__in=['pending', 'preparing', 'ready']
                ))
                
                if active_orders:
                    messages.error(
                        request, 
                        f'Cannot delete Table {table_number}! It has {len(active_orders)} active order(s).'
                    )
                else:
                    table.delete()
                    messages.success(request, f'✅ Table {table_number} deleted successfully!')
                    
                return redirect('table_management')
                
            except Table.DoesNotExist:
                messages.error(request, 'Table not found!')
            except Exception as e:
                logger.error(f"Error deleting table: {e}")
                messages.error(request, f'Error deleting table: {str(e)}')
        
        elif action == 'mark_available':
            table_id = request.POST.get('table_id')
            try:
                table = Table.objects.get(id=table_id)
                
                # Check for active orders
                active_orders = list(order.objects.filter(
                    table=table.table_number,
                    status__in=['pending', 'preparing', 'ready']
                ))
                
                if active_orders:
                    messages.error(
                        request,
                        f'Cannot mark Table {table.table_number} as available! It has {len(active_orders)} active order(s).'
                    )
                else:
                    table.is_occupied = False
                    table.save()
                    messages.success(request, f'✅ Table {table.table_number} marked as available!')
                    
                return redirect('table_management')
                
            except Table.DoesNotExist:
                messages.error(request, 'Table not found!')
            except Exception as e:
                logger.error(f"Error updating table: {e}")
                messages.error(request, f'Error: {str(e)}')
    
    context = {
        'tables': all_tables,
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
# ==================== ADMIN ORDER MANAGEMENT ====================

def admin_place_order(request):
    """Admin creates order for walk-in customers"""
    if not (request.user.is_superuser or request.user.cafe_manager):
        messages.error(request, 'Only staff members can access this!')
        return redirect('menu')
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        table_number = request.POST.get('table_number', 'take away')
        is_takeaway = request.POST.get('is_takeaway') == 'on'
        notes = request.POST.get('notes', '')
        
        if is_takeaway:
            table_number = 'take away'
        
        # Find or create customer
        try:
            customer = User.objects.get(phone=phone)
        except User.DoesNotExist:
            # Create new customer account
            customer = User.objects.create_user(
                phone=phone,
                password=phone
            )
            customer.first_name = first_name
            customer.last_name = last_name
            customer.save()
            messages.info(request, f'New customer account created for {phone}')
        except Exception as e:
            logger.error(f"Error with customer: {e}")
            messages.error(request, 'Error with customer account. Please try again.')
            return redirect('admin_place_order')
        
        # Store order info in session
        request.session['admin_order'] = {
            'customer_phone': customer.phone,
            'customer_name': f"{customer.first_name} {customer.last_name}".strip() or customer.phone,
            'table_number': table_number,
            'notes': notes
        }
        if table_number and table_number != 'take away':
            try:
                table = Table.objects.get(table_number=table_number)
                table.is_occupied = True
                table.save()
            except Table.DoesNotExist:
                pass
        
        return redirect('admin_select_items')
    
    # Get recent customers - FIXED
    try:
        all_orders = list(order.objects.all())
        phones = list(set(o.phone for o in all_orders if o.phone))
        recent_customers = []
        for phone in phones[:10]:
            try:
                customer = User.objects.get(phone=phone)
                recent_customers.append(customer)
            except User.DoesNotExist:
                pass
    except Exception as e:
        logger.error(f"Error fetching recent customers: {e}")
        recent_customers = []
    
        # Get available tables - FIXED FOR DJONGO
    # Get available tables - DETAILED DEBUG
    try:
        all_tables_query = Table.objects.all()

        
        all_tables = []
        for table in all_tables_query:
            all_tables.append(table)
            print(f"  Found: Table {table.table_number}, Occupied: {table.is_occupied}")
        
        # Filter for available tables
        available_tables = []
        for table in all_tables:
            if not table.is_occupied:
                available_tables.append(table)
        
        available_tables.sort(key=lambda x: x.table_number)
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"ERROR Type: {type(e)}")
        import traceback
        traceback.print_exc()
        available_tables = []
        
    return render(request, 'admin_place_order.html', {
        'recent_customers': recent_customers,
        'available_tables': available_tables
    })


def admin_select_items(request):
    """Admin selects items for customer order"""
    if not (request.user.is_superuser or request.user.cafe_manager):
        messages.error(request, 'Only staff members can access this!')
        return redirect('menu')
    
    if 'admin_order' not in request.session:
        messages.error(request, 'Please start a new order first!')
        return redirect('admin_place_order')
    
    if request.method == 'POST':
        cart_data = json.loads(request.POST.get('cart_data', '[]'))
        
        if not cart_data:
            messages.error(request, 'Please add items to order!')
            return redirect('admin_select_items')
        
        order_info = request.session['admin_order']
        
        # Build items_json in your existing format: {"pr1": [qty, name, price], ...}
        items_json = {}
        total = 0
        for idx, item_data in enumerate(cart_data, start=1):
            items_json[f'pr{item_data["id"]}'] = [
                item_data['quantity'],
                item_data['name'],
                item_data['price']
            ]
            total += item_data['price'] * item_data['quantity']
        
        # Create order
        now_ist = timezone.now()
        new_order = order(
            name=order_info['customer_name'],
            phone=order_info['customer_phone'],
            items_json=json.dumps(items_json),
            table=order_info['table_number'],
            order_time=now_ist,
            price=str(total),
            special_instructions=order_info['notes'],
            status='confirmed'
        )
        new_order.save()
        
        # Clear session
        del request.session['admin_order']
        
        messages.success(request, f'Order #{new_order.order_id} placed successfully!')
        return redirect('all_orders')
    
    # Get all menu items
    menu_items = menu_item.objects.all().order_by('list_order', 'name')
    categories = menu_item.objects.values_list('category', flat=True).distinct()
    
    return render(request, 'admin_select_items.html', {
        'menu_items': menu_items,
        'categories': categories
    })


def admin_edit_order(request, order_id):
    """Edit an existing order"""
    if not (request.user.is_superuser or request.user.cafe_manager):
        messages.error(request, 'Only staff members can access this!')
        return redirect('menu')
    
    order_obj = get_object_or_404(order, order_id=order_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_items':
            # Parse existing items
            try:
                items_dict = json.loads(order_obj.items_json)
            except:
                items_dict = {}
            
            # Update quantities for existing items
            updated_items = {}
            total = 0
            
            for key in items_dict.keys():
                new_qty = request.POST.get(f'quantity_{key}')
                if new_qty and int(new_qty) > 0:
                    qty = int(new_qty)
                    name = items_dict[key][1]
                    price = items_dict[key][2]
                    updated_items[key] = [qty, name, price]
                    total += qty * price
            
            # Add new item if selected
            new_item_id = request.POST.get('new_item_id')
            new_item_quantity = request.POST.get('new_item_quantity')
            
            if new_item_id and new_item_quantity:
                try:
                    new_menu_item = menu_item.objects.get(id=new_item_id)
                    qty = int(new_item_quantity)
                    price = int(new_menu_item.price)
                    updated_items[f'pr{new_item_id}'] = [qty, new_menu_item.name, price]
                    total += qty * price
                except:
                    pass
            
            # Update special instructions
            order_obj.special_instructions = request.POST.get('special_instructions', '')
            
            # Save updated order
            order_obj.items_json = json.dumps(updated_items)
            order_obj.price = str(total)
            order_obj.save()
            
            messages.success(request, 'Order updated successfully!')
            return redirect('admin_edit_order', order_id=order_id)
        
        elif action == 'cancel':
            order_obj.status = 'completed'  # Mark as completed instead of cancelled
            order_obj.save()
            messages.success(request, 'Order cancelled!')
            return redirect('all_orders')
    
    # Parse items for display
    try:
        items_dict = json.loads(order_obj.items_json)
        order_items = []
        for key, value in items_dict.items():
            order_items.append({
                'key': key,
                'quantity': value[0],
                'name': value[1],
                'price': value[2],
                'subtotal': value[0] * value[2]
            })
    except:
        order_items = []
    
    # Get all menu items for adding
    all_menu_items = menu_item.objects.all().order_by('category', 'name')
    
    return render(request, 'admin_edit_order.html', {
        'order': order_obj,
        'order_items': order_items,
        'all_menu_items': all_menu_items
    })
    
@csrf_exempt
def update_order_status(request, order_id):
    """Update order status and handle table availability"""
    if request.method == 'POST':
        status = request.POST.get('status')
        try:
            order_obj = order.objects.get(order_id=order_id)
            order_obj.status = status
            order_obj.save()
            
            # If completed, check if table should be released
            if status == 'completed' and order_obj.table != 'take away':
                try:
                    table = Table.objects.get(table_number=order_obj.table)
                    
                    # Check if there are OTHER active orders for this table
                    other_active = False
                    for o in order.objects.filter(table=order_obj.table):
                        if o.order_id != order_id and o.status in ['pending', 'preparing', 'ready', 'confirmed']:
                            other_active = True
                            break
                    
                    # Release table only if no other active orders
                    if not other_active:
                        table.is_occupied = False
                        table.save()
                        messages.success(request, f'Order #{order_id} completed! Table {order_obj.table} is now available.')
                    else:
                        messages.success(request, f'Order #{order_id} completed!')
                        
                except Table.DoesNotExist:
                    messages.success(request, f'✅ Order #{order_id} marked as {status}!')
                except Exception as e:
                    logger.error(f"Error updating table status: {e}")
                    messages.success(request, f'✅ Order #{order_id} marked as {status}!')
            else:
                messages.success(request, f'✅ Order #{order_id} marked as {status}!')
            
        except order.DoesNotExist:
            messages.error(request, '❌ Order not found!')
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            messages.error(request, f'❌ Error updating order: {str(e)}')
    
    # Redirect back to referring page
    return redirect(request.META.get('HTTP_REFERER', 'admin_orders'))

def check_table_availability(table_number):
    """
    Helper function to check if a table is available
    Returns: (is_available, message)
    """
    if not table_number or table_number == 'take away':
        return True, "Take away order"
    
    try:
        # Check if table exists
        try:
            table = Table.objects.get(table_number=table_number)
        except Table.DoesNotExist:
            return False, f"Table {table_number} does not exist"
        
        # Check for active orders
        active_orders = list(order.objects.filter(
            table=table_number,
            status__in=['pending', 'preparing', 'ready']
        ))
        
        if active_orders:
            return False, f"Table {table_number} has {len(active_orders)} active order(s)"
        
        return True, "Table available"
        
    except Exception as e:
        logger.error(f"Error checking table availability: {e}")
        return False, f"Error checking table: {str(e)}"


# --------------------- OPTIONAL: Add this to your generate_bill function ---------------------
# Add this code right before you mark table as available in generate_bill

# In generate_bill function, after marking orders as bill_clear:
    # if t_number and t_number != 'take away':
    #     try:
    #         table = Table.objects.get(table_number=t_number)
            
    #         # Check if ALL orders for this table are bill_clear
    #         all_table_orders = list(order.objects.filter(table=t_number))
    #         all_cleared = all(o.bill_clear for o in all_table_orders)
            
    #         if all_cleared:
    #             table.is_occupied = False
    #             table.save()
    #             messages.success(request, f'✅ Table {t_number} is now available!')
    #         else:
    #             messages.info(request, f'Table {t_number} still has pending bills.')
                
    #     except Table.DoesNotExist:
    #         pass
    #     except Exception as e:
    #         logger.error(f"Error releasing table: {e}")


