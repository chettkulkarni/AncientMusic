from django.shortcuts import render
# encoding: utf-8
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import requests
from django.shortcuts import render, redirect

from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

import os

# conversion wav to png

from .conf import ACCESS_KEY, SECRET_KEY, settings

#import mongo
import pymongo

# Create your views here.

access_key = ACCESS_KEY
secret_key = SECRET_KEY



@login_required(login_url='login')
def uploads(request):

    # print('inside uploads view')

    username = request.user.username

    #get docs from mongodb - songs collection
    mongodbUrl = settings['mongoUrl']
    db = settings['database']
    col = settings['songCol']

    myclient = pymongo.MongoClient(mongodbUrl)
    mydb = myclient[db]
    mycol = mydb[col]

    songList = []

    myquery = { "username": username }
    for x in mycol.find(myquery):
        print(x)
        songList.append(x)

    context = {
        'songList': songList,
        'username': username
    }

    return render(request, 'uploads.html', context)




# user management

# user login
@csrf_exempt
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'username or password is incorrect')

        context = {

        }
        return render(request, 'login.html', context)


# register user
@csrf_exempt
def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()

        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for :' + user)
                return redirect('login')
        context = {
            'form': form
        }
        return render(request, 'register.html', context)


# user logout
@csrf_exempt
def logoutUser(request):
    logout(request)
    return redirect('login')
