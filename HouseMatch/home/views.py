from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render


def home(request):
    return render(request, 'home/home.html')


def pricing(request):
    return render(request, 'home/pricing.html')


def mapa(request):
    return render(request, 'home/mapa.html')


def login(request):
    if request.user.is_authenticated:
        return redirect('home:index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect(next_url or 'home:mapa')
        return render(request, 'home/login.html', {
            'error': 'Email o contraseña incorrectos.',
            'email': email,
            'next': next_url,
        })

    return render(request, 'home/login.html', {'next': request.GET.get('next', '')})


def logout(request):
    auth_logout(request)
    return redirect('home:index')
