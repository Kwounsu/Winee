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
    br = models.Wine.objects.all().order_by('-points')
    b = request.GET.get('b','')
    if b:
        br = br.filter(title__icontains=b) | br.filter(winery__icontains=b)
    paginator = Paginator(br, 6)
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
    l1=list(rate)
    l2=list(avg_rate)
    context = {
        "title":"Best Bottle",
        "wines":wines,
        "totalRatedWines":totalRatedWines,
        "rate":rate,
        "avg_rate":avg_rate,
        "l1":l1,
        "l2":l2,
    }
    return render(request, 'mypage.html', context)

@permission_required('admin.can_add_log_entry')
def wine_upload(request):
    template = "wine_upload.html"

    prompt = {
        'order': 'Order of the CSV does matter'
    }

    if request.method == "GET":
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'This is not a csv file')

    data_set = csv_file.read().decode('unicode_escape')
    # data_set = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar='|'):
        _, created = models.Wine.objects.update_or_create(
            country=column[0],
            description=column[1],
            points=column[2],
            price=column[3],
            province=column[4],
            title=column[5],
            variety=column[6],
            winery=column[7],
        )

    context = {}
    return render(request, template, context)