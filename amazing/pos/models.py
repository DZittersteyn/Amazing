import datetime
# import urllib
import os
import json

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers


EXCHANGE = 0.55  # Price of one credit in Euros. Positive float.

PRODUCTS = {  # price is in CREDITS! always a positive integer
            'CANDYBIG':   {'price': 1, 'desc': 'Groot Snoep'},
            'CANDYSMALL': {'price': 1, 'desc': 'Klein Snoep'},
            'SOUP':       {'price': 1, 'desc': 'Soep'},
            'CAN':        {'price': 1, 'desc': 'Blikje'},
            'BEER':       {'price': 1, 'desc': 'Bier'},
            'SAUSAGE':    {'price': 1, 'desc': 'Broodje rookworst'},
            'BAPAO':      {'price': 1, 'desc': 'Bapao'},
            'BREAD':      {'price': 1, 'desc': 'Broodje beleg'},
            }


CREDITS = {  # price is in CREDITS! always a negative integer.
             # editor beware, -2 means a user gets 2 credits per EXCHANGE euro.
             # Don't know why you would want this, but it's in there anyways ;)
            'DIGITAL': {'price': -1, 'desc': 'Kruisje'},
            #'ADMIN':   {'price': -1, 'desc': 'Admin kruisje'},
            }


class User(models.Model):
    def __unicode__(self):
        return self.name

    def as_dict(self):
        data = json.loads(serializers.serialize('json', [self]))
        data[0]['fields']['credit'] = self.get_credit()
        data[0]['fields']['pk'] = data[0]['pk']
        return data[0]['fields']

    def buy_credit(self, type, amount, activity, admin=False):
        if amount > 0:
            if type in CREDITS:
                price = CREDITS[type]['price']
                if type == 'DIGITAL':
                    filename = " ".join([self.name, datetime.datetime.now().strftime("%Y %m %d-%H %M %S")]).replace(" ", "_") + ".pdf"
                    # url = "http://www.svcover.nl/incasso/api"
                    # dataDict = {
                    #            'app': 'awesome',
                    #            'bedrag': amount * EXCHANGE,
                    #            'omschrijving': str(amount) + " kruisjes kopen via amazing",
                    #            'naam': self.name,
                    #            'adres': self.address,
                    #            'woonplaats': self.city,
                    #            'rekeningnummer': self.bank_account,
                    #            }
                    #if self.email != "":
                    #    dataDict['email'] = self.email
                    #data = urllib.urlencode(dataDict)

                    #print(data)

                    #outfile = open(filename, 'wb')
                    #try:
                    #    infile = urllib2.urlopen(url,data)
                    #except URLError:
                    #    print ("urlerror")
                    #    return False
                    #shutil.copyfileobj(infile.fp, outfile)
                    #outfile.close()
                    #infile.close()

                    # TODO: Print

                    Purchase(date=datetime.datetime.now(), user=self, product=type, price=price * amount, activity=activity, assoc_file=filename).save()

                    return True
                elif type == 'ADMIN':
                    Purchase(date=datetime.datetime.now(), user=self, product=type, price=price * amount, activity=activity, admin=True).save()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return True

    def buy_item(self, item, amount, activity, admin=False):
        if item != None and self.get_credit() >= PRODUCTS[item]['price'] * amount or admin == True:
            for i in range(amount):
                Purchase(date=datetime.datetime.now(), user=self, product=item, price=PRODUCTS[item]['price'], activity=activity, admin=admin).save()
            return True
        else:
            return False

    def get_credit(self):
        purchases = Purchase.objects.filter(user=self).filter(valid=True)
        credit = 0
        for purchase in purchases:
            credit -= purchase.price
        return credit

    def get_latest_purchase_date(self):
        return Purchase.objects.filter(user=self).order_by('-date')[:1]

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    bank_account = models.CharField(max_length=9)
    email = models.EmailField()
    barcode = models.CharField(max_length=10)
    isAdmin = models.BooleanField()
    has_passcode = models.BooleanField(default=False)
    passcode = models.CharField(max_length=255)  # Logging in from the actual POS requires an optional passcode
    active = models.BooleanField(default=True)


