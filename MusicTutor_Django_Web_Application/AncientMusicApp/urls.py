"""AncientMusicApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from general import views, interactiveViews

from django.conf.urls import url

urlpatterns = [


    path('admin/', admin.site.urls),
    # path('', views.home, name='home'),
    path('uploads', views.uploads, name='uploads'),

    path('chat/', include('chat.urls')),



    #interactive paths
    path('', interactiveViews.selectRaga, name='home'),
    # path('index', interactiveViews.index, name='index'),
    path('selectRaga', interactiveViews.selectRaga),

    path('uploadSong', interactiveViews.uploadRaga, name='uploadSong'),
    path('recordSong', interactiveViews.recordSong, name='recordSong'),
    path('processRecord', interactiveViews.processRecord, name='processRecord'),


    path('getRecommendations', interactiveViews.getRecommendations, name='getRecommendations'),


    #song prediction
    # path('songPred', views.predict_song),

    # user management
    # login
    path('login/', views.loginPage, name="login"),
    # register
    path('register/', views.registerPage, name='register'),
    # logout
    path('logout/', views.logoutUser, name='logout'),

]
