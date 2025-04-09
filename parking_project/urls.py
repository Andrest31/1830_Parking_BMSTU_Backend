from parking_app import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('hello/', views.HelloPage),
    path('parkings/', views.MainPage, name='MainPage'),
    path('parking/<int:parking_id>/', views.ParkingPage, name='ParkingPage'),
    path('parking/<int:parking_id>/add/', views.add_to_order, name='add_to_order'),
    path('pass/<int:order_id>/', views.PassPage, name='pass_page'),
    path('order/clear/', views.clear_order, name='clear_order'),
    path('order/remove/<int:parking_id>/', views.remove_item, name='remove_item'),
    path('order/update/<int:parking_id>/<str:action>/', views.update_quantity, name='update_quantity'),
]
