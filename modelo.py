
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
 
PAIS = "Ecuador"
 

NODOS = [
    ('A', 'Tulcán'), ('B', 'Ibarra'), ('C', 'Otavalo'),
    ('D', 'Quito'), ('E', 'Latacunga'), ('F', 'Ambato'),
    ('G', 'Riobamba'), ('H', 'Azogues'), ('I', 'Cuenca'),
    ('J', 'Loja'), ('K', 'San Lorenzo'), ('L', 'Esmeraldas'),
    ('M', 'Santo Domingo de los Colorados'), ('N', 'Chone'), ('O', 'Manta'),
    ('P', 'Portoviejo'), ('Q', 'Quevedo'), ('R', 'Babahoyo'),
    ('S', 'Guayaquil'), ('T', 'Santa Elena'), ('U', 'Machala'),
    ('V', 'Pasaje'), ('W', 'Guaranda'), ('X', 'Baeza'),
    ('Y', 'Nueva Loja'), ('Z', 'Tena'), ('AA', 'Puerto Francisco de Orellana (Coca)'),
    ('AB', 'Puyo'), ('AC', 'Macas'), ('AD', 'Zamora'),
]
 
# Tramos base del taller (origen, destino, km), en el mismo orden de filas del Excel
ARCOS_BASE = [
    ('T', 'S', 145), ('S', 'R', 80), ('R', 'Q', 117), ('Q', 'M', 124),
    ('M', 'D', 107), ('D', 'C', 70), ('C', 'B', 27), ('E', 'D', 115),
    ('X', 'D', 96), ('F', 'E', 47), ('G', 'F', 63), ('W', 'F', 77),
    ('AB', 'F', 100), ('H', 'G', 163), ('W', 'G', 53), ('I', 'H', 34),
    ('J', 'I', 167), ('V', 'I', 136), ('J', 'V', 135), ('AD', 'J', 39),
    ('K', 'L', 131), ('L', 'M', 197), ('N', 'M', 152), ('O', 'N', 102),
    ('P', 'N', 77), ('O', 'P', 43), ('S', 'P', 192), ('W', 'Q', 110),
    ('U', 'S', 160), ('U', 'V', 26), ('Y', 'X', 172), ('Z', 'X', 81),
    ('AA', 'Y', 84), ('AA', 'Z', 147), ('AB', 'Z', 79), ('AC', 'AB', 124),
    ('AD', 'AC', 293), ('B', 'A', 92),
]
 
LETRA = {c: l for l, c in NODOS}
CIUDAD = {l: c for l, c in NODOS}
CIUDADES = [c for _, c in NODOS]
LETRAS = [l for l, _ in NODOS]
 
 
def _fila_de(u, v):
    for i, (a, b, _) in enumerate(ARCOS_BASE):
        if {a, b} == {u, v}:
            return i
    raise KeyError((u, v))
 
 
def resolver_rutas(origen, destino, k=3):
    """origen/destino = letras de nodo (p. ej. "T", "A"). Devuelve hasta k rutas, de menor a mayor km.
    Cada ruta trae: camino (letras), km, filas (filas 0-based de ARCOS_BASE usadas, en orden de recorrido)
    y arcos (lista de 38 (origen, destino, km) con el sentido ajustado para que la ruta sea válida)."""
    dirigidos = []
    for a, b, d in ARCOS_BASE:
        dirigidos += [(a, b, d), (b, a, d)]
    n, m = len(dirigidos), len(LETRAS)
    A = np.zeros((m, n))
    for j, (o, d, _) in enumerate(dirigidos):
        A[LETRAS.index(o), j] += 1
        A[LETRAS.index(d), j] -= 1
    b = np.zeros(m)
    b[LETRAS.index(origen)] = 1
    b[LETRAS.index(destino)] = -1
    c = np.array([d for _, _, d in dirigidos], float)
    cons = [LinearConstraint(A, b, b)]
    rutas = []
    for _ in range(k):
        res = milp(c, constraints=cons, integrality=np.ones(n), bounds=Bounds(0, 1))
        if not res.success:
            break
        x = np.round(res.x).astype(int)
        usados = {dirigidos[j][0]: dirigidos[j][1] for j in range(n) if x[j]}
        camino = [origen]
        while camino[-1] != destino and len(camino) <= m:
            camino.append(usados[camino[-1]])
        filas = [_fila_de(u, v) for u, v in zip(camino, camino[1:])]
        arcos = list(ARCOS_BASE)
        for (u, v), f in zip(zip(camino, camino[1:]), filas):
            arcos[f] = (u, v, ARCOS_BASE[f][2])      # sentido del recorrido
        rutas.append({"camino": camino, "km": int(c @ x), "filas": filas, "arcos": arcos})
        cons.append(LinearConstraint(x.reshape(1, -1), -np.inf, x.sum() - 1))
    return rutas
 