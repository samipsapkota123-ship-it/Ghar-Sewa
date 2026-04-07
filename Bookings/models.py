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
        # ('Khalti', 'Khalti'),
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

class ReviewRating(models.Model):
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_reviews',
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_reviews',
        null=True,
        blank=True,
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
        null=True,
        blank=True,
    )
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject or f'Review #{self.pk}'
