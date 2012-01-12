from django.db import models

PRODUCTS = (
            ('CANDYBIG', 'Groot Snoep'),
            ('CANDYSMALL', 'Klein Snoep'),
            ('BEER', 'Bier'),
            ('SAUSAGE', 'Broodje Rookworst'),
            ('BAPAO', 'Broodje Bapao'),
            ('BREAD', 'Broodje met Beleg'),
            ('SOUP', 'Soep'),
            ('CAN', 'Blikje drinken'),
            )

class Product(models.Model):
    type = models.CharField(max_length = 10, choices = PRODUCTS, unique = True)
    cost = models.DecimalField(max_digits = 5, decimal_places = 2)


