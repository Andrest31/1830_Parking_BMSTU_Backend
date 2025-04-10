from .models import Parking, Order, OrderItem
from rest_framework import serializers
from django.contrib.auth.models import User

class ParkingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parking
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at', 'submitted_at', 'completed_at')

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parking
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']