#!/usr/bin/env python3
"""Aplica el estilo «pádel low-key» (referencias/padel_ref_1.jpg y padel_ref_2.jpg).

Look: fotografía deportiva de pista cubierta en clave baja. Fondo que se
hunde en negro puro (~90 % de la imagen por debajo de 20/255), el sujeto
recortado por un foco duro, color apagado con virado partido: sombras
medias azul petróleo/cian y luces cálidas en la piel. Luces sin quemar
(máximo ~220/255), nitidez algo blanda y grano fino.

Uso:
    python3 tools/aplicar_estilo_padel.py entrada.jpg [salida.jpg]
        [--foco X,Y] [--radio 0.45] [--oscuridad 1.0] [--saturacion 0.55]
        [--virado 1.0] [--grano 1.0]

--foco     centro del foco en fracción de la imagen (0-1). Por defecto se
           busca automáticamente la zona más iluminada.
--radio    tamaño del foco (fracción de la diagonal). Más pequeño = más drama.
--oscuridad  cuánto se hunden los medios tonos y el fondo (0 = nada).
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# Valores medidos sobre las dos referencias (0-255)
MAX_LUZ = 222.0                                   # percentil 99.9: luces nunca quemadas
TEAL = np.array([17.5, 35.5, 50.0]) / 34.3        # tinte en sombras medias (lum 20-50)
CALIDO = np.array([220.7, 197.0, 188.3]) / 202.0  # tinte en luces (lum > 180)


def _suavizar(a: np.ndarray, radio: float) -> np.ndarray:
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radio))).astype(np.float32) / 255.0


def _buscar_foco(a: np.ndarray, lum: np.ndarray) -> tuple[float, float]:
    """Centro del sujeto: tonos de piel si los hay; si no, la zona luminosa
    más cercana al centro (evita que un fondo claro se lleve el foco)."""
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    centro = np.exp(-(((xx / w - 0.5) / 0.35) ** 2 + ((yy / h - 0.45) / 0.35) ** 2))
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    piel = ((r > g) & (g > b) & (r - b > 0.08) & (lum > 0.2)).astype(np.float32)
    if piel.mean() > 0.01:
        peso = _suavizar(piel, max(h, w) / 40) * centro
    else:
        peso = _suavizar(lum, max(h, w) / 25) ** 2 * centro
    peso = peso * (peso >= np.percentile(peso, 90))
    return float((xx * peso).sum() / peso.sum() / w), float((yy * peso).sum() / peso.sum() / h)


def estilizar(img: Image.Image, foco=None, radio: float = 0.45, oscuridad: float = 1.0,
              saturacion: float = 0.55, virado: float = 1.0, grano: float = 1.0,
              seed: int = 7) -> Image.Image:
    rng = np.random.default_rng(seed)
    img = img.convert("RGB")
    img = img.filter(ImageFilter.GaussianBlur(radius=max(img.size) / 2200))
    a = np.asarray(img).astype(np.float32) / 255.0
    h, w = a.shape[:2]
    lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lo, hi = np.percentile(lum, [0.5, 99.7])
    lum = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1)

    # Foco: caída gaussiana alrededor del sujeto, el resto se va a negro
    fx, fy = foco if foco else _buscar_foco(a, lum)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    diag = np.hypot(w, h)
    d = np.hypot(xx - fx * w, yy - fy * h) / diag
    spot = np.exp(-(d / max(radio, 1e-3)) ** 2 * 2.2)
    lum = lum * (1 - oscuridad * 0.85 * (1 - spot))

    # Curva de clave baja: umbral que aplasta el fondo a negro puro y
    # hombro suave arriba para que las luces no quemen
    umbral = 0.18 * oscuridad
    t = np.clip((lum - umbral) / (1 - umbral), 0, 1)
    t = t ** (1 + 0.6 * oscuridad)
    y = t * (MAX_LUZ / 255.0)

    # Color apagado: conservar el croma original reducido
    base = a / np.maximum(a @ np.array([0.299, 0.587, 0.114], dtype=np.float32), 1e-4)[..., None]
    color = 1 + saturacion * (base - 1)

    # Virado partido: petróleo en sombras medias, cálido en luces
    w_sombra = np.exp(-((y - 0.14) / 0.09) ** 2)[..., None] * virado
    w_luz = np.clip((y - 0.45) / 0.35, 0, 1)[..., None] * virado
    tinte = 1 + w_sombra * (TEAL - 1) * 0.6 + w_luz * (CALIDO - 1)
    out = y[..., None] * color * tinte

    # Grano fino, más visible en medios tonos que en los negros
    ruido = rng.normal(0, 1, (h, w)).astype(np.float32)
    ruido = _suavizar(ruido * 0.15 + 0.5, 0.5) * 2 - 1
    out = out + (0.018 * grano * ruido * np.sqrt(y))[..., None]

    out = np.clip(out * 255, 0, MAX_LUZ + 8).astype(np.uint8)
    return Image.fromarray(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("entrada")
    p.add_argument("salida", nargs="?")
    p.add_argument("--foco", type=str, default=None, help="X,Y en fracción (p. ej. 0.4,0.35)")
    p.add_argument("--radio", type=float, default=0.45)
    p.add_argument("--oscuridad", type=float, default=1.0)
    p.add_argument("--saturacion", type=float, default=0.55)
    p.add_argument("--virado", type=float, default=1.0)
    p.add_argument("--grano", type=float, default=1.0)
    args = p.parse_args()
    foco = tuple(float(v) for v in args.foco.split(",")) if args.foco else None
    src = Path(args.entrada)
    dst = Path(args.salida) if args.salida else src.with_name(src.stem + "_padel.jpg")
    estilizar(Image.open(src), foco, args.radio, args.oscuridad, args.saturacion,
              args.virado, args.grano).save(dst, quality=92)
    print(dst)


if __name__ == "__main__":
    main()
