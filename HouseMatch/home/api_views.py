from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Etiqueta, Inmueble, InmuebleGuardado
from .serializers import InmuebleCreateSerializer


class InmuebleCreateAPIView(generics.CreateAPIView):
    queryset = Inmueble.objects.all()
    serializer_class = InmuebleCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
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
            imagenes_list = list(inmueble.imagenes.all())
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
                        "imagen_principal": imagenes_list[0].url if imagenes_list else None,
                        "imagenes": [img.url for img in imagenes_list],
                        "url_propiedad": inmueble.url_propiedad,
                        "tipo_propiedad": inmueble.tipo_propiedad.nombre,
                        "tipo_transaccion": inmueble.tipo_transaccion.nombre,
                        "departamento": inmueble.departamento.nombre,
                        "nombre_captador": inmueble.nombre_captador,
                        "celular_captacion": inmueble.celular_captacion,
                    },
                }
            )

        return Response({"type": "FeatureCollection", "features": features})


class EtiquetaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Etiqueta.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        from django.core.exceptions import ValidationError as DjangoValidationError
        from rest_framework.exceptions import ValidationError as DRFValidationError

        etiqueta = Etiqueta(usuario=self.request.user, nombre=self.request.data.get("nombre", ""))
        try:
            etiqueta.clean()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)
        serializer.save(usuario=self.request.user)

    def get_serializer_class(self):
        from rest_framework import serializers as drf_serializers

        class EtiquetaSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = Etiqueta
                fields = ["id", "nombre", "creada_en"]
                read_only_fields = ["id", "creada_en"]

        return EtiquetaSerializer


class EtiquetaDestroyAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Etiqueta.objects.filter(usuario=self.request.user)

    def get_serializer_class(self):
        from rest_framework import serializers as drf_serializers

        class EtiquetaSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = Etiqueta
                fields = ["id", "nombre", "creada_en"]

        return EtiquetaSerializer


class InmuebleGuardadoListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        etiqueta_id = self.kwargs.get("etiqueta_id")
        return InmuebleGuardado.objects.filter(
            etiqueta__id=etiqueta_id,
            etiqueta__usuario=self.request.user,
        ).select_related("inmueble")

    def perform_create(self, serializer):
        from django.core.exceptions import ValidationError as DjangoValidationError
        from rest_framework.exceptions import ValidationError as DRFValidationError

        etiqueta_id = self.kwargs.get("etiqueta_id")
        etiqueta = generics.get_object_or_404(
            Etiqueta, id=etiqueta_id, usuario=self.request.user
        )
        guardado = InmuebleGuardado(etiqueta=etiqueta, inmueble=serializer.validated_data["inmueble"])
        try:
            guardado.clean()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message)
        serializer.save(etiqueta=etiqueta)

    def get_serializer_class(self):
        from rest_framework import serializers as drf_serializers

        class InmuebleGuardadoSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = InmuebleGuardado
                fields = ["id", "inmueble", "guardado_en"]
                read_only_fields = ["id", "guardado_en"]

        return InmuebleGuardadoSerializer


class InmuebleGuardadoDestroyAPIView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InmuebleGuardado.objects.filter(
            etiqueta__usuario=self.request.user
        )

    def get_serializer_class(self):
        from rest_framework import serializers as drf_serializers

        class InmuebleGuardadoSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = InmuebleGuardado
                fields = ["id", "inmueble", "guardado_en"]

        return InmuebleGuardadoSerializer
