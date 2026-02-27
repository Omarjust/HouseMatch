import json
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from groq import Groq


def _require_plan(request):
    user = request.user
    if not user.is_authenticated:
        login_url = reverse('home:login')
        return redirect(f'{login_url}?next={request.path}')
    if not (user.is_staff or user.is_superuser or user.plan_activo):
        return redirect('home:pricing')
    return None


def dashboard(request):
    guard = _require_plan(request)
    if guard:
        return guard
    return render(request, 'tools/dashboard.html')


def acm(request):
    guard = _require_plan(request)
    if guard:
        return guard
    return render(request, 'tools/acm.html')


@require_POST
def acm_generar(request):
    guard = _require_plan(request)
    if guard:
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    try:
        body = json.loads(request.body)
        comparables = body.get('comparables', [])
        sujeto = body.get('sujeto', {})

        if len(comparables) < 2 or len(comparables) > 3:
            return JsonResponse({'ok': False, 'error': 'Se requieren 2 o 3 inmuebles comparables'}, status=400)

        prompt = _build_prompt(comparables, sujeto)

        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=3000,
        )
        reporte = completion.choices[0].message.content
        return JsonResponse({'ok': True, 'reporte': reporte})

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


def _build_prompt(comparables, sujeto):
    def fmt_comp(c, idx):
        return f"""Comparable {idx}:
- Título: {c.get('titulo', 'N/D')}
- Tipo: {c.get('tipo_propiedad', 'N/D')} | Transacción: {c.get('tipo_transaccion', 'N/D')}
- Zona: {c.get('zona', 'N/D')}, {c.get('ciudad', 'N/D')}
- Área construida: {c.get('area_construida', 'N/D')} m² | Terreno: {c.get('area_terreno', 'N/D')} m²
- Habitaciones: {c.get('cant_cuartos', 'N/D')} | Baños: {c.get('cant_banios', 'N/D')}
- Precio: ${c.get('precio_usd', 'N/D')} USD
- Amenidades: Parqueo={'Sí' if c.get('parqueo') else 'No'}, Piscina={'Sí' if c.get('piscina') else 'No'}, Mascotas={'Sí' if c.get('permite_mascotas') else 'No'}""".strip()

    comps_text = '\n\n'.join(fmt_comp(c, i + 1) for i, c in enumerate(comparables))

    sujeto_text = f"""- Tipo: {sujeto.get('tipo_propiedad', 'N/D')} | Transacción: {sujeto.get('tipo_transaccion', 'N/D')}
- Zona: {sujeto.get('zona', 'N/D')}, {sujeto.get('ciudad', 'Santa Cruz')}
- Área construida: {sujeto.get('area_construida', 'N/D')} m² | Terreno: {sujeto.get('area_terreno', 'N/D')} m²
- Habitaciones: {sujeto.get('cant_cuartos', 'N/D')} | Baños: {sujeto.get('cant_banios', 'N/D')}
- Parqueo: {'Sí' if sujeto.get('parqueo') else 'No'} | Piscina: {'Sí' if sujeto.get('piscina') else 'No'} | Mascotas: {'Sí' if sujeto.get('permite_mascotas') else 'No'}
- Estado de conservación: {sujeto.get('estado_conservacion', 'N/D')}
- Precio del propietario: {('$' + str(sujeto.get('precio_propietario_usd')) + ' USD') if sujeto.get('precio_propietario_usd') else 'No especificado'}
- Notas adicionales: {sujeto.get('notas', 'Ninguna')}""".strip()

    return f"""Eres un perito inmobiliario certificado con amplia experiencia en el mercado boliviano (Santa Cruz, La Paz, Cochabamba). Genera un Análisis de Mercado Comparativo (AMC) profesional y detallado en español para el inmueble sujeto, basándote en los inmuebles comparables proporcionados.

INMUEBLES COMPARABLES DEL MERCADO:
{comps_text}

INMUEBLE SUJETO A ANALIZAR:
{sujeto_text}

Genera el AMC con las siguientes secciones en formato Markdown:

## 1. Resumen Ejecutivo
Síntesis de los hallazgos clave.

## 2. Tabla Comparativa
Tabla comparando el inmueble sujeto vs. cada comparable (características + precio/m²).

## 3. Análisis de Precio por m²
Calcula el precio USD/m² de cada comparable y su promedio ponderado.

## 4. Ajustes por Diferencias
Identifica diferencias relevantes (zona, estado, amenidades, tamaño) y su impacto estimado en el valor.

## 5. Rango de Valor Estimado
Rango mínimo-máximo justificado para el inmueble sujeto (en USD).

## 6. Precio de Lista Recomendado
Un precio específico de publicación con justificación.

## 7. Contexto de Mercado
Breve análisis del mercado inmobiliario local en esa zona/ciudad.

## 8. Conclusión y Recomendación
Estrategia recomendada para el asesor (precio, tiempo estimado de venta, puntos a negociar).

Sé preciso, profesional y fundamenta cada estimación con datos de los comparables."""
