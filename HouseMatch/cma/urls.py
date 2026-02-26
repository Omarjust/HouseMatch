from django.urls import path
from . import views

app_name = 'cma'

urlpatterns = [
    path('', views.cma_historial, name='historial'),
    path('nuevo/', views.cma_mapa, name='mapa'),
    path('formulario/', views.cma_formulario, name='formulario'),
    path('procesar/', views.cma_procesar, name='procesar'),
    path('resultado/<int:pk>/', views.cma_resultado, name='resultado'),
    path('pdf/<int:pk>/', views.cma_pdf, name='pdf'),
    path('api/inmuebles/', views.cma_api_inmuebles_geojson, name='api_geojson'),
]