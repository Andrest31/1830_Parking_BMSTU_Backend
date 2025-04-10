from django.http import HttpResponse
from .models import Parking, Order, OrderItem
from django.shortcuts import get_object_or_404, render, redirect

# Данные парковок (коллекция)
PARKINGS_DATA = [
    {
        "id": 1,
        "name": "Главное здание",
        "short_name": "ГЗ",
        "place": "Москва, 2-я Бауманская ул., 5, стр. 4",
        "open_hour": 8,
        "close_hour": 21,
        "image_card": "http://localhost:9000/images/mock.jpg",
        "image_discr": "http://localhost:9000/images/building1.jpg",
        "status": True,
        "description": "Парковка у главного входа в университет. Охраняемая территория, видеонаблюдение."
    },
    {
        "id": 2,
        "name": "Учебно-лабораторный корпус",
        "short_name": "УЛК",
        "place": "Москва, Рубцовская наб., 2/18",
        "open_hour": 7,
        "close_hour": 22,
        "image_card": "http://localhost:9000/images/mock.jpg",
        "image_discr": "http://localhost:9000/images/building2.jpg",
        "status": True,
        "description": "Парковка для сотрудников УЛК. Крытая часть доступна в плохую погоду."
    },
    {
        "id": 3,
        "name": "Спортивный комплекс",
        "short_name": "СК",
        "place": "Москва, Госпитальный пер., 4/6",
        "open_hour": 6,
        "close_hour": 23,
        "image_card": "http://localhost:9000/images/mock.jpg",
        "image_discr": "http://localhost:9000/images/building3.jpg",
        "status": True,
        "description": "Парковка рядом со спортзалом. Доступна для посетителей мероприятий."
    }
]

# Текущая заявка (корзина)
CURRENT_ORDER = {
    "id": 1,
    "user_name": "Андрест Владислав Дмитриевич",
    "car_number": "С532РР178",
    "status": "draft",
    "items": [
        {
            "parking_id": 1,
            "parking_name": "ГЗ",
            "quantity": 1,
            "image": "http://localhost:9000/parking-images/gz.jpg"
        }
    ],
    "total_quantity": 1
}

def get_draft_order(user_id):
    return {
        'id': 1,
        'items': [],
        'total_quantity': 0
    }

def HelloPage(request):
    return render(request, 'HelloPage.html')

def MainPage(request):
    parkings = Parking.objects.filter(is_active=True)
    work_hour = request.GET.get('work_hour')
    
    # Фильтрация парковок
    if work_hour and work_hour.isdigit():
        work_hour = int(work_hour)
        filtered_parkings = [
            p for p in parkings 
            if p.open_hour <= work_hour <= p.close_hour
        ]
    else:
        filtered_parkings = parkings
    
    order = Order.objects.filter(user=request.user, status='draft').first()
    total_quantity = sum(item['quantity'] for item in CURRENT_ORDER['items'])
    
    context = {
        'parkings': filtered_parkings,
        'search_hour': work_hour or '',
        'order': order,
        'total_quantity': total_quantity
    }
    return render(request, 'MainPage.html', context)


def ParkingPage(request, parking_id):
    try:
        parking = Parking.objects.get(id=parking_id, is_active=True)
        return render(request, 'ParkingPage.html', {'parking': parking})
    except Parking.DoesNotExist:
        return HttpResponse("Парковка не найдена", status=404)

def add_to_order(request, parking_id):
    # Получаем парковку или возвращаем 404
    parking = get_object_or_404(Parking, id=parking_id, is_active=True)
    
    # Получаем или создаем черновик заявки для пользователя
    order, created = Order.objects.get_or_create(
        user=request.user,
        status='draft',
        defaults={
            'user_name': request.user.get_full_name() or request.user.username,
            'car_number': '',  # Можно установить значение по умолчанию
        }
    )
    
    # Пытаемся найти существующий элемент заявки для этой парковки
    item, item_created = OrderItem.objects.get_or_create(
        order=order,
        parking=parking,
        defaults={
            'quantity': 1,
        }
    )
    
    # Если элемент уже существовал, увеличиваем количество
    if not item_created:
        item.quantity += 1
        item.save()
    
    return redirect('MainPage')

def PassPage(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        order.user_name = request.POST.get('user_name', '')
        order.car_number = request.POST.get('car_number', '')
        order.save()
        return redirect('pass_page', order_id=order.id)
    
    items = order.items.select_related('parking').all()
    return render(request, 'PassPage.html', {'order': order, 'items': items})


def clear_order(request):
    CURRENT_ORDER['items'] = []
    return redirect('pass_page', order_id=CURRENT_ORDER['id'])

def remove_item(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    item.delete()
    return redirect('pass_page', order_id=order.id)

def update_quantity(request, order_id, item_id, action):
    # Получаем заявку и проверяем права доступа
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Получаем конкретный элемент заявки
    item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    # Изменяем количество
    if action == 'increase':
        item.quantity += 1
    elif action == 'remove':
        item.delete()
    elif action == 'decrease':
        if item.quantity > 1:  # Не позволяем уменьшить ниже 1
            item.quantity -= 1
    
    # Сохраняем изменения
    item.save()
    
    # Перенаправляем обратно на страницу заявки
    return redirect('pass_page', order_id=order.id)