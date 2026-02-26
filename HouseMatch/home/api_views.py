from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

MAPA_CACHE_KEY = 'mapa_geojson'
MAPA_CACHE_TTL = 60  # segundos

from .models import Etiqueta, Inmueble, InmuebleGuardado
from .serializers import InmuebleCreateSerializer


class ObtenerTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'error': 'email y password requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class InmuebleCreateAPIView(generics.CreateAPIView):
    queryset = Inmueble.objects.all()
    serializer_class = InmuebleCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        cache.delete(MAPA_CACHE_KEY)


class InmuebleMapGeoJSONAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = cache.get(MAPA_CACHE_KEY)
        if data is None:
            inmuebles = (
                Inmueble.objects.filter(activo=True, latitud__isnull=False, longitud__isnull=False)
                .select_related("tipo_propiedad", "tipo_transaccion", "departamento")
                .prefetch_related("imagenes")
                .order_by("-id")[:1000]
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
                            "area_construida": str(inmueble.area_construida),
                            "area_terreno": str(inmueble.area_terreno),
                            "tipo_propiedad": inmueble.tipo_propiedad.nombre,
                            "tipo_transaccion": inmueble.tipo_transaccion.nombre,
                            "departamento": inmueble.departamento.nombre,
                            "nombre_captador": inmueble.nombre_captador,
                            "celular_captacion": inmueble.celular_captacion,
                        },
                    }
                )

            data = {"type": "FeatureCollection", "features": features}
            cache.set(MAPA_CACHE_KEY, data, MAPA_CACHE_TTL)

        return Response(data)


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
