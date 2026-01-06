from django.db import models
from Accounts.models import User
from Services.models import Service

class Booking(models.Model):
    STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Accepted', 'Accepted'),
    ('Completed', 'Completed'),
    ('Not Available', 'Not Available'),
]
    
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Esewa', 'Esewa'),
        ('Khalti', 'Khalti'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Received', 'Received'),
        ('Cancelled', 'Cancelled'),
        ('Failed', 'Failed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    address = models.TextField(help_text="Service address", blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Customer phone number")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='Cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_cancel = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Failed')
    payment_received = models.BooleanField(default=False, help_text="Mark as received by provider")
