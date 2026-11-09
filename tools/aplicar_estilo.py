#!/usr/bin/env python3
"""Aplica el estilo de referencia (referencias/estilo_ref.jpg) a una foto.

Look: retrato B/N años 80 impreso/escaneado. Negros levantados, blancos
apagados (sin blanco puro), virado partido (sombras neutras-cálidas, luces
verdosas/cian frías), textura de trama de impresión + grano y viñeta suave.

Uso:
    python3 tools/aplicar_estilo.py entrada.jpg [salida.jpg] [--grano 1.0] [--trama 1.0] [--gamma 1.15]
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# Valores medidos sobre la foto de referencia (0-255)
NEGRO = 34.0          # percentil 1 de luminancia
BLANCO = 206.0        # percentil 99
SOMBRA_RGB = np.array([48, 46.5, 43]) / 46.0    # tinte en sombras (ligeramente cálido)
LUZ_RGB = np.array([182, 198, 187]) / 189.0     # tinte en luces (verde-cian)


def estilizar(img: Image.Image, grano: float = 1.0, trama: float = 1.0, seed: int = 7,
              mezcla=(0.22, 0.62, 0.16), gamma: float = 1.15) -> Image.Image:
    rng = np.random.default_rng(seed)
    img = img.convert("RGB")
    # Suavizado leve: la referencia es una reproducción, no tiene nitidez digital
    img = img.filter(ImageFilter.GaussianBlur(radius=max(img.size) / 1600))
    a = np.asarray(img).astype(np.float32) / 255.0
    # Mezcla B/N con poco rojo (película de la época): la piel no se quema y conserva textura
    lum = a @ np.array(mezcla, dtype=np.float32)
    h, w = lum.shape

    # Normalizar y curva en S suave (contraste medio con medios tonos generosos)
    lo, hi = np.percentile(lum, [1, 99])
    lum = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1) ** gamma
    lum = lum + 0.18 * np.sin(np.pi * lum) * (lum - 0.5) * 2 * 0.5
    lum = np.clip(lum, 0, 1)

    # Textura de trama de impresión (líneas diagonales finas) + grano
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    periodo = max(w, h) / 380.0
    lineas = np.sin((xx + yy) * (2 * np.pi / periodo)) * np.sin((xx - yy) * (2 * np.pi / (periodo * 1.7)))
    lum = lum + 0.035 * trama * lineas * (1 - np.abs(lum - 0.5) * 1.2)
    ruido = rng.normal(0, 1, (h, w)).astype(np.float32)
    ruido = np.asarray(Image.fromarray(((ruido * 40) + 128).clip(0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 128 - 1
    lum = lum + 0.05 * grano * ruido

    # Viñeta suave
    cy, cx = h / 2, w / 2
    r = np.sqrt(((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2) / np.sqrt(2)
    lum = lum * (1 - 0.18 * r ** 2.2)
    lum = np.clip(lum, 0, 1)

    # Mapear a rango apagado y virar
    v = NEGRO + lum * (BLANCO - NEGRO)
    t = np.clip(lum, 0, 1)[..., None] ** 1.3
    tinte = SOMBRA_RGB * (1 - t) + LUZ_RGB * t
    out = np.clip(v[..., None] * tinte, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("entrada")
    p.add_argument("salida", nargs="?")
    p.add_argument("--grano", type=float, default=1.0)
    p.add_argument("--trama", type=float, default=1.0)
    p.add_argument("--gamma", type=float, default=1.15, help=">1 oscurece medios tonos")
    args = p.parse_args()
    src = Path(args.entrada)
    dst = Path(args.salida) if args.salida else src.with_name(src.stem + "_estilo.jpg")
    estilizar(Image.open(src), args.grano, args.trama, gamma=args.gamma).save(dst, quality=92)
    print(dst)


if __name__ == "__main__":
    main()
