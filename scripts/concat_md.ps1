<#
  concat_md.ps1

  Propósito:
    Concatenar archivos Markdown de pruebas en tres documentos resumen:
      - `tests/all_scenarios.md`     <- concatena `docs/test/scenarios/*.md`
      - `docs/test/all_unit.md`      <- concatena `docs/test/unit/**/*.md`
      - `docs/test/all_integration.md` <- concatena `docs/test/integration/*.md`

  Uso (PowerShell):
    pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/concat_md.ps1

  Notas:
    - El script ordena los archivos por nombre (o FullName en unitarios) antes de concatenar.
    - Inserta un comentario HTML del tipo <!-- file: ... --> antes del contenido de cada fichero
      para conservar referencia al origen dentro del archivo combinado.
    - Sobrescribe los archivos de salida si ya existen.
#>

# --- Escenarios (docs/test/scenarios -> tests/all_scenarios.md)
$scenarios = Get-ChildItem -Path "docs/test/scenarios" -Filter *.md | Sort-Object Name
$out1 = 'tests/all_scenarios.md'
if (Test-Path $out1) { Remove-Item $out1 }
foreach ($f in $scenarios) {
  # Marca el origen antes de cada bloque para trazabilidad
  "`n`n<!-- file: $($f.Name) -->`n" | Out-File -FilePath $out1 -Append -Encoding utf8
  # Añade el contenido del archivo
  Get-Content $f.FullName | Out-File -FilePath $out1 -Append -Encoding utf8
}

# --- Unitarios (docs/test/unit -> docs/test/all_unit.md)
# Busca recursivamente en la carpeta `docs/test/unit`
$units = Get-ChildItem -Path "docs/test/unit" -Filter *.md -Recurse | Sort-Object FullName
$out2 = 'docs/test/all_unit.md'
if (Test-Path $out2) { Remove-Item $out2 }
foreach ($f in $units) {
  "`n`n<!-- file: $($f.FullName) -->`n" | Out-File -FilePath $out2 -Append -Encoding utf8
  Get-Content $f.FullName | Out-File -FilePath $out2 -Append -Encoding utf8
}

# --- Integración (docs/test/integration -> docs/test/all_integration.md)
$integration = Get-ChildItem -Path "docs/test/integration" -Filter *.md | Sort-Object Name
$out3 = 'docs/test/all_integration.md'
if (Test-Path $out3) { Remove-Item $out3 }
foreach ($f in $integration) {
  "`n`n<!-- file: $($f.FullName) -->`n" | Out-File -FilePath $out3 -Append -Encoding utf8
  Get-Content $f.FullName | Out-File -FilePath $out3 -Append -Encoding utf8
}

Write-Output "Done: $out1, $out2 and $out3"