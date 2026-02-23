from rest_framework import serializers

from .models import ImagenInmueble, Inmueble


class InmuebleCreateSerializer(serializers.ModelSerializer):
    imagenes = serializers.ListField(
        child=serializers.URLField(max_length=500),
        write_only=True,
        required=False,
        default=list,
        help_text="Lista de URLs de imágenes. La primera (índice 0) será la principal.",
    )

    class Meta:
        model = Inmueble
        fields = [
            "tipo_propiedad",
            "tipo_transaccion",
            "departamento",
            "nombre_captador",
            "celular_captacion",
            "titulo",
            "descripcion",
            "cant_cuartos",
            "cant_banios",
            "area_construida",
            "area_terreno",
            "precio_usd",
            "precio_bs",
            "calle",
            "zona",
            "ciudad",
            "latitud",
            "longitud",
            "url_propiedad",
            "parqueo",
            "piscina",
            "permite_mascotas",
            "activo",
            "imagenes",
        ]

    def validate(self, attrs):
        latitud = attrs.get("latitud")
        longitud = attrs.get("longitud")

        if latitud is None or longitud is None:
            raise serializers.ValidationError(
                "latitud y longitud son requeridas para mostrar en el mapa."
            )

        if not (-90 <= float(latitud) <= 90):
            raise serializers.ValidationError(
                {"latitud": "Debe estar entre -90 y 90."}
            )

        if not (-180 <= float(longitud) <= 180):
            raise serializers.ValidationError(
                {"longitud": "Debe estar entre -180 y 180."}
            )

        return attrs

    def create(self, validated_data):
        imagenes_urls = validated_data.pop("imagenes", [])
        inmueble = Inmueble.objects.create(**validated_data)
        ImagenInmueble.objects.bulk_create([
            ImagenInmueble(inmueble=inmueble, url=url, orden=i)
            for i, url in enumerate(imagenes_urls)
        ])
        return inmueble
