from django.db import models
from django.contrib.auth.models import User

class Wine(models.Model):
    title = models.CharField(max_length=150)
    winery = models.CharField(max_length=70)
    country = models.CharField(max_length=30)
    province = models.CharField(max_length=35)
    variety = models.CharField(max_length=40)
    points = models.FloatField(default=0)
    price = models.IntegerField(default=0)
    description = models.CharField(max_length=1000)
    image = models.ImageField(
        max_length=144, upload_to='wine_images/')
    def __str__(self):
        return f'{self.id} {self.title}'

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE)
    rating = models.FloatField(default=0)

    def __str__(self):
        return f'{self.user} {self.wine}'