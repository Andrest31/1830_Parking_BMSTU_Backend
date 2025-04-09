from django.http import HttpResponse
from .models import Parking
from django.shortcuts import render, redirect

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
            if p['open_hour'] <= work_hour <= p['close_hour']
        ]
    else:
        filtered_parkings = parkings
    
    total_quantity = sum(item['quantity'] for item in CURRENT_ORDER['items'])
    
    context = {
        'parkings': filtered_parkings,
        'search_hour': work_hour or '',
        'order': CURRENT_ORDER,
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
    parking = next((p for p in PARKINGS_DATA if p['id'] == parking_id), None)
        
    if parking:
            item = next((item for item in CURRENT_ORDER['items'] if item['parking_id'] == parking_id), None)
            
            if item:
                item['quantity'] += 1
            else:
                CURRENT_ORDER['items'].append({
                    'parking_id': parking_id,
                    'parking_name': parking['short_name'],
                    'quantity': 1,
                    'image': parking['image_card']
                })
    
    return redirect('MainPage')

def PassPage(request, order_id):
    if request.method == 'POST':
        # Обработка сохранения данных формы
        CURRENT_ORDER['user_name'] = request.POST.get('user_name', '')
        CURRENT_ORDER['car_number'] = request.POST.get('car_number', '')
        # Здесь можно добавить обработку даты, если нужно
        
        # Обработка изменения количества
        for item in CURRENT_ORDER['items']:
            quantity = request.POST.get(f'quantity_{item["parking_id"]}', 1)
            item['quantity'] = max(1, int(quantity))  # Не меньше 1
        
        return redirect('pass_page', order_id=order_id)
    
    if order_id != CURRENT_ORDER['id']:
        return HttpResponse("Заявка не найдена", status=404)
    
    return render(request, 'PassPage.html', {
        'order': CURRENT_ORDER
    })

def clear_order(request):
    CURRENT_ORDER['items'] = []
    return redirect('pass_page', order_id=CURRENT_ORDER['id'])

def remove_item(request, parking_id):
    CURRENT_ORDER['items'] = [item for item in CURRENT_ORDER['items'] if item['parking_id'] != parking_id]
    return redirect('pass_page', order_id=CURRENT_ORDER['id'])

def update_quantity(request, parking_id, action):
    for item in CURRENT_ORDER['items']:
        if item['parking_id'] == parking_id:
            if action == 'increase':
                item['quantity'] += 1
            elif action == 'decrease' and item['quantity'] > 1:
                item['quantity'] -= 1
            break
    return redirect('pass_page', order_id=CURRENT_ORDER['id'])