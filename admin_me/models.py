from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    units_sold = models.PositiveIntegerField(default=0)
    in_stock = models.PositiveIntegerField(default=0)
    expire_date = models.DateField()

    def __str__(self):
        return self.name
