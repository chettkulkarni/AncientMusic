
# encoding: utf-8
import json
# from django.http import HttpResponse, HttpResponseRedirect
# from django.views.generic import CreateView, DeleteView, ListView, DetailView
from django.views.decorators.csrf import csrf_exempt
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import re

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

import math

# s3 upload
import tinys3


# conversion wav to png

import librosa
import numpy as np

import os

#import mongo
import pymongo


# import config

from .conf import ACCESS_KEY, SECRET_KEY, settings

@login_required(login_url='login')
@csrf_exempt
def selectRaga(request):
    username = request.user.username


    if request.method == 'POST':
        ragaType = request.POST.get('raga')
        print(ragaType)

        context = {
            'ragaType' : ragaType
        }
        return render(request,'uploadMethod.html', context)

    context = {

    }
    return render(request, 'selectRaga.html', context)


# @login_required(login_url='login')
# @csrf_exempt
def index(request):
    return render(request, 'index.html')


@login_required(login_url='login')
@csrf_exempt
def uploadRaga(request):
    username = request.user.username

    if request.method == 'POST':
        # ragaType = request.POST.get('senderSong')
        # print(ragaType)
        # audio_data = request.FILES.get('data')
        # path = default_storage.save('123' + '.mp3', ContentFile(audio_data.read()))
        # audio_data = request.FILES['data']
        # print(audio_data)

        # print('bossssss',request.POST.get('selectedRaga'))

        context = {}

        songname = 'mysong.mp3'
        print("header", request.headers)
        print(request)

        with open(songname, mode='wb') as f:
            f.write(request.body)

        f = open(songname, mode='rb')

        try:
            fileName = request.FILES['mySong'].name
        except:
            fileName = 'recorded'

        fileName = re.sub('\W+', '', fileName) + '.mp3'

        conn = tinys3.Connection(ACCESS_KEY, SECRET_KEY, tls=True)
        conn.upload(username + '/' + fileName, f, 'musictutor-storage')

        # sending s3 link to prediction microservice.
        songLink = 'https://musictutor-storage.s3.amazonaws.com/' + username + '/' + fileName

        def predict_raga(fp):
            # class_names = ['Khamaj', 'Lalit', 'Malkauns']
            class_names = ['Des Raga',
                           'Bhairavi Raga',
                           'Bilaskhani todi Raga',
                           'Bageshree Raga',
                           'Ahira Bhairav Raga']

            # y, sr = librosa.load(fp, res_type='kaiser_best')

            # mfcc = librosa.feature.mfcc(y=y, sr=22050, hop_length=512, n_mfcc=13)
            # mfcc = mfcc.T

            SAMPLE_RATE = 22050
            TRACK_DURATION = 30  # measured in seconds
            SAMPLES_PER_TRACK = SAMPLE_RATE * TRACK_DURATION
            num_segments = 10
            hop_length = 512
            num_mfcc = 13
            sample_rate = 22050
            n_fft = 2048

            samples_per_segment = int(SAMPLES_PER_TRACK / num_segments)
            signal, sample_rate = librosa.load(fp, res_type='kaiser_best', sr=SAMPLE_RATE)

            data = {
                "mfcc": []
            }
            predictions_list = []

            for d in range(num_segments):
                # calculate start and finish sample for current segment
                start = samples_per_segment * d
                finish = start + samples_per_segment

                # extract mfcc
                mfcc = librosa.feature.mfcc(signal[start:finish], sample_rate, n_mfcc=num_mfcc, n_fft=n_fft,
                                            hop_length=hop_length)
                mfcc = mfcc.T

                data["mfcc"].append(mfcc.tolist())

            for i in data['mfcc']:
                X = np.array(i)
                X = X.reshape(1, X.shape[0], X.shape[1])
                # X=[X]
                # print(X.shape)

                data_x = json.dumps({"signature_name": "serving_default", "instances": X.tolist()})
                # print('Data: {} ... {}'.format(data[:50], data[len(data) - 52:]))

                headers = {"content-type": "application/json"}
                json_response = requests.post('http://34.122.53.110:8501/v1/models/classify_raga:predict', data=data_x,
                                              headers=headers)

                predictions = json.loads(json_response.text)['predictions']

                predictions_list.append(np.argmax(predictions))

            final = max(predictions_list, key=predictions_list.count)
            final_prec = str((predictions_list.count(final) / len(predictions_list)) * 100) + '%'
            print(final, final_prec)

            return (class_names[final], final_prec)

        # predict the raga and confidence score using the tensorflow serving model

        raga, confidence = predict_raga('mysong.mp3')

        context["raga"] = raga

        context["confidence"] = confidence

        context["selectedRaga"] = request.POST.get('selectedRaga')

        # send the data to mongo db

        # username, song name, song link, predicted raga, predicted confidence score

        mongodbUrl = settings['mongoUrl']
        db = settings['database']
        col = settings['songCol']

        myclient = pymongo.MongoClient(mongodbUrl)
        mydb = myclient[db]
        mycol = mydb[col]

        doc = {"username": username, "fileName": fileName, "songLink": songLink, "predictedRaga": raga,
               "confidenceScore": confidence}

        try:
            mycol.insert_one(doc)
        except:
            print('failed to add details into db')

        return render(request, 'result.html', context)

    context = {

    }
    return render(request, 'selectRaga.html', context)




#get recommendations

