from django.db import models
from django.contrib.auth.models import User

class Table(models.Model):
    table_number = models.IntegerField(unique=True)
    capacity = models.IntegerField(default=4)
    is_locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    locked_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='table_images/', null=True, blank=True) 

    def __str__(self):
        return f"Table {self.table_number}"
    
    class Meta:
        ordering = ['table_number']