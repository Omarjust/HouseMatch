
from django.db import models
from django.contrib.auth.models import AbstractUser

class Empresa(models.Model):
    nombre = models.CharField(max_length=100) # Ej: Century 21, Remax
    
    def __str__(self):
        return self.nombre

class Usuario(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    email = models.EmailField(unique=True)

    
    # Campo para identificar al asesor
    is_asesor = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class PerfilAsesor(models.Model):
    user = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    id_asesor_externo = models.CharField(max_length=50, blank=True, null=True)
    es_century = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.empresa}"



class TipoPropiedad(models.Model):
    nombre = models.CharField(max_length=50) # Casa, Dpto, Quinta

    def __str__(self):
        return self.nombre

class TipoTransaccion(models.Model):
    nombre = models.CharField(max_length=50) # Venta, Alquiler

    def __str__(self):
        return self.nombre

class Departamento(models.Model):
    nombre = models.CharField(max_length=50) # Santa Cruz, La Paz

    def __str__(self):
        return self.nombre

class Inmueble(models.Model):
    # Relaciones
    asesor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='inmuebles')
    tipo_propiedad = models.ForeignKey(TipoPropiedad, on_delete=models.PROTECT)
    tipo_transaccion = models.ForeignKey(TipoTransaccion, on_delete=models.PROTECT)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)

    # Detalles
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    # Características
    cant_cuartos = models.PositiveIntegerField()
    cant_banios = models.PositiveIntegerField()
    area_construida = models.DecimalField(max_digits=10, decimal_places=2)
    area_terreno = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Precios
    precio_usd = models.DecimalField(max_digits=12, decimal_places=2)
    precio_bs = models.DecimalField(max_digits=12, decimal_places=2)

    # Ubicación y Fotos
    calle = models.CharField(max_length=255)
    zona = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    url_image = models.URLField(max_length=500, help_text="URL de la foto principal")
    url_propiedad = models.URLField(max_length=500, help_text="URL de la foto principal",default='', blank=True)

    # Boleanos
    parqueo = models.BooleanField(default=False)
    piscina = models.BooleanField(default=False)
    permite_mascotas = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titulo} - {self.precio_usd}$"