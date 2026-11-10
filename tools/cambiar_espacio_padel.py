#!/usr/bin/env python3
"""Lleva una foto de pádel (exterior, luz plana o de día) al espacio de las
referencias low-key: pista cubierta a oscuras con un foco duro sobre el jugador.

Pasos:
  1. Recorta al jugador con rembg (modelo isnet-general-use) y recupera la
     bola por color.
  2. Sustituye el fondo por la oscuridad de la pista: negro con un leve
     velo petróleo, la valla/red apenas insinuada y algún foco del techo
     desenfocado.
  3. Conserva el suelo hundido en negro salvo un charco de luz bajo los pies.
  4. Reilumina al jugador (foco cenital: cabeza y torso más luz, piernas caen)
     y aplica la gradación de tools/aplicar_estilo_padel.py.

Uso:
    pip install "rembg[cpu]"
    python3 tools/cambiar_espacio_padel.py entrada.jpg [salida.jpg] [--suelo 0.8] [--sin-bola]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from aplicar_estilo_padel import estilizar  # noqa: E402


def _blur(a: np.ndarray, r: float) -> np.ndarray:
    img = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(float(r)))).astype(np.float32) / 255.0


def mascara_jugador(img: Image.Image) -> np.ndarray:
    from rembg import new_session, remove
    m = remove(img, session=new_session("isnet-general-use"), only_mask=True)
    return np.asarray(m).astype(np.float32) / 255.0


def mascara_bola(a: np.ndarray, jugador: np.ndarray) -> np.ndarray:
    """Pelota amarillo-verde fluorescente: la mancha saturada más grande fuera del jugador."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    amarillo = (g > 0.55) & (r > 0.45) & (b < 0.45) & (g - b > 0.35) & (jugador < 0.5)
    if amarillo.sum() < 50:
        return np.zeros_like(jugador)
    from scipy import ndimage
    lab, n = ndimage.label(ndimage.binary_closing(amarillo, iterations=3))
    tam = ndimage.sum(amarillo, lab, range(1, n + 1))
    ys, xs = np.nonzero(lab == (np.argmax(tam) + 1))
    # Disco ajustado a la mancha (el borde superior, más claro, no pasa el umbral de color)
    cy, cx = ys.mean(), xs.mean()
    rad = max(np.ptp(xs), np.ptp(ys)) / 2 + 1
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    bola = (np.hypot(yy - cy, xx - cx) <= rad).astype(np.float32)
    return _blur(bola, 1.2)


