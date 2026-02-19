from django.shortcuts import render


def home(request):
    return render(request, 'home/home.html')


def pricing(request):
    return render(request, 'home/pricing.html')


def mapa(request):
    return render(request, 'home/mapa.html')
