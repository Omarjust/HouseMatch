from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Departamento, Inmueble, TipoPropiedad, TipoTransaccion


class InmuebleCreateAPITests(APITestCase):
    def setUp(self):
        self.url = "/api/inmuebles/"
        self.tipo_propiedad = TipoPropiedad.objects.create(nombre="Casa")
        self.tipo_transaccion = TipoTransaccion.objects.create(nombre="Venta")
        self.departamento = Departamento.objects.create(nombre="Santa Cruz")

    def _payload(self):
        return {
            "tipo_propiedad": self.tipo_propiedad.id,
            "tipo_transaccion": self.tipo_transaccion.id,
            "departamento": self.departamento.id,
            "titulo": "Casa centrica",
            "descripcion": "Amplia y luminosa",
            "cant_cuartos": 3,
            "cant_banios": 2,
            "area_construida": "180.00",
            "area_terreno": "250.00",
            "precio_usd": "120000.00",
            "precio_bs": "830000.00",
            "calle": "Av. Principal 123",
            "zona": "Centro",
            "ciudad": "Santa Cruz",
            "latitud": "-17.783300",
            "longitud": "-63.182100",
            "url_image": "https://example.com/photo.jpg",
            "url_propiedad": "https://example.com/property/123",
            "parqueo": True,
            "piscina": False,
            "permite_mascotas": True,
            "activo": True,
        }

    def test_create_inmueble_as_asesor(self):
        user = get_user_model().objects.create_user(
            email="asesor@example.com",
            username="asesor",
            password="test1234",
            is_asesor=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inmueble = Inmueble.objects.get()
        self.assertEqual(inmueble.asesor_id, user.id)
        self.assertEqual(inmueble.url_propiedad, "https://example.com/property/123")

    def test_create_inmueble_rejects_non_asesor(self):
        user = get_user_model().objects.create_user(
            email="cliente@example.com",
            username="cliente",
            password="test1234",
            is_asesor=False,
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Inmueble.objects.count(), 0)

    def test_create_inmueble_rejects_missing_coordinates(self):
        user = get_user_model().objects.create_user(
            email="asesor2@example.com",
            username="asesor2",
            password="test1234",
            is_asesor=True,
        )
        self.client.force_authenticate(user=user)
        payload = self._payload()
        payload.pop("latitud")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("latitud y longitud son requeridas", str(response.data))
        self.assertEqual(Inmueble.objects.count(), 0)

    def test_create_inmueble_rejects_out_of_range_coordinates(self):
        user = get_user_model().objects.create_user(
            email="asesor3@example.com",
            username="asesor3",
            password="test1234",
            is_asesor=True,
        )
        self.client.force_authenticate(user=user)
        payload = self._payload()
        payload["latitud"] = "95.000000"
        payload["longitud"] = "-200.000000"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("latitud", response.data)
        self.assertEqual(Inmueble.objects.count(), 0)

    def test_map_geojson_returns_feature_collection(self):
        user = get_user_model().objects.create_user(
            email="asesor4@example.com",
            username="asesor4",
            password="test1234",
            is_asesor=True,
        )
        Inmueble.objects.create(
            asesor=user,
            tipo_propiedad=self.tipo_propiedad,
            tipo_transaccion=self.tipo_transaccion,
            departamento=self.departamento,
            titulo="Casa para mapa",
            descripcion="Con coordenadas",
            cant_cuartos=4,
            cant_banios=3,
            area_construida="210.00",
            area_terreno="300.00",
            precio_usd="200000.00",
            precio_bs="1390000.00",
            calle="Calle 10",
            zona="Norte",
            ciudad="Santa Cruz",
            latitud="-17.780000",
            longitud="-63.170000",
            url_image="https://example.com/map-photo.jpg",
            url_propiedad="https://example.com/property/map-1",
            parqueo=True,
            piscina=True,
            permite_mascotas=True,
            activo=True,
        )

        response = self.client.get("/api/inmuebles/mapa/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "FeatureCollection")
        self.assertEqual(len(response.data["features"]), 1)
        feature = response.data["features"][0]
        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertEqual(feature["properties"]["titulo"], "Casa para mapa")


class MapPageTests(TestCase):
    def test_map_page_renders(self):
        response = self.client.get("/mapa/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mapa de Propiedades")
