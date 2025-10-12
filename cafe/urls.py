from django.contrib import admin
from django.urls import path, include
from cafe import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.menu, name='menu'),
    path('delete_dish/<int:item_id>/', views.delete_dish, name='delete_dish'),
    path('offers', views.offers, name='offers'),
    path('reviews', views.reviews, name='reviews'),
    path('profile', views.profile, name='profile'),
    path('all_orders', views.all_orders, name='all_orders'),
    path('manage_menu', views.manage_menu, name='manage_menu'),
    path('cart', views.cart, name='cart'),
    path('my_orders', views.my_orders, name='my_orders'),
    path('login', views.Login, name='login'),
    path('signup', views.signup, name='signup'),
    path('logout', views.Logout, name='logout'),
    path('generate_bill', views.generate_bill, name='generate_bill'),
    path('view_bills', views.view_bills, name='view_bills'),
    
    # ==================== TABLE MANAGEMENT URLS ====================
    path('generate_qr/', views.generate_table_qr, name='generate_qr'),
    path('tables/', views.table_list, name='table_list'),
    path('table_orders/', views.admin_orders, name='admin_orders'),
    path('update_order/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('table_management/', views.table_management, name='table_management'),
    
    # ==================== NEW: RATING URLS ====================
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('submit_ratings/<int:order_id>/', views.submit_ratings, name='submit_ratings'),
    path('upload_payment/<int:order_id>/', views.upload_payment, name='upload_payment'),
    path('mark_paid/<int:order_id>/', views.mark_payment_paid, name='mark_paid'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)