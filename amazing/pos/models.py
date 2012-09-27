import datetime
# import urllib
import os

from django.db import models

EXCHANGE = 0.25  # Price of one credit in Euros. Positive float.

PRODUCTS = {  # price is in CREDITS! always a positive integer
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


CREDITS = {  # price is in CREDITS! always a negative integer.
             # editor beware, -2 means a user gets 2 credits per EXCHANGE euro.
             # Don't know why you would want this, but it's in there anyways ;)
            'CASH':    {'price': -1, 'desc': 'Cash kruisje'},
            'DIGITAL': {'price': -1, 'desc': 'Gemachtigd kruisje'},
            'ADMIN':   {'price': -1, 'desc': 'Admin kruisje'},
}


class Writer():
    @staticmethod
    def write(message):
        dir = os.path.dirname(message)
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            f = open(message, "w")
            f.close()
        except IOError:
            print("ERROR WRITING FILE!!!!!")


class User(models.Model):
    def __unicode__(self):
        return self.name

    def buy_credit(self, type, amount):
        if type in CREDITS:
            if type == 'DIGITAL':
                Writer.write("purchase/" + self.name + "/" + datetime.datetime.now().isoformat() + " " + str(amount) + " credits worth of " + CREDITS[type]['desc'])

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

                self.credit -= CREDITS[type]['price'] * amount
                self.save()
                Purchase(user=self, product=type, price=CREDITS[type]['price'] * amount, activity=Activity.get_active(), assoc_file=filename).save()

                return True
            else:
                return False
        else:
            return False

    def buy_item(self, item):
        if item != None and self.credit >= PRODUCTS[item]['price']:
            self.credit -= PRODUCTS[item]['price']
            self.save()
            Purchase(user=self, product=item, price=PRODUCTS[item]['price'], activity=Activity.get_active()).save()

            Writer.write("purchase/" + self.name + "/" + datetime.datetime.now().isoformat() + " " + str(PRODUCTS[item]['price']) + " credits worth of " + PRODUCTS[item]['desc'])

            return True
        else:
            return False

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
    credit = models.IntegerField()
    active = models.BooleanField(default=True)


class Activity(models.Model):
    def __unicode__(self):
        return self.name

    @staticmethod
    def get_active():
        acts = Activity.objects.filter(end=None)
        if acts.exists():
            return acts[0]
        else:
            std = Activity.objects.filter(name='Gewone Verkoop')
            if std.exists():
                return std[0]
            else:
                Activity(name='Gewone Verkoop').save()
                Activity.finish()
                return Activity.objects.get(name='Gewone Verkoop')

    @staticmethod
    def finish():
        running = Activity.objects.filter(end=None)
        for act in running:
            act.end = datetime.datetime.now()
            act.save()

    name = models.CharField(max_length=255)
    responsible = models.CharField(max_length=255)
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(null=True)


class Purchase(models.Model):
    def __unicode__(self):
        return str(self.user) + " bought " + str(self.product) + " for " + str(self.price) + " credits on " + str(self.date) + " at activity " + str(self.activity)

    def desc(self):
        if self.product in PRODUCTS:
            return PRODUCTS[self.product]['desc']
        elif self.product in CREDITS:
            return CREDITS[self.product]['desc']
        else:
            return "UNKNOWN!"
    activity = models.ForeignKey(Activity)
    user = models.ForeignKey(User)
    product = models.CharField(max_length=255)
    price = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    valid = models.BooleanField(default=True)
    admin = models.BooleanField(default=False)
    assoc_file = models.CharField(max_length=255)

class Inventory(models.Model):
    choices = [[PRODUCTS[a]['desc'], a] for a in PRODUCTS.keys()]
    #item = models.CharField(max_length=30, choices)