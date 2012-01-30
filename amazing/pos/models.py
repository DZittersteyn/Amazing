import datetime
import pickle

from django.db import models
from pos.products import Product


class User(models.Model):
    def __unicode__(self):
        return self.name
    name = models.CharField(max_length = 255)
    adress = models.CharField(max_length = 255)
    city = models.CharField(max_length = 255)
    bank_account = models.CharField(max_length = 9)
    email = models.EmailField()
    barcode = models.CharField(max_length = 10)
    isAdmin = models.BooleanField()
    credit = models.IntegerField()


class Activity(models.Model): 
    name = models.CharField(max_length = 255)
    start = models.DateTimeField(auto_now_add = True)
    end = models.DateTimeField(null = True)

class Purchase(models.Model):
    activity = models.ForeignKey(Activity)
    user = models.ForeignKey(User)
    product = models.ForeignKey(Product)
    date = models.DateTimeField(auto_now_add = True)



