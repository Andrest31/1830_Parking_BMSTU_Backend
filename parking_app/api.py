from requests import Response
from .models import Parking, Order, OrderItem
from .serializers import ParkingSerializer, OrderItemSerializer, OrderSerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
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
    # Получаем фиксированного пользователя (для ЛР3)
    user = get_fixed_user()
    
    # Фильтрация парковок
    parkings = Parking.objects.filter(is_active=True)
    work_hour = request.GET.get('work_hour')
    
    if work_hour and work_hour.isdigit():
        work_hour = int(work_hour)
        parkings = parkings.filter(open_hour__lte=work_hour, close_hour__gte=work_hour)
    
    # Получаем черновик заявки пользователя (если есть)
    draft_order = Order.objects.filter(user=user, status='draft').first()
    order_data = None
    if draft_order:
        order_items_count = draft_order.items.count()
        order_data = {
            'order_id': draft_order.id,
            'items_count': order_items_count
        }
    
    # Сериализация парковок
    serializer = ParkingSerializer(parkings, many=True)
    
    # Формируем ответ
    response_data = {
        'parkings': serializer.data,
        'draft_order': order_data
    }
    
    return Response(response_data)

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

    if parking.image_url:
            try:
                minio_client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_USE_SSL
                )
                
                # Извлекаем имя файла из URL
                image_path = parking.image_url.split(f"{settings.MINIO_BUCKET_NAME}/")[-1]
                minio_client.remove_object(settings.MINIO_BUCKET_NAME, image_path)
            except Exception as e:
                # Логируем ошибку, но продолжаем удаление
                print(f"Error deleting image from MinIO: {str(e)}")

    parking.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# POST /api/parkings/<id>/add-to-order/ - добавление в заявку-черновик
@api_view(['POST'])
def add_to_order(request, pk):
    parking = get_object_or_404(Parking, pk=pk, is_active=True)
    user = get_fixed_user()
    
    order, order_created = Order.objects.get_or_create(
        user=user,
        status='draft',
        defaults={
            'user_name': user.get_full_name() or user.username,
            'created_at': timezone.now()  # Системное поле
        }
    )
    
    item, item_created = OrderItem.objects.get_or_create(
        order=order,
        parking=parking,
        defaults={'quantity': 1}
    )
    
    if not item_created:
        item.quantity += 1
        item.save()
    
    response_data = {
        'status': 'added',
        'order_id': order.id,
        'parking_id': parking.id,
        'quantity': item.quantity,
        'is_new_order': order_created,
        'is_new_item': item_created
    }
    
    return Response(response_data, status=status.HTTP_201_CREATED)

# POST /api/parkings/<id>/image/ - добавление изображения
@api_view(['POST'])
def parking_upload_image(request, pk):
    parking = get_object_or_404(Parking, pk=pk)
    
    if 'image' not in request.FILES:
        return Response(
            {'error': 'No image file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    image_file = request.FILES['image']
    minio_client = Minio(
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL
    )
    
    try:
        if parking.image_url:
            try:
                old_image_path = parking.image_url.split(f"{settings.MINIO_BUCKET_NAME}/")[-1]
                minio_client.remove_object(settings.MINIO_BUCKET_NAME, old_image_path)
            except Exception as e:
                print(f"Error deleting old image: {str(e)}")
        
        file_extension = image_file.name.split('.')[-1]
        new_filename = f"parking-{pk}-{int(time.time())}.{file_extension}"
        
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            new_filename,
            image_file,
            length=image_file.size,
            content_type=image_file.content_type
        )
        
        new_image_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET_NAME}/{new_filename}"
        parking.image_url = new_image_url
        parking.save()
        
        return Response(
            {
                'status': 'success',
                'image_url': new_image_url,
                'parking_id': pk
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': f'Image upload failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

# GET /api/orders/ - список заявок с фильтрацией
@api_view(['GET'])
def order_list(request):
    try:
        # Базовый запрос (исключаем удаленные и черновики)
        orders = Order.objects.exclude(status__in=['deleted', 'draft'])
        
        # Фильтрация по статусу
        status_filter = request.GET.get('status')
        if status_filter:
            if status_filter not in ['formed', 'completed', 'rejected']:
                return Response(
                    {"error": "Invalid status value. Use: formed, completed, rejected"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            orders = orders.filter(status=status_filter)
        
        # Фильтрация по дате (исправлено sumbited_at → submitted_at)
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if date_from:
            try:
                orders = orders.filter(sumbited_at__date__gte=date_from)
            except ValueError:
                return Response(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        if date_to:
            try:
                orders = orders.filter(submitted_at__date__lte=date_to)
            except ValueError:
                return Response(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Добавляем сортировку по дате создания (новые сначала)
        orders = orders.order_by('-created_at')
        
        serializer = OrderSerializer(orders, many=True)
        
        # Возвращаем даже пустой массив с пояснением
        response_data = {
            "count": orders.count(),
            "orders": serializer.data,
            "message": "No orders found" if not orders.exists() else None
        }
        
        return Response(response_data)
    
    except Exception as e:
        return Response(
            {"error": f"Server error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
    """
    Обновление полей заявки (только для черновиков)
    Разрешенные поля: user_name, state_number, deadline
    """
    try:
        # 1. Получаем заявку
        order = Order.objects.get(pk=pk, user=get_fixed_user())
        
        # 2. Проверяем, что заявка в статусе черновика
        if order.status != 'draft':
            return Response(
                {"error": "Only draft orders can be modified"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Проверяем и фильтруем разрешенные поля
        allowed_fields = {'user_name', 'state_number', 'deadline'}
        update_data = {
            k: v for k, v in request.data.items() 
            if k in allowed_fields
        }
        
        if not update_data:
            return Response(
                {"error": "No valid fields provided for update"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. Обновляем заявку
        serializer = OrderSerializer(
            instance=order, 
            data=update_data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found or not owned by user"},
            status=status.HTTP_404_NOT_FOUND
        )

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