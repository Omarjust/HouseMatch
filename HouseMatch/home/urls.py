from django.urls import path

from .api_views import InmuebleCreateAPIView, InmuebleMapGeoJSONAPIView
from .views import home, mapa, pricing

app_name = 'home'

urlpatterns = [
    path('', home, name='index'),
    path('precios/', pricing, name='pricing'),
    path('mapa/', mapa, name='mapa'),
    path('api/inmuebles/', InmuebleCreateAPIView.as_view(), name='api_inmueble_create'),
    path('api/inmuebles/mapa/', InmuebleMapGeoJSONAPIView.as_view(), name='api_inmueble_mapa'),
]
