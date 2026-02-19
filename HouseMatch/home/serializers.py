from rest_framework import serializers

from .models import Inmueble


class InmuebleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inmueble
        fields = [
            "tipo_propiedad",
            "tipo_transaccion",
            "departamento",
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
            "url_image",
            "url_propiedad",
            "parqueo",
            "piscina",
            "permite_mascotas",
            "activo",
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
        return Inmueble.objects.create(
            asesor=self.context["request"].user,
            **validated_data,
        )
