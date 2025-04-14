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
        model = OrderItem  # Исправлено с Parking на OrderItem
        fields = ['id', 'order', 'parking', 'quantity']
        read_only_fields = ['id', 'order', 'parking']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

class OrderItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['quantity']

class OrderItemDeleteSerializer(serializers.Serializer):
    parking_id = serializers.IntegerField()

class OrderDetailSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Order
        fields = [
            'id',
            'status',
            'user_name',
            'state_number',
            'created_at',
            'sumbited_at',
            'accepted_at'
        ]
        read_only_fields = fields

class OrderItemWithImageSerializer(serializers.ModelSerializer):
    parking_name = serializers.CharField(source='parking.name', read_only=True)
    parking_image = serializers.URLField(source='parking.image_url', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'quantity',
            'parking_name',
            'parking_image'
        ]