
"""Excel igual al del taller (Rutas_Ecuador_tres_alternativas): una hoja por ruta, mismo orden y fórmulas."""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from modelo import NODOS, ARCOS_BASE, CIUDAD
 
C11, C11B = Font(name="Calibri", size=11), Font(name="Calibri", size=11, bold=True, color="FFFFFF")
G10 = Font(name="Calibri", size=10, color="191C21")
A10 = Font(name="Arial", size=10)
A10B = Font(name="Arial", size=10, bold=True, color="17365D")
FILL_AC, FILL_RESTO, FILL_K = (PatternFill("solid", fgColor=c) for c in ("405F90", "28547D", "EAF2F8"))
lado = lambda c: Side(style="thin", color=c)
B_AC = Border(*(lado("D8E0EA"),) * 2, *(lado("D8E0EA"),) * 2)
B_NEG = Border(left=lado("000000"), right=lado("000000"), top=lado("000000"), bottom=lado("000000"))
B_H = Border(left=lado("667284"), right=lado("667284"), top=lado("667284"), bottom=lado("667284"))
CEN, IZQ = Alignment(horizontal="center", vertical="center"), Alignment(horizontal="left", vertical="center")
 
NODOS_RNG = (2, 31)
ARC_RNG = (2, 39)
 
 
def _hoja(ws, origen, destino, rutas, k):
    ruta = rutas[k]
    nA, nN = len(ARCOS_BASE), len(NODOS)
    f1, fN = ARC_RNG[0], 1 + nA          # filas de arcos 2..39
    n1, nM = NODOS_RNG[0], 1 + nN        # filas de nodos 2..31
 
    for col, h in zip("ABCDEFGIJKL", ["N.º", "Nodo", "Ciudad o pueblo", "Origen", "Destino", "Distancia (km)",
                                      "En ruta", "Nodo", "Flujo", "Operador", "Condición"]):
        c = ws[f"{col}1"]
        c.value, c.font, c.alignment = h, C11B, CEN
        c.fill = FILL_AC if col in "ABC" else FILL_RESTO
        if col in "ABC":
            c.border = B_H
            if col == "C": c.alignment = IZQ
    ws.row_dimensions[1].height = 24
 
    usadas = set(ruta["filas"])
    for i, (letra, ciudad) in enumerate(NODOS):
        r = n1 + i
        for col, v, al in (("A", i + 1, CEN), ("B", letra, CEN), ("C", ciudad, IZQ)):
            c = ws[f"{col}{r}"]
            c.value, c.font, c.alignment, c.border = v, G10, al, B_AC
        ws[f"I{r}"] = letra
        ws[f"J{r}"] = f"=SUMIF($D${f1}:$D${fN},I{r},$G${f1}:$G${fN})-SUMIF($E${f1}:$E${fN},I{r},$G${f1}:$G${fN})"
        ws[f"K{r}"] = '"="'
        ws[f"L{r}"] = 1 if letra == origen else (-1 if letra == destino else 0)
        for col in "IJKL":
            c = ws[f"{col}{r}"]
            c.font, c.border = C11, B_NEG
            if col != "I": c.alignment = Alignment(horizontal="center")
    for i, (o, d, km) in enumerate(ruta["arcos"]):
        r = f1 + i
        for col, v in zip("DEFG", (o, d, km, 1 if i in usadas else 0)):
            c = ws[f"{col}{r}"]
            c.value, c.font, c.border = v, C11, B_NEG
            c.fill = PatternFill("solid", fgColor="FFFFFF")
            if col == "F": c.number_format = "#,##0"
            if col == "G": c.alignment = Alignment(horizontal="center")
 
    for r in range(2, 54):
        ws.row_dimensions[r].height = 19.5
    # Bloque de resumen (columnas I:K)
    info = [
        (34, "Distancia Minima", f"=SUMPRODUCT(F{f1}:F{fN},G{f1}:G{fN})"),
        (35, "Distancia verificada (km)", ruta["km"]),
        (36, "Origen ", origen), (37, "Destino", destino),
        (38, "Nodos de la red", nN), (39, "Aristas", nA),
        (40, "Tramos elegidos", len(ruta["filas"])),
        (41, "Recorrido", " - ".join(ruta["camino"])),
        (42, "Tipo", "Ruta 1 - mínima" if k == 0 else f"Ruta {k+1} - alternativa"),
    ]
    for r, et, v in info:
        ws[f"I{r}"], ws[f"K{r}"] = et, v
        ws[f"I{r}"].font = ws[f"K{r}"].font = A10
    ws["I44"], ws["I44"].font = "Configuración de Solver", A10B
    for r, t in zip(range(45, 49), [f"Objetivo: minimizar K34", f"Variables: G{f1}:G{fN} binarias",
                                    f"Balance: J{n1}:J{nM} = L{n1}:L{nM}", "Método: Simplex LP"]):
        ws[f"I{r}"], ws[f"I{r}"].font = t, A10
    for j in (0, 1):
        r = 50 + j
        ws[f"I{r}"], ws[f"I{r}"].font = f"Exclusión ruta {j+1}", A10B
        for col in "KL":
            ws[f"{col}{r}"].fill, ws[f"{col}{r}"].font = FILL_K, A10
        if j < k:
            celdas = ",".join(f"G{f + 2}" for f in rutas[j]["filas"])
            ws[f"K{r}"] = f"=SUM({celdas})"
            ws[f"L{r}"] = len(rutas[j]["filas"]) - 1
    ws["I53"] = ("Sin restricciones de exclusión" if k == 0 else
                 "Agregar en Solver: K50 <= L50" if k == 1 else "Agregar en Solver: K50 <= L50 y K51 <= L51")
    ws["I53"].font = A10
 
    for col, w in zip("ABCDEFGHI", [3.2, 4.9, 27, 11.3, 11.7, 18.1, 10.9, 12.7, 29]):
        ws.column_dimensions[col].width = w
    ws.sheet_format.defaultColWidth = 12.66
    ws.freeze_panes = "A2"
    ws.sheet_view.zoomScale = 70
 
 
def construir_excel(origen, destino, rutas, ruta_salida):
    """origen/destino = letras de nodo (p. ej. 'T' y 'A')."""
    wb = Workbook()
    wb.remove(wb.active)
    for k in range(len(rutas)):
        _hoja(wb.create_sheet(f"{origen} - {destino} Ruta {k+1}"), origen, destino, rutas, k)
    wb.save(ruta_salida)
    return ruta_salida
 
 
if __name__ == "__main__":
    from modelo import resolver_rutas
    construir_excel("T", "A", resolver_rutas("T", "A"), "Rutas_Ecuador_tres_alternativas_T_A.xlsx")
 