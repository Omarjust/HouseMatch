
from django.db import models
from django.contrib.auth.models import AbstractUser

class Empresa(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Usuario(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    email = models.EmailField(unique=True)
    is_asesor = models.BooleanField(default=True)
    fecha_vencimiento_plan = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def plan_activo(self):
        """True si is_active=True Y la fecha de vencimiento no ha pasado."""
        from datetime import date
        if not self.is_active:
            return False
        if self.fecha_vencimiento_plan is None:
            return False
        return self.fecha_vencimiento_plan >= date.today()

    def __str__(self):
        return self.email


class PerfilAsesor(models.Model):
    user = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    id_asesor_externo = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.empresa}"


class TipoPropiedad(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class TipoTransaccion(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Departamento(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Inmueble(models.Model):
    # Relaciones (sin asesor FK)
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_propiedad = models.ForeignKey(TipoPropiedad, on_delete=models.PROTECT)
    tipo_transaccion = models.ForeignKey(TipoTransaccion, on_delete=models.PROTECT)
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT)

    # Captador (datos del scraping)
    nombre_captador = models.CharField(max_length=200, blank=True)
    celular_captacion = models.CharField(max_length=30, blank=True)

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

    # Ubicación
    calle = models.CharField(max_length=255)
    zona = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    url_propiedad = models.URLField(max_length=500, default='', blank=True)

    # Booleanos
    parqueo = models.BooleanField(default=False)
    piscina = models.BooleanField(default=False)
    permite_mascotas = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    @property
    def imagen_principal(self):
        img = self.imagenes.first()
        return img.url if img else None

    def __str__(self):
        return f"{self.titulo} - {self.precio_usd}$"


class ImagenInmueble(models.Model):
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, related_name='imagenes')
    url = models.URLField(max_length=500)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        unique_together = [('inmueble', 'orden')]

    def __str__(self):
        return f"Imagen {self.orden} - {self.inmueble.titulo}"


class Etiqueta(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='etiquetas')
    nombre = models.CharField(max_length=100)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('usuario', 'nombre')]

    def clean(self):
        from django.core.exceptions import ValidationError
        if Etiqueta.objects.filter(usuario=self.usuario).exclude(pk=self.pk).count() >= 10:
            raise ValidationError("No puedes tener más de 10 etiquetas.")

    def __str__(self):
        return f"{self.nombre} ({self.usuario.email})"


class InmuebleGuardado(models.Model):
    etiqueta = models.ForeignKey(Etiqueta, on_delete=models.CASCADE, related_name='guardados')
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE)
    guardado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('etiqueta', 'inmueble')]

    def clean(self):
        from django.core.exceptions import ValidationError
        if InmuebleGuardado.objects.filter(etiqueta=self.etiqueta).exclude(pk=self.pk).count() >= 20:
            raise ValidationError("Esta etiqueta ya tiene 20 inmuebles guardados.")

    def __str__(self):
        return f"{self.etiqueta.nombre} → {self.inmueble.titulo}"
