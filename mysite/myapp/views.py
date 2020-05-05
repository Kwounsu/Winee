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
from random import randint
from . import models
from . import forms

# Create your views here.
def index(request):
    # Rating stacked total
    rate_stacked_count = models.Rating.objects.all().count()
    if rate_stacked_count >= 1000 and rate_stacked_count < 1000000:
        rate_stacked_count /= 1000
        rate_stacked = str(rate_stacked_count) + 'K'
    elif rate_stacked_count >= 1000000 and rate_stacked_count < 1000000000:
        rate_stacked_count /= 1000000
        rate_stacked = str(rate_stacked_count) + 'M'
    else:
        rate_stacked = rate_stacked_count
    
    # Trending wines / Wine Recommendation
    wines = models.Wine.objects.all().order_by('-rate_stacked')[:10]
    top_one_rate = 0
    top_two_rate = 0
    top_three_rate = 0
    top_one_wine = []
    top_two_wine = []
    top_three_wine = []
    for wine in wines:
        # Get predicted rate
        predicted_rate = 0
        if rate_stacked_count > 0:
            predicted_rate = getPredictRate(request.user.id, wine.id)
        if predicted_rate == 0 or predicted_rate > 5:
            predicted_rate = models.Wine.objects.filter(id=wine.id).values('points')[0]['points'] / 20
        if top_three_rate < predicted_rate:
            if top_two_rate < predicted_rate:
                if top_one_rate < predicted_rate:
                    top_three_rate = top_two_rate
                    top_two_rate = top_one_rate
                    top_one_rate = predicted_rate
                    recommending_wine = models.Wine.objects.get(id=wine.id)
                    top_one_wine.clear()
                    top_one_wine.append(recommending_wine)
                else:
                    top_three_rate = top_two_rate
                    top_two_rate = predicted_rate
                    recommending_wine = models.Wine.objects.get(id=wine.id)
                    top_two_wine.clear()
                    top_two_wine.append(recommending_wine)
            else:
                top_three_rate = predicted_rate
                recommending_wine = models.Wine.objects.get(id=wine.id)
                top_three_wine.clear()
                top_three_wine.append(recommending_wine)
    recommending_wines = top_one_wine + top_two_wine + top_three_wine
    
    context = {
        "title":"Best Bottle",
        "rate_stacked":rate_stacked,
        "wines":recommending_wines,
    }
    return render(request, "index.html", context=context)

def logout_view(request):
    logout(request)
    return redirect("/")

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
    wishlists_queryset = models.WishList.objects.filter(user=request.user)
    wishlists = wishlists_queryset.filter(pk__in=wishlists_queryset)
    wishlistsNum = wishlists_queryset.count()
    totalRatedWines = wines.count()

    paginator = Paginator(rates, 12)
    page = request.GET.get('page')
    br = paginator.get_page(page)
    context = {
        "title":"Best Bottle",
        "wines":wines,
        "totalRatedWines":totalRatedWines,
        "rates":rates,
        "page":page,
        "paginator":paginator,
        "wishlists":wishlists,
        "wishlistsNum":wishlistsNum,
        "search":br,
    }
    return render(request, 'mypage.html', context)

@login_required(login_url='/login/')
def wine_info(request, wine_id):
    wine = models.Wine.objects.get(id=wine_id)

    # My Rate
    try:
        my_rate = models.Rating.objects.get(wine=wine_id, user=request.user)
    except models.Rating.DoesNotExist:
        my_rate = None
    try:
        avg_rate = models.Rating.objects.filter(wine=wine_id) \
            .values('wine') \
            .annotate(Avg('rating'))[0]['rating__avg']
    except:
        avg_rate = 0
    temp_predicted_rate = models.Wine.objects.filter(id=wine_id) \
                .values('points')[0]['points'] / 20
    predicted_rate = temp_predicted_rate

    # Rate Stacked
    rate_stacked_count = models.Rating.objects.filter(wine=wine_id).count()
    if rate_stacked_count >= 1000 and rate_stacked_count < 1000000:
        rate_stacked_count /= 1000
        rate_stacked = str(rate_stacked_count) + 'K'
    elif rate_stacked_count >= 1000000 and rate_stacked_count < 1000000000:
        rate_stacked_count /= 1000000
        rate_stacked = str(rate_stacked_count) + 'M'
    else:
        rate_stacked = rate_stacked_count
    
    # Predicted Rate
    if rate_stacked_count > 0:
        predicted_rate = getPredictRate(request.user.id, wine_id)
    if predicted_rate == 0:
        predicted_rate = temp_predicted_rate
    
    # WishList
    try:
        boolWishList = models.WishList.objects.get(wine=wine_id, user=request.user)
    except models.WishList.DoesNotExist:
        boolWishList = 0

    # Rating Chart
    Ones = 0
    Twos = 0
    Theres = 0
    Fours = 0
    Fives = 0

    ratingQS = models.Rating.objects.filter(wine=wine_id)
    for i in ratingQS:
        if int(i.rating) == 1:
            Ones += 1
        elif int(i.rating) == 2:
            Twos += 1
        elif int(i.rating) == 3:
            Theres += 1
        elif int(i.rating) == 4:
            Fours += 1
        elif int(i.rating) == 5:
            Fives += 1
    chart = [Ones, Twos, Theres, Fours, Fives]
    context = {
        "title":"Best Bottle",
        "wine":wine,
        "my_rate":my_rate,
        "rate_stacked":rate_stacked,
        "avg_rate":avg_rate,
        "temp_predicted_rate":temp_predicted_rate,
        "predicted_rate":predicted_rate,
        "boolWishList":boolWishList,
        "chart":chart,
    }
    return render(request, 'wine_info.html', context)

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
    result = 0
    try:
        result = (sumXY - ((sumX * sumY) / count)) / sqrt((sumPowX - (pow(sumX, 2) / count)) * (sumPowY - (pow(sumY, 2) / count)))
    except:
        pass
    return result

def getPredictRate(theUser, theWine, sim_function=sim_pearson):
    ratings = models.Rating.objects.filter(wine=theWine)
    users = User.objects.filter(pk__in=ratings.values('user_id'))
    predicted_rate = 0
    sumR = 0
    for i in users:
        if theUser != i.id:
            r = sim_function(theUser, i.id)
            simRatingObj = models.Rating.objects.get(wine=theWine, user=i.id)
            predicted_rate += r * simRatingObj.rating
            sumR += r
    if sumR == 0:
        predicted_rate = 0
    else:
        predicted_rate /= sumR
    return predicted_rate

def ratingWine(request, rate, wine_id):
    wine = models.Wine.objects.get(id=wine_id)
    if rate == 0:
        query = models.Rating.objects.get(wine=wine, user=request.user)
        query.delete()
        wine.rate_stacked -= 1
        wine.save()
    else:
        try:
            query = models.Rating.objects.get(wine=wine, user=request.user)
            query.delete()
        except:
            pass
        obj, created = models.Rating.objects.update_or_create(
            user=request.user, wine=wine, rating=rate
        )
        wine.rate_stacked += 1
        wine.save()
    return redirect("/wine_info/"+ str(wine_id) + "/")

def AddWishList(request, wine_id):
    wine = models.Wine.objects.get(id=wine_id)
    obj, created = models.WishList.objects.update_or_create(
        wine=wine, user=request.user
    )
    return redirect("/wine_info/"+ str(wine_id) + "/")

def DelWishList(request, wine_id):
    wine = models.Wine.objects.get(id=wine_id)
    query = models.WishList.objects.get(wine=wine, user=request.user)
    query.delete()
    return redirect("/wine_info/"+ str(wine_id) + "/")