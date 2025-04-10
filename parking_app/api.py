from requests import Response
from .models import Parking, Order, OrderItem
from .serializers import ParkingSerializer, OrderItemSerializer, OrderSerializer, UserSerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import time
from minio import Minio

# Заглушка для пользователя (как требуется в ТЗ ЛР3)
def get_fixed_user():
    """Singleton-функция возвращает фиксированного пользователя для ЛР3"""
    user, _ = User.objects.get_or_create(
        username='fixed_user',
        defaults={'email': 'user@example.com', 'password': 'unused'}
    )
    return user


# GET /api/parkings/ - список парковок с фильтрацией
@api_view(['GET'])
def parking_list(request):
    parkings = Parking.objects.filter(is_active=True)
    work_hour = request.GET.get('work_hour')
    
    if work_hour and work_hour.isdigit():
        work_hour = int(work_hour)
        parkings = parkings.filter(open_hour__lte=work_hour, close_hour__gte=work_hour)
    
    serializer = ParkingSerializer(parkings, many=True)
    return Response(serializer.data)

# GET /api/parkings/<id>/ - получение одной парковки
@api_view(['GET'])
def parking_detail(request, pk):
    parking = get_object_or_404(Parking, pk=pk, is_active=True)
    serializer = ParkingSerializer(parking)
    return Response(serializer.data)

# POST /api/parkings/ - добавление новой парковки
@api_view(['POST'])
def parking_create(request):
    serializer = ParkingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUT /api/parkings/<id>/ - изменение парковки
@api_view(['PUT'])
def parking_update(request, pk):
    parking = get_object_or_404(Parking, pk=pk)
    serializer = ParkingSerializer(parking, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# DELETE /api/parkings/<id>/ - удаление парковки
@api_view(['DELETE'])
def parking_delete(request, pk):
    parking = get_object_or_404(Parking, pk=pk)
    parking.is_active = False
    parking.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

# POST /api/parkings/<id>/add-to-order/ - добавление в заявку-черновик
@api_view(['POST'])
def add_to_order(request, pk):
    parking = get_object_or_404(Parking, pk=pk, is_active=True)
    order, created = Order.objects.get_or_create(
        user = get_fixed_user(),
        status='draft',
        defaults={'user_name': "Fixed User"}
    )
    
    item, created = OrderItem.objects.get_or_create(
        order=order,
        parking=parking,
        defaults={'quantity': 1}
    )
    
    if not created:
        item.quantity += 1
        item.save()
    
    return Response({'status': 'added'}, status=status.HTTP_201_CREATED)

# POST /api/parkings/<id>/image/ - добавление изображения
@api_view(['POST'])
def parking_upload_image(request, pk):
    parking = get_object_or_404(Parking, pk=pk)
    image = request.FILES.get('image')
    
    if not image:
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Upload to MinIO
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL
    )
    
    try:
        image_name = f"parking-{pk}-{int(time.time())}.{image.name.split('.')[-1]}"
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            image_name,
            image,
            length=image.size,
            content_type=image.content_type
        )
        
        parking.image_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/{image_name}"
        parking.save()
        
        return Response({'image_url': parking.image_url})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# GET /api/orders/ - список заявок с фильтрацией
@api_view(['GET'])
def order_list(request):
    orders = Order.objects.exclude(status__in=['deleted', 'draft'])
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Фильтрация по дате формирования
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        orders = orders.filter(sumbited_at__gte=date_from)
    if date_to:
        orders = orders.filter(sumbited_at__lte=date_to)
    
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

# GET /api/orders/<id>/ - получение заявки с услугами
@api_view(['GET'])
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.user != get_fixed_user() and not get_fixed_user().is_staff:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    order_serializer = OrderSerializer(order)
    items = OrderItem.objects.filter(order=order)
    items_serializer = OrderItemSerializer(items, many=True)
    
    response_data = order_serializer.data
    response_data['items'] = items_serializer.data
    return Response(response_data)

# PUT /api/orders/<id>/ - изменение заявки
@api_view(['PUT'])
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk, user=get_fixed_user())
    
    if order.status != 'draft':
        return Response(
            {'error': 'Only draft orders can be modified'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = OrderSerializer(order, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUT /api/orders/<id>/submit/ - формирование заявки
@api_view(['PUT'])
def order_submit(request, pk):
    order = get_object_or_404(Order, pk=pk, user=get_fixed_user())
    
    if order.status != 'draft':
        return Response(
            {'error': 'Only draft orders can be submitted'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверка обязательных полей
    if not order.user_name or not order.state_number:
        return Response(
            {'error': 'User name and car number are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    order.status = 'formed'
    order.sumbited_at = timezone.now()
    order.save()
    
    return Response(OrderSerializer(order).data)

# PUT /api/orders/<id>/complete/ - завершение заявки
@api_view(['PUT'])
def order_complete(request, pk):
    order = get_object_or_404(Order, pk=pk, status='formed')
    
    action = request.data.get('action')
    if action not in ['complete', 'reject']:
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if action == 'complete':
        order.status = 'completed'
        # Расчет стоимости
        items = OrderItem.objects.filter(order=order)
        total = sum(item.parking.price * item.quantity for item in items)
        order.total_price = total
    else:
        order.status = 'rejected'
    
    order.accepted_at = timezone.now()
    order.moderator = get_fixed_user()
    order.save()
    
    return Response(OrderSerializer(order).data)

# DELETE /api/orders/<id>/ - удаление заявки
@api_view(['DELETE'])
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk, user=get_fixed_user())
    
    if order.status != 'draft':
        return Response(
            {'error': 'Only draft orders can be deleted'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    order.status = 'deleted'
    order.save()
    return Response(status=status.HTTP_204_NO_CONTENT)



# DELETE /api/order-items/<id>/ - удаление из заявки
@api_view(['DELETE'])
def order_item_delete(request, pk):
    item = get_object_or_404(OrderItem, pk=pk)
    order = item.order
    
    if order.user != get_fixed_user() or order.status != 'draft':
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# PUT /api/order-items/<id>/ - изменение количества
@api_view(['PUT'])
def order_item_update(request, pk):
    item = get_object_or_404(OrderItem, pk=pk)
    order = item.order
    
    if order.user != get_fixed_user() or order.status != 'draft':
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    quantity = request.data.get('quantity')
    if not quantity or not str(quantity).isdigit() or int(quantity) < 1:
        return Response(
            {'error': 'Invalid quantity'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    item.quantity = int(quantity)
    item.save()
    return Response(OrderItemSerializer(item).data)

# POST /api/users/register/ - регистрация
@api_view(['POST'])
def user_register(request):
    return Response(
        {'message': 'Auth will be implemented in Lab 4'},
        status=status.HTTP_501_NOT_IMPLEMENTED
    )

# PUT /api/users/<id>/ - изменение пользователя
@api_view(['PUT'])
def user_update(request, pk):
    return Response(
        {'message': 'Auth will be implemented in Lab 4'},
        status=status.HTTP_501_NOT_IMPLEMENTED
    )