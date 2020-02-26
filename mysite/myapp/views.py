import csv, io

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Subquery
from math import sqrt

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
def mypage(request):
    rated_wine_queryset = models.Rating.objects.filter(user=request.user)
    wines = models.Wine.objects.filter(pk__in=rated_wine_queryset.values('wine_id'))
    rates = rated_wine_queryset.filter(pk__in=rated_wine_queryset).select_related('wine').order_by('-rating')
    totalRatedWines = wines.count()
    paginator = Paginator(wines, 12)
    page = request.GET.get('page')
    wines = paginator.get_page(page)
    context = {
        "title":"Best Bottle",
        "wines":wines,
        "totalRatedWines":totalRatedWines,
        "rates":rates,
        "page":page,
        "paginator":paginator,
    }
    return render(request, 'mypage.html', context)

@login_required(login_url='/login/')
def wine_info(request, wine_id):
    wine = models.Wine.objects.get(id=wine_id)
    try:
        my_rate = models.Rating.objects.get(wine=wine_id, user=request.user)
    except models.Rating.DoesNotExist:
        my_rate = None
    avg_rate_list = models.Rating.objects.filter(wine=wine_id)
    avg_rate = 0
    count = 0
    for i in avg_rate_list:
        avg_rate += i.rating
        count += 1
    if count > 0:
        avg_rate = avg_rate / count
    # avg_rate = models.Rating.objects.filter(wine=wine_id) \
    #         .values('wine') \
    #         .annotate(Avg('rating'))[0]['rating__avg']
    rate_stacked = models.Rating.objects.filter(wine=wine_id).count()
    temp_predicted_rate = models.Wine.objects.filter(id=wine_id) \
                .values('points')[0]['points'] / 20
    predicted_rate = temp_predicted_rate
    if rate_stacked > 2:
        predicted_rate = getPredictRate(request.user.id, wine_id)
    context = {
        "title":"Best Bottle",
        "wine":wine,
        "my_rate":my_rate,
        "rate_stacked":rate_stacked,
        "avg_rate":avg_rate,
        "temp_predicted_rate":temp_predicted_rate,
        "predicted_rate":predicted_rate,
    }
    return render(request, 'wine_info.html', context)

def ratingWine(request, rate, wine_id):
    wine = models.Wine.objects.get(id=wine_id)
    if rate == 0:
        query = models.Rating.objects.get(wine=wine, user=request.user)
        query.delete()
    else:
        obj, created = models.Rating.objects.update_or_create(
            user=request.user, wine=wine, rating=rate
        )
    return redirect("/wine_info/"+ str(wine_id) + "/")

def sim_pearson(reqUser, user2):
    sumX = 0        # sum of X
    sumY = 0        # sum of Y
    sumPowX = 0     # sum of power of X
    sumPowY = 0     # sum of power of Y
    sumXY = 0       # sum of X*Y
    user1rates = models.Rating.objects.filter(user_id=reqUser) # user1's rating list
    user2rates = models.Rating.objects.filter(user_id=user2) # user2's rating list
    der_user1 = user1rates.filter(wine_id__in=Subquery(user2rates.values('wine_id')))
    der_user2 = user2rates.filter(wine_id__in=Subquery(user1rates.values('wine_id')))
    count = der_user1.count() # num of wines
    if count < 2:
        return 0
    for d_user1 in der_user1.iterator():
        sumX += d_user1.rating
        sumPowX += pow(d_user1.rating, 2)
        for d_user2 in der_user2.iterator():
            if d_user2.wine_id == d_user1.wine_id:
                sumXY += d_user1.rating * d_user2.rating
    for d_user2 in der_user2.iterator():
        sumY += d_user2.rating
        sumPowY += pow(d_user2.rating, 2)
    return (sumXY - ((sumX * sumY) / count)) / sqrt((sumPowX - (pow(sumX, 2) / count)) * (sumPowY - (pow(sumY, 2) / count)))

