from django.contrib import admin

# Register your models here.
from .models import Parking, Order, OrderItem

admin.site.register(Parking)
admin.site.register(Order)
admin.site.register(OrderItem)