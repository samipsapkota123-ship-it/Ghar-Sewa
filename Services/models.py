from django.db import models
from Accounts.models import User

class Service(models.Model):
    CATEGORY_CHOICES = [
    ('Plumbing', 'Plumbing'),
    ('Electrical', 'Electrical'),
    ('Cleaning', 'Cleaning'),
    ('Painting', 'Painting'),
    ('Appliance Repair', 'Appliance Repair'),
    ('Handyman', 'Handyman'),
]


    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.IntegerField()
    provider = models.ForeignKey(User, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True, help_text="Service availability status")

    def __str__(self):
        return self.name
