from django.core.management.base import BaseCommand

from home.models import Departamento, TipoPropiedad, TipoTransaccion


class Command(BaseCommand):
    help = 'Crea registros de catálogo (TipoPropiedad, TipoTransaccion, Departamento)'

    def handle(self, *args, **options):
        tipos_propiedad = ['Casa', 'Departamento', 'Quinta', 'Oficina', 'Terreno']
        for nombre in tipos_propiedad:
            obj, created = TipoPropiedad.objects.get_or_create(nombre=nombre)
            estado = 'creado' if created else 'ya existía'
            self.stdout.write(f'TipoPropiedad "{nombre}" → {estado}')

        tipos_transaccion = ['Venta', 'Alquiler', 'Anticrético']
        for nombre in tipos_transaccion:
            obj, created = TipoTransaccion.objects.get_or_create(nombre=nombre)
            estado = 'creado' if created else 'ya existía'
            self.stdout.write(f'TipoTransaccion "{nombre}" → {estado}')

        departamentos = [
            'Santa Cruz', 'La Paz', 'Cochabamba', 'Oruro',
            'Potosí', 'Sucre', 'Tarija', 'Beni', 'Pando',
        ]
        for nombre in departamentos:
            obj, created = Departamento.objects.get_or_create(nombre=nombre)
            estado = 'creado' if created else 'ya existía'
            self.stdout.write(f'Departamento "{nombre}" → {estado}')

        self.stdout.write(self.style.SUCCESS('Catálogo sembrado exitosamente.'))
