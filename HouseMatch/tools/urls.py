from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('acm/', views.acm, name='acm'),
    path('acm/api/generar/', views.acm_generar, name='acm_generar'),
]
