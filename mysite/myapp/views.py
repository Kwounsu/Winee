import csv, io

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.db.models import Avg

from . import models
from . import forms

# Create your views here.
def index(request):
    rate_stacked = models.Rating.objects.all().count()
    context = {
        "title":"Best Bottle",
        "rate_stacked":rate_stacked,
    }
    return render(request, "index.html", context=context)

def logout_view(request):
    logout(request)
    return redirect("/login/")

def register(request):
    if request.method == "POST":
        form_instance = forms.RegistrationForm(request.POST)
        if form_instance.is_valid():
            form_instance.save()
            return redirect("/login/")
    else:
        form_instance = forms.RegistrationForm()
    context = {
        "form":form_instance,
    }
    return render(request, "registration/register.html", context=context)

@login_required(login_url='/login/')
def search(request):
    br = models.Wine.objects.all().order_by('-id')
    b = request.GET.get('b','')
    if b:
        br = br.filter(title__icontains=b) | br.filter(winery__icontains=b)
    paginator = Paginator(br, 12)
    page = request.GET.get('page')
    br = paginator.get_page(page)
    totalQ = models.Wine.objects.all().count()
    context = {
        "title":"Best Bottle",
        "search":br,
        "b":b,
        "page":page,
        "paginator":paginator,
        "totalQ":totalQ,
    }
    return render(request, 'search.html', context)

@login_required(login_url='/login/')
def wine_info(request, wine_id):
    wine = models.Wine.objects.get(id=wine_id)
    try:
        my_rate = models.Rating.objects.get(wine=wine_id, user=request.user)
        avg_rate = models.Rating.objects.filter(wine=wine_id) \
                .values('wine') \
                .annotate(Avg('rating'))[0]['rating__avg']
    except models.Rating.DoesNotExist:
        my_rate = None
        avg_rate = 0
    rate_stacked = models.Rating.objects.filter(wine=wine_id).count()
    predicted_rate = models.Wine.objects.filter(id=wine_id) \
                .values('points')[0]['points'] / 20
    context = {
        "title":"Best Bottle",
        "wine":wine,
        "my_rate":my_rate,
        "rate_stacked":rate_stacked,
        "avg_rate":avg_rate,
        "predicted_rate":predicted_rate,
    }
    return render(request, 'wine_info.html', context)

@login_required(login_url='/login/')
def mypage(request):
    rated_wine_queryset = models.Rating.objects.filter(user=request.user)
    wines = models.Wine.objects.filter(pk__in=rated_wine_queryset)
    totalRatedWines = wines.count()
    rate = rated_wine_queryset.filter(pk__in=rated_wine_queryset)
    avg_rate = rated_wine_queryset.filter(pk__in=rated_wine_queryset) \
                .values('wine') 
                # \
                # .annotate(Avg('rating'))[0]['rating__avg']
    context = {
        "title":"Best Bottle",
        "wines":wines,
        "totalRatedWines":totalRatedWines,
        "rate":rate,
        "avg_rate":avg_rate,
    }
    return render(request, 'mypage.html', context)

def ratingWine(request, rate, wine_id):
    wine = models.Wine.objects.get(id=wine_id)
    if rate == 0:
        query = models.Rating.objects.get(wine=wine,user=request.user)
        query.delete()
    else:
        obj, created = models.Rating.objects.update_or_create(
            user=request.user, wine=wine, rating=rate
        )
    return redirect("/wine_info/"+ str(wine_id) + "/")