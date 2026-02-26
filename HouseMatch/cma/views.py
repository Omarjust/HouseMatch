import json
import io
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST

from home.models import Inmueble
from .models import AnálisisCMA
from .services import generar_cma
from .pdf import generar_pdf_cma


# ─────────────────────────────────────────────────────────────────────────────
# PASO 1 — Mapa de selección de 3 comparables
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def cma_mapa(request):
    """Vista del mapa interactivo para seleccionar 3 inmuebles comparables."""
    return render(request, 'cma/paso1_mapa.html')


@login_required
def cma_api_inmuebles_geojson(request):
    """
    Endpoint GeoJSON para poblar el mapa con los inmuebles disponibles.
    Solo devuelve inmuebles con coordenadas.
    """
    qs = Inmueble.objects.filter(
        activo=True,
        latitud__isnull=False,
        longitud__isnull=False,
    ).select_related('tipo_propiedad').prefetch_related('imagenes')

    features = []
    for inm in qs:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(inm.longitud), float(inm.latitud)],
            },
            "properties": {
                "id": inm.pk,
                "titulo": inm.titulo,
                "precio_usd": float(inm.precio_usd),
                "cant_cuartos": inm.cant_cuartos,
                "cant_banios": inm.cant_banios,
                "area_construida": float(inm.area_construida),
                "area_terreno": float(inm.area_terreno),
                "parqueo": inm.parqueo,
                "piscina": inm.piscina,
                "zona": inm.zona,
                "ciudad": inm.ciudad,
                "imagen": inm.imagen_principal or '',
            },
        })

    return JsonResponse({"type": "FeatureCollection", "features": features})


# ─────────────────────────────────────────────────────────────────────────────
# PASO 2 — Formulario de la propiedad objetivo
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def cma_formulario(request):
    """
    GET: muestra el formulario.
    Recibe los IDs de las 3 comparables desde query params (?c1=&c2=&c3=)
    que el mapa pasa al navegar al siguiente paso.
    """
    ids = [request.GET.get('c1'), request.GET.get('c2'), request.GET.get('c3')]

    if not all(ids):
        return redirect('cma:mapa')

    try:
        comparables = [
            get_object_or_404(Inmueble, pk=int(i)) for i in ids
        ]
    except (ValueError, TypeError):
        return redirect('cma:mapa')

    context = {
        'comparables': comparables,
        'ids': ids,
    }
    return render(request, 'cma/paso2_formulario.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# PASO 3 — Procesamiento IA + resultado
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def cma_procesar(request):
    """
    Recibe el formulario POST, llama a la IA y guarda el análisis.
    Redirige al resultado.
    """
    data = request.POST

    try:
        c1 = get_object_or_404(Inmueble, pk=int(data['comp_1']))
        c2 = get_object_or_404(Inmueble, pk=int(data['comp_2']))
        c3 = get_object_or_404(Inmueble, pk=int(data['comp_3']))
    except (ValueError, KeyError):
        return redirect('cma:mapa')

    # Scores de antigüedad ingresados por el usuario para cada comparable
    c1._antiguedad_score = int(data.get('antiguedad_1', 3))
    c2._antiguedad_score = int(data.get('antiguedad_2', 3))
    c3._antiguedad_score = int(data.get('antiguedad_3', 3))

    objetivo = {
        'area_terreno': float(data.get('area_terreno', 0)),
        'area_construida': float(data.get('area_construida', 0)),
        'cant_cuartos': int(data.get('cant_cuartos', 1)),
        'cant_banios': int(data.get('cant_banios', 1)),
        'parqueo': data.get('parqueo') == 'on',
        'piscina': data.get('piscina') == 'on',
        'antiguedad': int(data.get('antiguedad_objetivo', 3)),
        'zona': data.get('zona', ''),
        'ciudad': data.get('ciudad', ''),
        'contexto': data.get('contexto', ''),
    }

    try:
        resultado = generar_cma(c1, c2, c3, objetivo)
    except Exception as e:
        context = {
            'error': f'Error al generar el análisis: {str(e)}',
            'comparables': [c1, c2, c3],
            'ids': [c1.pk, c2.pk, c3.pk],
        }
        return render(request, 'cma/paso2_formulario.html', context)

    analisis = AnálisisCMA.objects.create(
        usuario=request.user,
        comparable_1=c1,
        comparable_2=c2,
        comparable_3=c3,
        obj_titulo=data.get('titulo', 'Propiedad a valuar'),
        obj_cant_cuartos=objetivo['cant_cuartos'],
        obj_cant_banios=objetivo['cant_banios'],
        obj_area_construida=Decimal(str(objetivo['area_construida'])),
        obj_area_terreno=Decimal(str(objetivo['area_terreno'])),
        obj_parqueo=objetivo['parqueo'],
        obj_piscina=objetivo['piscina'],
        obj_antiguedad=objetivo['antiguedad'],
        obj_zona=objetivo['zona'],
        obj_ciudad=objetivo['ciudad'],
        resultado_json=resultado,
        precio_minimo=Decimal(str(resultado.get('precio_minimo', 0))),
        precio_sugerido=Decimal(str(resultado.get('precio_sugerido', 0))),
        precio_maximo=Decimal(str(resultado.get('precio_maximo', 0))),
        justificacion=resultado.get('justificacion', ''),
    )

    return redirect('cma:resultado', pk=analisis.pk)


@login_required
def cma_resultado(request, pk):
    """Muestra el informe CMA generado."""
    analisis = get_object_or_404(AnálisisCMA, pk=pk, usuario=request.user)
    resultado = analisis.resultado_json or {}

    ponderacion = resultado.get('ponderacion', [])
    ajustes = resultado.get('ajustes', [])
    precio_m2 = resultado.get('precio_m2_comparables', [])

    def get_by_comp(lst, idx):
        return next((x for x in lst if x.get('comparable') == idx), None)

    comps = [analisis.comparable_1, analisis.comparable_2, analisis.comparable_3]
    comparables_data = [
        (
            comps[i],
            get_by_comp(ponderacion, i + 1),
            get_by_comp(ajustes, i + 1),
            get_by_comp(precio_m2, i + 1),
        )
        for i in range(3)
    ]

    context = {
        'analisis': analisis,
        'comparables_data': comparables_data,
        'consideraciones': resultado.get('consideraciones', ''),
    }
    return render(request, 'cma/paso3_resultado.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# EXPORTAR PDF
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def cma_pdf(request, pk):
    """Genera y devuelve el PDF del análisis CMA."""
    analisis = get_object_or_404(AnálisisCMA, pk=pk, usuario=request.user)
    pdf_bytes = generar_pdf_cma(analisis)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CMA_{analisis.pk}.pdf"'
    return response


# ─────────────────────────────────────────────────────────────────────────────
# HISTORIAL
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def cma_historial(request):
    """Lista todos los análisis del usuario."""
    analisis_list = AnálisisCMA.objects.filter(usuario=request.user)
    return render(request, 'cma/historial.html', {'analisis_list': analisis_list})