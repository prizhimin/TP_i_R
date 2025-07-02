from django.db import models
# from django.contrib.auth.models import AbstractUser


class Department(models.Model):
    """
    Список филиалов
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
