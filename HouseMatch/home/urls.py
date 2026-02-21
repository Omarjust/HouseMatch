from django.urls import path

from .api_views import InmuebleCreateAPIView, InmuebleMapGeoJSONAPIView
from .views import home, login, logout, mapa, pricing

app_name = 'home'

urlpatterns = [
    path('', home, name='index'),
    path('precios/', pricing, name='pricing'),
    path('mapa/', mapa, name='mapa'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('api/inmuebles/', InmuebleCreateAPIView.as_view(), name='api_inmueble_create'),
    path('api/inmuebles/mapa/', InmuebleMapGeoJSONAPIView.as_view(), name='api_inmueble_mapa'),
]
