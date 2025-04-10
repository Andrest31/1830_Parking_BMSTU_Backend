from parking_app import views
from django.contrib import admin
from django.urls import path, include
from parking_app.models import Parking, Order, OrderItem
from parking_app.serializers import ParkingSerializer, OrderSerializer, OrderItemSerializer

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

    path('api/', include('parking_app.urls')),
]