def getPredictRate(theUser, theWine, sim_function=sim_pearson):
    ratings = models.Rating.objects.filter(wine=theWine)
    users = User.objects.filter(pk__in=ratings.values('user_id'))
    topSim = -1
    simRateScore = 0
    simUser = users[0].id
    predicted_rate = 0
    count=0
    for i in users:
        if theUser != i.id:
            r = sim_function(theUser, i.id)
            simRatingObj = models.Rating.objects.get(wine=theWine, user=i.id)
            if r < 0:
                predicted_rate += (1+r) * simRatingObj.rating
            else:
                predicted_rate += r * simRatingObj.rating
            count += 1
    predicted_rate /= count
    #     if topSim < r:
    #         topSim = r
    #         simUser = i.id
    # simRatingObj = models.Rating.objects.get(wine=theWine, user=simUser)
    # if topSim < 0:
    #     predicted_rate = (1+topSim) * simRatingObj.rating
    # else:
    #     predicted_rate = topSim * simRatingObj.rating
    return predicted_rate

# def getPredictRate(request, theWine, sim_function=sim_pearson):
#     ratings = models.Rating.objects.filter(wine=theWine)
#     users = User.objects.filter(pk__in=ratings.values('user_id'))
#     topSim = -1
#     simRateScore = 0
#     simUser = users[0].id
#     testlist=[1,2]
#     testlist.clear()
#     for i in users:
#         if request.user.id != i.id:
#             r = sim_function(request.user.id, i.id)
#             testlist.append(r)
#         if topSim < r:
#             topSim = r
#             simUser = i.id
#     simRatingObj = models.Rating.objects.get(wine=theWine, user=simUser)
#     predicted_rate = (abs(topSim) * simRatingObj.rating)

#     try:
#         my_rate = models.Rating.objects.get(wine=theWine, user=request.user)
#         avg_rate = models.Rating.objects.filter(wine=theWine) \
#                 .values('wine') \
#                 .annotate(Avg('rating'))[0]['rating__avg']
#     except models.Rating.DoesNotExist:
#         my_rate = None
#         avg_rate = 0
    
#     context = {
#         "topSim":topSim,
#         "simUser":simUser,
#         "simRateScore":simRateScore,
#         "predicted_rate":predicted_rate,
#         "my_rate":my_rate,
#         "avg_rate":avg_rate,
#         "r":r,
#         "testlist":testlist,
#     }
#     return render(request, 'test.html', context)

# def getPredictRate(request, theWine, user2):
#     sumX = 0        # sum of X
#     sumY = 0        # sum of Y
#     sumPowX = 0     # sum of power of X
#     sumPowY = 0     # sum of power of Y
#     sumXY = 0       # sum of X*Y
#     user1rates = models.Rating.objects.filter(user=request.user)    # user1's rating list
#     user2rates = models.Rating.objects.filter(user_id=user2)        # user2's rating list
#     der_user1 = user1rates.filter(wine_id__in=Subquery(user2rates.values('wine_id'))).order_by('wine_id')
#     der_user2 = user2rates.filter(wine_id__in=Subquery(user1rates.values('wine_id'))).order_by('wine_id')
#     count = der_user1.count() # num of wines
#     if count < 2:
#         return 0
#     for d_user1 in der_user1.iterator():
#         sumX += d_user1.rating
#         sumPowX += pow(d_user1.rating, 2)
#         for d_user2 in der_user2.iterator():
#             if d_user2.wine_id == d_user1.wine_id:
#                 sumXY += d_user1.rating * d_user2.rating
#     for d_user2 in der_user2.iterator():
#         sumY += d_user2.rating
#         sumPowY += pow(d_user2.rating, 2)
#     r = (sumXY - ((sumX * sumY) / count)) / sqrt((sumPowX - (pow(sumX, 2) / count)) * (sumPowY - (pow(sumY, 2) / count)))
#     somerate = user2rates.get(wine=theWine)
#     pred_rate = abs(r) * somerate.rating
#     context = {
#         "pred_rate":pred_rate,
#         "user2":user2,
#         "r":r,
#         "user1rates":user1rates,
#         "user2rates":user2rates,
#         "der_user1":der_user1,
#         "der_user2":der_user2,
#         "sumXY":sumXY,
#         "sumX":sumX,
#         "sumY":sumY,
#         "sumPowX":sumPowX,
#         "sumPowY":sumPowY,
#         "count":count,
#     }
#     return render(request, 'test.html', context)