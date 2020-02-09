from django.contrib import admin

from . import models
admin.site.register(models.Wine)
admin.site.register(models.Rating)