class Activity(models.Model):
    def __unicode__(self):
        return self.name

    @staticmethod
    def get_normal_sale():
        act, created = Activity.objects.get_or_create(name='Gewone Verkoop', defaults={'start': datetime.datetime.now()})
        act.end = None
        act.save()
        return act

    @staticmethod
    def get_active():
        acts = Activity.objects.exclude(end__lt=datetime.datetime.now()).exclude(start=None).order_by('-start')
        if acts.exists():  # return the running activity that was started last
            return acts[0]
        else:
            return Activity.get_normal_sale()

    @staticmethod
    def finish():
        running = Activity.objects.filter(end=None)
        for act in running:
            act.end = datetime.datetime.now()
            act.save()
        normal = Activity.get_normal_sale()
        normal.end = None
        normal.save()

    name = models.CharField(max_length=255, blank=False)
    responsible = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)


class Purchase(models.Model):
    def __unicode__(self):
        return str(self.user) + " bought " + str(self.product) + " for " + str(self.price) + " credits on " + str(self.date) + " at activity " + str(self.activity)

    def desc(self):
        if self.product in PRODUCTS:
            return PRODUCTS[self.product]['desc']
        elif self.product in CREDITS:
            return CREDITS[self.product]['desc']
        else:
            return "Unknown ID: " + self.product + "."

    @staticmethod
    def csvheader():
        return ", ".join([
            "username",
            "product",
            "price",
            "date",
            "time",
            "valid",
            "admin"
            ])

    def csv(self):
        return ", ".join([
            self.user.name,
            self.product,
            str(self.price),
            self.date.date().isoformat(),
            self.date.time().isoformat(),
            str(self.valid),
            str(self.admin)
            ])

    activity = models.ForeignKey(Activity)
    user = models.ForeignKey(User)
    product = models.CharField(max_length=255)
    price = models.IntegerField()
    date = models.DateTimeField()
    valid = models.BooleanField(default=True)
    admin = models.BooleanField(default=False)
    assoc_file = models.CharField(max_length=255)


class Product(models.Model):
    description = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    # Not a choicefield, as the catagories may change. Were I to do design this from scratch, PRODUCTS and CREDITS would be a database, fixing this issue.
    amount = models.IntegerField(default=0)


class Inventory_balance(models.Model):
    description = models.CharField(max_length=255)  # e.g. "Inventory check Feb 18 2013"
    date = models.DateTimeField(auto_now_add=True)
    activity = models.ForeignKey(Activity, blank=True, null=True)


class Inventory_balance_product(models.Model):
    # inventory_balance entries set the current inventory count.
    # an inv_bal is declarative, i.e. the amounts entered *replace* what we currently think
    # is in our inventory.
    # this is used to account for differences in real and registered stock, due
    # to theft, loss, etc
    inventory = models.ForeignKey(Inventory_balance)
    category = models.CharField(max_length=255)     # e.g. "CANDYBIG"
    modification = models.IntegerField()            # e.g. 20 (count is in *credits*, not number of items)


class Inventory_purchase(models.Model):
    description = models.CharField(max_length=255)  # e.g. "Inventory check Feb 18 2013"
    date = models.DateTimeField(auto_now_add=True)
    activity = models.ForeignKey(Activity, blank=True, null=True)


class Inventory_purchase_product(models.Model):
    # inventory_purchase entries change the current inventory count by a certain amount.
    # an inv_purc is incremental, i.e. the amounts are *added* to what we currently think is
    # our inventory
    inventory = models.ForeignKey(Inventory_purchase)
    category = models.CharField(max_length=255)    # e.g. "CANDYBIG"
    modification = models.IntegerField()           # e.g. +5 or -3 (in *credits*, not number of items)


class Export(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    running = models.BooleanField(default=False)
    done = models.BooleanField(default=False)
    progress = models.IntegerField(default=0)
    filename = models.CharField(max_length=255)
