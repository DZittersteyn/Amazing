import datetime

from django.db import models

PRODUCTS = {
            'CANDYBIG':   1,
            'CANDYSMALL': 1,
            'SOUP':       1,
            'CAN':        1,
            'BEER':       1,
            'SAUSAGE':    1,
            'BAPAO':      1,
            'BREAD':      1,
            'ADMIN':      1,
            }
CREDITS = {
            'CASH',
            'DIGITAL',
            'ADMIN',
}

class User(models.Model):
    def __unicode__(self):
        return self.name
    def buy_credit(self, type, amount):
        if(type in CREDITS):
            self.credit += 10 * amount
            self.save()
            Purchase(user = self, product = type, activity = Activity.get_active()).save()
            return True
        else:
            return False
    def buy_item(self, item):
        if item != None and self.credit >= PRODUCTS[item]:
            self.credit -= PRODUCTS[item]
            self.save()
            Purchase(user = self, product = item, activity = Activity.get_active()).save()
            return True
        else:
            return False
    name = models.CharField(max_length = 255)
    address = models.CharField(max_length = 255)
    city = models.CharField(max_length = 255)
    bank_account = models.CharField(max_length = 9)
    email = models.EmailField()
    barcode = models.CharField(max_length = 10)
    isAdmin = models.BooleanField()
    credit = models.IntegerField()


class Activity(models.Model): 
    def __unicode__(self):
        return self.name
    @staticmethod
    def get_active():
        acts = Activity.objects.filter(end = None)
        if acts.exists():
            return acts[0]
        else:
            std = Activity.objects.filter(name = 'gewone verkoop')
            if std.exists():
                return std[0]
            else:
                Activity(name = 'gewone verkoop').save();
                return Activity.objects.get(name = 'gewone verkoop')
    
    @staticmethod
    def finish():
        running = Activity.objects.filter(end = None)
        for act in running:
            act.end = datetime.datetime.now()
            act.save();
        
    
    name = models.CharField(max_length = 255)
    start = models.DateTimeField(auto_now_add = True)
    end = models.DateTimeField(null = True)

class Purchase(models.Model):
    def __unicode__(self):
        return str(self.user) + " bought " + str(self.product) + " on " + str(self.date) + " at activity " + str(self.activity)
    activity = models.ForeignKey(Activity)
    user = models.ForeignKey(User)
    product = models.CharField(max_length = 255)
    date = models.DateTimeField(auto_now_add = True)



