from django.shortcuts import render
from django.http import HttpResponse

def hello(requests):
    return render(requests, "home.html")
def world(requests):
    return render(requests, "world.html")