from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Inmueble
from .serializers import InmuebleCreateSerializer


class InmuebleCreateAPIView(generics.CreateAPIView):
    queryset = Inmueble.objects.all()
    serializer_class = InmuebleCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_asesor:
            raise PermissionDenied("Solo asesores pueden publicar inmuebles.")
        serializer.save()


class InmuebleMapGeoJSONAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        inmuebles = (
            Inmueble.objects.filter(activo=True, latitud__isnull=False, longitud__isnull=False)
            .select_related("tipo_propiedad", "tipo_transaccion", "departamento")
            .prefetch_related("imagenes")
            .order_by("-id")
        )

        features = []
        for inmueble in inmuebles:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(inmueble.longitud), float(inmueble.latitud)],
                    },
                    "properties": {
                        "id": inmueble.id,
                        "titulo": inmueble.titulo,
                        "precio_usd": str(inmueble.precio_usd),
                        "precio_bs": str(inmueble.precio_bs),
                        "ciudad": inmueble.ciudad,
                        "zona": inmueble.zona,
                        "calle": inmueble.calle,
                        "cant_cuartos": inmueble.cant_cuartos,
                        "cant_banios": inmueble.cant_banios,
                        "piscina": inmueble.piscina,
                        "parqueo": inmueble.parqueo,
                        "permite_mascotas": inmueble.permite_mascotas,
                        "imagen_principal": inmueble.imagen_principal,
                        "imagenes": [img.url for img in inmueble.imagenes.all()],
                        "url_propiedad": inmueble.url_propiedad,
                        "tipo_propiedad": inmueble.tipo_propiedad.nombre,
                        "tipo_transaccion": inmueble.tipo_transaccion.nombre,
                        "departamento": inmueble.departamento.nombre,
                    },
                }
            )

        return Response({"type": "FeatureCollection", "features": features})
