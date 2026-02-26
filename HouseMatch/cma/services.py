"""
Servicio CMA: construye el prompt con los datos de las comparables
y llama a la API de OpenAI para obtener el análisis de precio.
"""

import json
from openai import OpenAI
from django.conf import settings


SYSTEM_PROMPT = """Eres un valuador inmobiliario experto especializado en Análisis Comparativo
de Mercado (CMA). Tu tarea es estimar el valor de una propiedad objetivo basándote en
3 propiedades comparables cuyos precios son conocidos.

LÓGICA DE AJUSTES A APLICAR:
- Cada cuarto adicional/menos respecto al promedio: +/- 3% del precio/m²
- Cada baño adicional/menos: +/- 2% del precio/m²
- Estacionamiento presente vs ausente: +/- 4% del precio total
- Piscina presente vs ausente: +/- 5% del precio total
- Diferencia en antigüedad (cada punto en escala 1-5): +/- 3% del precio total
- Diferencia en m² construidos: ajuste proporcional al precio/m²

PONDERACIÓN:
Asigna mayor peso (%) a la comparable que tenga más variables similares
a la propiedad objetivo. La suma de los 3 pesos debe ser 100%.

DEBES responder ÚNICAMENTE con un objeto JSON válido con esta estructura exacta,
sin texto adicional, sin markdown, sin bloques de código:

{
  "precio_minimo": 123000,
  "precio_sugerido": 135000,
  "precio_maximo": 148000,
  "ponderacion": [
    {"comparable": 1, "peso_pct": 40, "razon": "La más similar en m² y cuartos"},
    {"comparable": 2, "peso_pct": 35, "razon": "Similar pero sin piscina"},
    {"comparable": 3, "peso_pct": 25, "razon": "Zona similar pero mayor antigüedad"}
  ],
  "ajustes": [
    {"comparable": 1, "detalle": "+5% por cuarto adicional, -3% por ausencia de piscina"},
    {"comparable": 2, "detalle": "Sin ajustes significativos"},
    {"comparable": 3, "detalle": "-6% por antigüedad inferior (2 vs 4)"}
  ],
  "precio_m2_comparables": [
    {"comparable": 1, "precio_m2": 1875},
    {"comparable": 2, "precio_m2": 1833},
    {"comparable": 3, "precio_m2": 1866}
  ],
  "justificacion": "Párrafo de 3 a 5 líneas explicando el razonamiento en lenguaje claro.",
  "consideraciones": "Factores externos que el agente debe validar: zona, tendencia del mercado, etc."
}"""


def _build_user_prompt(comp1, comp2, comp3, objetivo: dict) -> str:
    def fmt_inmueble(label: str, inm, precio=None) -> str:
        lines = [
            f"--- {label} ---",
        ]
        if precio is not None:
            lines.append(f"Precio de venta: ${precio:,.2f} USD")
        lines += [
            f"Terreno (m²): {inm.get('area_terreno', 'N/D')}",
            f"Construcción (m²): {inm.get('area_construida', 'N/D')}",
            f"Cuartos: {inm.get('cant_cuartos', 'N/D')}",
            f"Baños: {inm.get('cant_banios', 'N/D')}",
            f"Estacionamiento: {'Sí' if inm.get('parqueo') else 'No'}",
            f"Piscina: {'Sí' if inm.get('piscina') else 'No'}",
            f"Antigüedad (1-5): {inm.get('antiguedad', 'N/D')}",
        ]
        if inm.get('zona'):
            lines.append(f"Zona: {inm['zona']}")
        return "\n".join(lines)

    def inmueble_to_dict(inm_obj):
        return {
            'area_terreno': float(inm_obj.area_terreno),
            'area_construida': float(inm_obj.area_construida),
            'cant_cuartos': inm_obj.cant_cuartos,
            'cant_banios': inm_obj.cant_banios,
            'parqueo': inm_obj.parqueo,
            'piscina': inm_obj.piscina,
            'antiguedad': getattr(inm_obj, '_antiguedad_score', 3),  # score enviado por el usuario
            'zona': inm_obj.zona,
        }

    c1 = inmueble_to_dict(comp1)
    c2 = inmueble_to_dict(comp2)
    c3 = inmueble_to_dict(comp3)

    prompt = "\n\n".join([
        fmt_inmueble("COMPARABLE 1", c1, float(comp1.precio_usd)),
        fmt_inmueble("COMPARABLE 2", c2, float(comp2.precio_usd)),
        fmt_inmueble("COMPARABLE 3", c3, float(comp3.precio_usd)),
        fmt_inmueble("PROPIEDAD OBJETIVO (sin precio)", objetivo),
    ])

    if objetivo.get('contexto'):
        prompt += f"\n\nContexto adicional: {objetivo['contexto']}"

    prompt += "\n\nRealiza el CMA y devuelve únicamente el JSON."
    return prompt


def generar_cma(comp1, comp2, comp3, objetivo: dict) -> dict:
    """
    Llama a OpenAI y devuelve el dict con el análisis.

    objetivo = {
        'area_terreno': ...,
        'area_construida': ...,
        'cant_cuartos': ...,
        'cant_banios': ...,
        'parqueo': True/False,
        'piscina': True/False,
        'antiguedad': 1-5,
        'zona': '...',
        'ciudad': '...',
        'contexto': '...',  (opcional)
    }
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    user_prompt = _build_user_prompt(comp1, comp2, comp3, objetivo)

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Limpiar posibles bloques markdown si el modelo los incluye de todas formas
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)