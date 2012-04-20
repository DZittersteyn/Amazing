import datetime

from django.db import models

PRODUCTS = {
            'CANDYBIG':   {'price': 1, 'desc': 'Groot Snoep'},
            'CANDYSMALL': {'price': 1, 'desc': 'Klein Snoep'},
            'SOUP':       {'price': 1, 'desc': 'Soep'},
            'CAN':        {'price': 1, 'desc': 'Blikje'},
            'BEER':       {'price': 1, 'desc': 'Bier'},
            'SAUSAGE':    {'price': 1, 'desc': 'Broodje rookworst'},
            'BAPAO':      {'price': 1, 'desc': 'Bapao'},
            'BREAD':      {'price': 1, 'desc': 'Broodje beleg'},
            'ADMIN':      {'price': 1, 'desc': 'Door admin gezet'},
            }


CREDITS = {
            'CASH': {'price': -10 , 'desc': 'Cash lijntje'},
            'DIGITAL': {'price': -10 , 'desc': 'Gemachtigd lijntje'},
            'ADMIN': {'price': -10 , 'desc': 'Adminlijntje'},
}

class User(models.Model):
    def __unicode__(self):
        return self.name
    def buy_credit(self, type, amount):
        if(type in CREDITS):
            self.credit -= CREDITS[type]['price'] * amount
            self.save()
            for i in range(amount):
                Purchase(user = self, product = type, activity = Activity.get_active()).save()
            return True
        else:
            return False
    def buy_item(self, item):
        if item != None and self.credit >= PRODUCTS[item]['price']:
            self.credit -= PRODUCTS[item]['price']
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
    has_passcode = models.BooleanField(default = False)
    passcode = models.CharField(max_length = 255) # Logging in from the actual POS requires an optional passcode
    password = models.CharField(max_length = 255) # Logging in from a remote location requires this password
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
    def desc(self):
        if self.product in PRODUCTS:
            return PRODUCTS[self.product]['desc']
        elif self.product in CREDITS:
            return CREDITS[self.product]['desc']
        else:
            return "UNKNOWN!"
    activity = models.ForeignKey(Activity)
    user = models.ForeignKey(User)
    product = models.CharField(max_length = 255)
    date = models.DateTimeField(auto_now_add = True)
    valid = models.BooleanField(default=True)



