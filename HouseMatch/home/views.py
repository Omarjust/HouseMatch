from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Empresa, Etiqueta, Inmueble, PerfilAsesor, Usuario


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


def registro(request):
    if request.user.is_authenticated:
        return redirect('home:index')

    empresas = Empresa.objects.all().order_by('nombre')

    if request.method == 'POST':
        nombre             = request.POST.get('nombre', '').strip()
        username           = request.POST.get('username', '').strip()
        email              = request.POST.get('email', '').strip().lower()
        password1          = request.POST.get('password1', '')
        password2          = request.POST.get('password2', '')
        es_asesor          = request.POST.get('es_asesor') == 'on'
        empresa_id         = request.POST.get('empresa_id', '').strip()
        id_asesor_externo  = request.POST.get('id_asesor_externo', '').strip()

        errores = []
        if not nombre:
            errores.append('El nombre es obligatorio.')
        if not email:
            errores.append('El email es obligatorio.')
        elif Usuario.objects.filter(email=email).exists():
            errores.append('Ya existe una cuenta con ese email.')
        if len(password1) < 8:
            errores.append('La contraseña debe tener al menos 8 caracteres.')
        if password1 != password2:
            errores.append('Las contraseñas no coinciden.')

        if errores:
            return render(request, 'home/registro.html', {
                'errores': errores,
                'nombre': nombre,
                'username': username,
                'email': email,
                'es_asesor': es_asesor,
                'empresa_id': empresa_id,
                'id_asesor_externo': id_asesor_externo,
                'empresas': empresas,
            })

        user = Usuario(
            email=email,
            username=username or None,
            first_name=nombre,
            is_asesor=es_asesor,
        )
        user.set_password(password1)
        user.save()

        if es_asesor:
            empresa = Empresa.objects.filter(pk=empresa_id).first() if empresa_id else None
            PerfilAsesor.objects.create(
                user=user,
                empresa=empresa,
                id_asesor_externo=id_asesor_externo or None,
            )

        auth_login(request, user)
        return redirect('home:mapa')

    return render(request, 'home/registro.html', {'empresas': empresas})


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
