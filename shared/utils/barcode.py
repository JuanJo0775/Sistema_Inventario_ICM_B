"""Utilidades para generación y render de códigos de barras."""

from __future__ import annotations

import base64

try:
    from barcode import get_barcode_class  # type: ignore
    from barcode.writer import SVGWriter  # type: ignore

    _HAS_BARCODE_LIB = True
except Exception:  # pragma: no cover - environment fallback for tests
    _HAS_BARCODE_LIB = False

BARCODE_SYMBOLOGY = "Code128"
# Configuración compacta para etiquetas pequeñas sin sacrificar demasiado la lectura.
BARCODE_RENDER_OPTIONS = {
    "module_width": 0.17,
    "module_height": 9.0,
    "quiet_zone": 1.0,
    "font_size": 7,
    "text_distance": 1.0,
    "write_text": True,
}


def build_product_barcode(sku: str) -> str:
    """
    Genera el barcode a partir del SKU del producto.

    RF-003 / BR-13:
    - El UUID queda como identificador técnico interno.
    - El SKU es el alias de negocio y el barcode escaneable.
    """
    value = (sku or "").strip()
    if not value:
        raise ValueError("sku es obligatorio para generar el barcode.")
    return value


def render_code128_svg(value: str) -> str:
    """Renderiza un barcode Code 128 a SVG."""
    if not _HAS_BARCODE_LIB:
        # Devuelve un SVG placeholder cuando la librería no está disponible
        placeholder = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="80">'
            f'<rect width="100%" height="100%" fill="#f3f3f3"/>'
            f'<text x="10" y="40" font-family="sans-serif" font-size="12" fill="#333">'
            f"Barcode lib missing - value: {value}"
            "</text></svg>"
        )
        return placeholder
    code128 = get_barcode_class("code128")
    barcode = code128(value, writer=SVGWriter())
    svg_bytes = barcode.render(writer_options=BARCODE_RENDER_OPTIONS)
    return svg_bytes.decode("utf-8")


def barcode_svg_data_uri(svg: str) -> str:
    """Convierte un SVG a un data URI embebible en frontend."""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_product_barcode_payload(barcode: str) -> dict[str, str]:
    """Construye valor, simbología y representación SVG para un barcode dado."""
    value = barcode.strip()
    svg = render_code128_svg(value)
    return {
        "type": BARCODE_SYMBOLOGY,
        "value": value,
        "svg": svg,
        "svg_data_uri": barcode_svg_data_uri(svg),
    }
