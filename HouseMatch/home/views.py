from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Etiqueta, Inmueble


def home(request):
    return render(request, 'home/home.html')


def pricing(request):
    return render(request, 'home/pricing.html')


def mapa(request):
    user = request.user
    if not user.is_authenticated:
        login_url = reverse('home:login')
        return redirect(f'{login_url}?next={request.path}')
    if user.is_staff or user.is_superuser or user.plan_activo:
        return render(request, 'home/mapa.html')
    return redirect('home:pricing')


def etiquetas(request):
    user = request.user
    if not user.is_authenticated:
        login_url = reverse('home:login')
        return redirect(f'{login_url}?next={request.path}')
    if not (user.is_staff or user.is_superuser or user.plan_activo):
        return redirect('home:pricing')
    qs = (
        Etiqueta.objects
        .filter(usuario=user)
        .prefetch_related('guardados__inmueble')
        .order_by('nombre')
    )
    return render(request, 'home/etiquetas.html', {'etiquetas': qs})


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


def detalle_inmueble(request, pk):
    inmueble = get_object_or_404(
        Inmueble.objects
        .select_related('tipo_propiedad', 'tipo_transaccion', 'departamento')
        .prefetch_related('imagenes'),
        pk=pk,
        activo=True,
    )
    return render(request, 'home/inmueble_detalle.html', {'inmueble': inmueble})