@login_required(login_url='login')
@csrf_exempt
def getRecommendations(request):
    username = request.user.username
    context = {}

    if request.method == 'POST':
        ragaType = request.POST.get('raga','Bhairavi Raga')
        selectedRagaType = request.POST.get('selectedRaga', 'Bhairavi Raga')
        confidence = request.POST.get('confidence', '0%')

        print(ragaType,selectedRagaType)

        mongodbUrl = settings['mongoUrl']
        db = settings['database']
        # col = settings['songCol']
        col = 'recommendations'


        myclient = pymongo.MongoClient(mongodbUrl)
        mydb = myclient[db]
        mycol = mydb[col]

        query = {"ragaType":ragaType}

        ragaRecommendations  = []
        try:
            result = mycol.find(query)
            print("result", result)
            
        except:
            result = ['']

        for i in result:
            ragaRecommendations = i['songs']
        context['ragaRecommendations'] = ragaRecommendations

        selectedRagaTypeQuery = {"ragaType": selectedRagaType}

        selectedRagaRecommendations = []
        try:
            selectedRagaResult = mycol.find(selectedRagaTypeQuery)
        except:
            selectedRagaResult = ['']
        

        for i in selectedRagaResult:
            selectedRagaRecommendations = i['songs']
        context['selectedRagaRecommendations'] = selectedRagaRecommendations
        context['raga'] = ragaType
        context['selectedRaga'] = selectedRagaType
        context['confidence'] = confidence


        print(context)
        return render(request,'result.html', context)


@login_required(login_url='login')
@csrf_exempt
def recordSong(request):
    username = request.user.username

    if request.method == 'POST':
        context = {}
        songname = 'mysong.wav'
        file_x = request.FILES.get('data')
        with open(songname, mode='wb') as f:
            f.write(file_x.read())
        f.close()

    return ''

@login_required(login_url='login')
@csrf_exempt
def processRecord(request):
    username = request.user.username

    if request.method == 'POST':
        songname = 'mysong.wav'

        f = open(songname, mode='rb')


        conn = tinys3.Connection(ACCESS_KEY, SECRET_KEY, tls=True)
        conn.upload(username + '/' + songname, f, 'musictutor-storage')

        # sending s3 link to prediction microservice.
        songLink = 'https://musictutor-storage.s3.amazonaws.com/' + username + '/' + songname



        def predict_raga(fp):
            # class_names = ['Khamaj', 'Lalit', 'Malkauns']
            print(fp)
            class_names = ['Des Raga',
                           'Bhairavi Raga',
                           'Bilaskhani todi Raga',
                           'Bageshree Raga',
                           'Ahira Bhairav Raga']


            # y, sr = librosa.load(fp, res_type='kaiser_best')

            # mfcc = librosa.feature.mfcc(y=y, sr=22050, hop_length=512, n_mfcc=13)
            # mfcc = mfcc.T

            SAMPLE_RATE = 22050
            TRACK_DURATION = 30  # measured in seconds
            SAMPLES_PER_TRACK = SAMPLE_RATE * TRACK_DURATION
            num_segments=10
            hop_length = 512
            num_mfcc = 13
            sample_rate = 22050
            n_fft = 2048





            samples_per_segment = int(SAMPLES_PER_TRACK / num_segments)
            signal, sample_rate = librosa.load(fp, res_type='kaiser_best',sr=SAMPLE_RATE)

            song_duration = librosa.get_duration(y=signal, sr=sample_rate)

            if song_duration < 35:
                return None, 0

            data = {
                "mfcc": []
            }
            predictions_list = []

            for d in range(num_segments):
                # calculate start and finish sample for current segment
                start = samples_per_segment * d
                finish = start + samples_per_segment


                # extract mfcc
                mfcc = librosa.feature.mfcc(signal[start:finish], sample_rate, n_mfcc=num_mfcc, n_fft=n_fft,
                                            hop_length=hop_length)
                mfcc = mfcc.T

                data["mfcc"].append(mfcc.tolist())






            for i in data['mfcc']:
                X = np.array(i)
                X = X.reshape(1,X.shape[0],X.shape[1])
                # X=[X]
                # print(X.shape)


                data_x = json.dumps({"signature_name": "serving_default", "instances": X.tolist()})
                # print('Data: {} ... {}'.format(data[:50], data[len(data) - 52:]))

                headers = {"content-type": "application/json"}
                json_response = requests.post('http://34.122.53.110:8501/v1/models/classify_raga:predict', data=data_x,
                                              headers=headers)


                predictions = json.loads(json_response.text)['predictions']



                predictions_list.append(np.argmax(predictions))


            final=max(predictions_list, key=predictions_list.count)
            final_prec= str((predictions_list.count(final)/len(predictions_list))*100)+'%'
            print(final,final_prec)


            return (class_names[final],final_prec)

        # predict the raga and confidence score using the tensorflow serving model

        raga, confidence = predict_raga(songname)

        if raga is None:
            context = {
                "message": "Please record the song for more than 35 seconds!"
            }
            return redirect('/')
        context = {}

        context["raga"] = raga

        context["confidence"] = confidence

        context["selectedRaga"] = request.POST.get('selectedRaga')

        # send the data to mongo db

        # username, song name, song link, predicted raga, predicted confidence score

        mongodbUrl = settings['mongoUrl']
        db = settings['database']
        col = settings['songCol']

        myclient = pymongo.MongoClient(mongodbUrl)
        mydb = myclient[db]
        mycol = mydb[col]

        doc = {"username": username, "fileName": songname, "songLink": songLink, "predictedRaga": raga,
               "confidenceScore": confidence}

        try:
            mycol.insert_one(doc)
        except:
            print('failed to add details into db')

        return render(request, 'result.html', context)

    context = {

    }
    return render(request, 'selectRaga.html', context)








