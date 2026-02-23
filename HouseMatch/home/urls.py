from django.urls import path

from .api_views import (
    InmuebleCreateAPIView,
    InmuebleMapGeoJSONAPIView,
    EtiquetaListCreateAPIView,
    EtiquetaDestroyAPIView,
    InmuebleGuardadoListCreateAPIView,
    InmuebleGuardadoDestroyAPIView,
    ObtenerTokenView,
)
from .views import home, login, logout, mapa, pricing, registro, etiquetas as etiquetas_view, detalle_inmueble

app_name = 'home'

urlpatterns = [
    path('', home, name='index'),
    path('precios/', pricing, name='pricing'),
    path('mapa/', mapa, name='mapa'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('registro/', registro, name='registro'),
    path('etiquetas/', etiquetas_view, name='etiquetas'),
    path('inmuebles/<int:pk>/', detalle_inmueble, name='detalle_inmueble'),
    path('api/token/', ObtenerTokenView.as_view(), name='api_token'),
    path('api/inmuebles/', InmuebleCreateAPIView.as_view(), name='api_inmueble_create'),
    path('api/inmuebles/mapa/', InmuebleMapGeoJSONAPIView.as_view(), name='api_inmueble_mapa'),
    path('api/etiquetas/', EtiquetaListCreateAPIView.as_view(), name='api_etiqueta_list_create'),
    path('api/etiquetas/<int:pk>/', EtiquetaDestroyAPIView.as_view(), name='api_etiqueta_destroy'),
    path('api/etiquetas/<int:etiqueta_id>/guardados/', InmuebleGuardadoListCreateAPIView.as_view(), name='api_guardado_list_create'),
    path('api/guardados/<int:pk>/', InmuebleGuardadoDestroyAPIView.as_view(), name='api_guardado_destroy'),
]
