from django.db import models
from django.conf import settings


class AnálisisCMA(models.Model):
    """Guarda un análisis comparativo de mercado generado por IA."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analisis_cma',
    )

    # Las 3 comparables seleccionadas en el mapa
    comparable_1 = models.ForeignKey(
        'home.Inmueble', on_delete=models.PROTECT, related_name='cma_comp1'
    )
    comparable_2 = models.ForeignKey(
        'home.Inmueble', on_delete=models.PROTECT, related_name='cma_comp2'
    )
    comparable_3 = models.ForeignKey(
        'home.Inmueble', on_delete=models.PROTECT, related_name='cma_comp3'
    )

    # Datos de la propiedad objetivo (ingresados manualmente)
    obj_titulo = models.CharField(max_length=200, default='Propiedad a valuar')
    obj_cant_cuartos = models.PositiveIntegerField()
    obj_cant_banios = models.PositiveIntegerField()
    obj_area_construida = models.DecimalField(max_digits=10, decimal_places=2)
    obj_area_terreno = models.DecimalField(max_digits=10, decimal_places=2)
    obj_parqueo = models.BooleanField(default=False)
    obj_piscina = models.BooleanField(default=False)
    obj_antiguedad = models.PositiveSmallIntegerField(
        help_text='Escala 1 (deteriorado) a 5 (nuevo/remodelado)'
    )
    obj_zona = models.CharField(max_length=100, blank=True)
    obj_ciudad = models.CharField(max_length=100, blank=True)

    # Resultado de la IA
    resultado_json = models.JSONField(null=True, blank=True)
    precio_minimo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    precio_sugerido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    precio_maximo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    justificacion = models.TextField(blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Análisis CMA'
        verbose_name_plural = 'Análisis CMA'

    def __str__(self):
        return f"CMA #{self.pk} - {self.obj_titulo} ({self.creado_en.strftime('%d/%m/%Y')})"