def fondo_pista(h: int, w: int, seed: int = 3) -> np.ndarray:
    """Oscuridad de pista cubierta: velo petróleo, valla tenue y focos desenfocados."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    fondo = np.zeros((h, w, 3), np.float32)
    # Velo muy tenue, algo más claro arriba (luz rebotada del techo)
    velo = 0.035 * np.clip(1 - yy / (h * 0.75), 0, 1)
    fondo += velo[..., None] * np.array([0.55, 0.95, 1.2])
    # Valla metálica: banda superior con rejilla fina casi invisible
    y0, y1 = int(h * 0.06), int(h * 0.30)
    paso = max(w // 260, 4)
    rejilla = ((xx.astype(int) % paso == 0) | (yy.astype(int) % paso == 0)).astype(np.float32)
    banda = ((yy > y0) & (yy < y1)).astype(np.float32)
    marco = (np.abs(yy - y0) < 2.5) | (np.abs(yy - y1) < 2.5)
    # La valla recibe algo de luz del foco: más visible hacia el centro-derecha
    caida = np.exp(-((xx / w - 0.6) / 0.45) ** 2)
    valla = _blur(rejilla * banda * 0.16 + marco * 0.22, max(w / 1100, 1.0)) * caida
    fondo += valla[..., None] * np.array([0.8, 0.95, 1.05])
    # Focos del techo desenfocados
    for fx, fy, rad, k in [(0.33, 0.17, 0.012, 0.85), (0.86, 0.55, 0.009, 0.35), (0.06, 0.05, 0.007, 0.25)]:
        d = np.hypot(xx - fx * w, yy - fy * h) / w
        fondo += (k * np.exp(-(d / rad) ** 2) + 0.06 * k * np.exp(-(d / (rad * 6)) ** 2))[..., None] \
            * np.array([1.0, 0.98, 0.92])
    fondo += rng.normal(0, 0.004, (h, w, 1)).astype(np.float32)
    return np.clip(fondo, 0, 1)


def cambiar_espacio(img: Image.Image, suelo: float = 0.8, bola: bool = True) -> Image.Image:
    img = img.convert("RGB")
    a = np.asarray(img).astype(np.float32) / 255.0
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    jug = mascara_jugador(img)
    ys, xs = np.nonzero(jug > 0.5)
    top, pies_y = ys.min(), np.percentile(ys, 99.5)
    cx = float(np.median(xs))
    alto = pies_y - top

    # Jugador reiluminado: foco cenital, caída hacia las piernas y luces contenidas
    rel = np.clip((yy - top) / max(alto, 1), 0, 1)
    luz = 1.0 - 0.55 * rel ** 1.4
    lado = np.exp(-((xx - cx) / (alto * 0.55)) ** 2)  # el borde del cuerpo cae un poco
    luz = luz * (0.8 + 0.2 * lado)
    sujeto = a * luz[..., None]
    sujeto = sujeto ** 1.35  # hunde medios tonos: sombras duras como bajo un foco
    # Blancos de la ropa a neutro-cálido (evita el violeta que deja el cielo azul)
    ys_ = sujeto @ np.array([0.299, 0.587, 0.114], np.float32)
    neutro = np.clip((ys_ - 0.35) / 0.4, 0, 1)[..., None] * 0.7
    sujeto = sujeto * (1 - neutro) + ys_[..., None] * np.array([1.03, 1.0, 0.95]) * neutro

    # Suelo: charco de luz bajo los pies, el resto negro
    d = np.hypot((xx - cx) / (alto * 0.55), (yy - pies_y) / (alto * 0.10))
    charco = np.exp(-d ** 2) * (yy > pies_y - alto * 0.12)
    gris_suelo = (a @ np.array([0.3, 0.59, 0.11], np.float32))[..., None]
    suelo_c = (0.5 * a + 0.5 * gris_suelo) * 0.35 * suelo * charco[..., None]
    # Sombra de contacto bajo las zapatillas
    contacto = _blur((jug > 0.5).astype(np.float32) * (yy > pies_y - alto * 0.08), alto * 0.02)
    suelo_c = suelo_c * (1 - 0.8 * contacto[..., None])

    fondo = fondo_pista(h, w) + suelo_c
    m = _blur(jug, 0.8)[..., None]
    out = fondo * (1 - m) + sujeto * m

    if bola:
        mb = mascara_bola(a, jug)[..., None]
        out = out * (1 - mb) + (a * 0.6) * mb

    res = Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8))
    # Gradación del estilo; foco sobre el torso del jugador
    foco = (cx / w, (top + alto * 0.3) / h)
    return estilizar(res, foco=foco, radio=0.75, oscuridad=0.35, saturacion=0.55, virado=1.0, grano=1.0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("entrada")
    p.add_argument("salida", nargs="?")
    p.add_argument("--suelo", type=float, default=0.8, help="intensidad del charco de luz en el suelo")
    p.add_argument("--sin-bola", action="store_true")
    args = p.parse_args()
    src = Path(args.entrada)
    dst = Path(args.salida) if args.salida else src.with_name(src.stem + "_pista.jpg")
    cambiar_espacio(Image.open(src), args.suelo, not args.sin_bola).save(dst, quality=93)
    print(dst)


if __name__ == "__main__":
    main()
