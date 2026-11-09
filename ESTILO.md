# Guía de estilo visual

Referencia: [`referencias/estilo_ref.jpg`](referencias/estilo_ref.jpg)

## Resumen
Retrato en blanco y negro de estética años 70–80, como una foto impresa y vuelta a fotografiar o escanear: tipo ficha o foto de carnet, frontal, directo y sin pose.

## Encuadre y composición
- Plano medio corto / primer plano, sujeto **centrado y frontal**, mirada directa a cámara.
- Cabeza ocupando ~60 % del alto; recorte por el pecho.
- Fondo simple y gráfico (damero gris desenfocado), sin profundidad.
- Expresión neutra, seria, sin sonrisa.

## Luz
- Luz frontal plana y suave (flash directo difuso), sombras mínimas.
- Brillo especular pequeño en los ojos y en el labio.

## Color y tono (valores medidos)
| Parámetro | Valor |
|---|---|
| Negro más profundo (p1) | ~34/255 → negros **levantados**, nunca negro puro |
| Blanco más alto (p99) | ~206/255 → blancos **apagados**, nunca blanco puro |
| Mediana | ~136/255 |
| Sombras | neutras, un pelo cálidas (R≈48 G≈47 B≈43) |
| Luces | virado **verde-cian frío** (R≈182 G≈198 B≈187) |
| Contraste | medio, curva en S suave, medios tonos generosos |

## Textura
- Trama de impresión / moiré visible en zonas texturizadas (camisa de cuadros).
- Grano fino, nitidez blanda (no digital); ligera viñeta.
- Marcas y defectos de papel/escaneo bienvenidos.

## Aplicar el estilo a otra foto
```bash
python3 tools/aplicar_estilo.py mi_foto.jpg salida.jpg --grano 1.0 --trama 1.0
```
Requiere `pillow` y `numpy`. `--grano` y `--trama` regulan la textura (0 = nada).

## Prompt para generación con IA
> Black and white 1980s ID-style portrait photo, frontal, centered, direct gaze, neutral expression, flat soft frontal flash, blurred grey checkerboard background, faded print rephotographed, lifted blacks, muted whites, subtle cool green-cyan tint in highlights, visible halftone/moiré texture, fine grain, soft focus, slight vignette.
