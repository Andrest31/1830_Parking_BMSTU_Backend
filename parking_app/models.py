from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Parking(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10)
    place = models.CharField(max_length=255)
    open_hour = models.IntegerField()
    close_hour = models.IntegerField()
    image_url = models.URLField(max_length=500)
    description_url = models.URLField(max_length=500)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'parkings'

class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('deleted', 'Удален'),
        ('formed', 'Сформирован'),
        ('completed', 'Завершен'),
        ('rejected', 'Отклонен'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    sumbited_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateField(default=timezone.now)  # Новое поле
    user_name = models.CharField(max_length=100)
    state_number = models.CharField(max_length=20)
    
    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"
    
    class Meta:
        db_table = 'orders'


class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('order', 'parking')
        db_table = 'orderitem'

    
    def __str__(self):
        return f"{self.quantity} x {self.parking.short_name}"