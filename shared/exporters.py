"""Helpers de exportación CSV y XLSX para views de reportes (NEW-01)."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from django.http import HttpResponse, StreamingHttpResponse

XLSX_ROW_LIMIT = 10_000


class _EchoBuffer:
    """Buffer mínimo para StreamingHttpResponse (csv.writer necesita .write())."""

    def write(self, value: str) -> str:
        return value


def export_to_csv(
    headers: list[str],
    rows: Iterable[dict],
    filename: str,
) -> StreamingHttpResponse:
    """Exporta datos a CSV como StreamingHttpResponse (seguro con datasets grandes)."""
    pseudo_buffer = _EchoBuffer()
    writer = csv.DictWriter(pseudo_buffer, fieldnames=headers, extrasaction="ignore")

    def row_generator():
        yield writer.writeheader() or pseudo_buffer.write(",".join(headers) + "\r\n")
        for row in rows:
            yield writer.writerow(row)

    response = StreamingHttpResponse(
        _csv_generator(headers, rows),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _csv_generator(headers: list[str], rows: Iterable[dict]):
    """Generador lazy que produce líneas CSV una a una."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    yield buf.getvalue()

    for row in rows:
        buf.seek(0)
        buf.truncate(0)
        writer.writerow(row)
        yield buf.getvalue()


def export_to_xlsx(
    headers: list[str],
    rows: Iterable[dict],
    filename: str,
) -> HttpResponse:
    """Exporta datos a XLSX. Limita a XLSX_ROW_LIMIT filas para evitar OOM."""
    import openpyxl
    from openpyxl.styles import Font

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Datos"

    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    truncated = False
    count = 0
    for count, row in enumerate(rows, start=1):
        if count > XLSX_ROW_LIMIT:
            truncated = True
            break
        ws.append(
            [str(row.get(h, "")) if row.get(h, "") is not None else "" for h in headers]
        )

    if truncated:
        ws.append(
            [
                f"[Exportación limitada a {XLSX_ROW_LIMIT} filas. Use ?format=csv para el dataset completo.]"
            ]
            + [""] * (len(headers) - 1)
        )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    response = HttpResponse(
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    if truncated:
        response["X-Export-Truncated"] = "true"
        response["X-Export-Row-Limit"] = str(XLSX_ROW_LIMIT)
    return response
