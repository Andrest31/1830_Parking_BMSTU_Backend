from parking_app import views
from django.contrib import admin
from django.urls import path
from . import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('front-hello/', views.HelloPage),
    path('front-parkings/', views.MainPage, name='MainPage'),
    path('front-parking/<int:parking_id>/', views.ParkingPage, name='ParkingPage'),
    path('front-parking/<int:parking_id>/add/', views.add_to_order, name='add_to_order'),
    path('front-pass/<int:order_id>/', views.PassPage, name='pass_page'),
    path('front-order/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('front-order/<int:order_id>/remove/<int:item_id>/', views.remove_item, name='remove_item'),
    path('front-order/<int:order_id>/update/<int:item_id>/<str:action>/', views.update_quantity, name='update_quantity'),



    # Parking endpoints
    path('parkings/', api.parking_list, name='parking-list'),
    path('parkings/<int:pk>/', api.parking_detail, name='parking-detail'),
    path('parkings/create/', api.parking_create, name='parking-create'),
    path('parkings/<int:pk>/update/', api.parking_update, name='parking-update'),
    path('parkings/<int:pk>/delete/', api.parking_delete, name='parking-delete'),
    path('parkings/<int:pk>/add-to-order/', api.add_to_order, name='add-to-order'),
    path('parkings/<int:pk>/image/', api.parking_upload_image, name='parking-upload-image'),
    
    # Order endpoints
    path('orders/', api.order_list, name='order-list'),
    path('orders/<int:pk>/', api.order_detail, name='order-detail'),
    path('orders/<int:pk>/update/', api.order_update, name='order-update'),
    path('orders/<int:pk>/submit/', api.order_submit, name='order-submit'),
    path('orders/<int:pk>/complete/', api.order_complete, name='order-complete'),
    path('orders/<int:pk>/delete/', api.order_delete, name='order-delete'),
    
    # OrderItem endpoints
    path('order-items/<int:pk>/delete/', api.order_item_delete, name='order-item-delete'),
    path('order-items/<int:pk>/update/', api.order_item_update, name='order-item-update'),
    
    # User endpoints (заглушки для ЛР4)
    path('users/register/', api.user_register, name='user-register'),
    path('users/<int:pk>/update/', api.user_update, name='user-update'),

]
