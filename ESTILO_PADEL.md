# Guía de estilo: pádel low-key

Referencias: [`referencias/padel_ref_1.jpg`](referencias/padel_ref_1.jpg) · [`referencias/padel_ref_2.jpg`](referencias/padel_ref_2.jpg)

## Resumen
Fotografía deportiva en pista cubierta, en clave baja y de aire cinematográfico. El jugador sale de un fondo negro, iluminado por un foco duro desde arriba. El color está apagado, con sombras azul petróleo y la piel cálida. Es una foto de momento, no de pose.

## Encuadre y composición
- **Contrapicado**: cámara baja y sujeto mirando hacia arriba o al frente, más allá de la cámara (nunca a cámara).
- Sujeto **descentrado**, con mucho espacio negativo oscuro (en horizontal, el jugador a la izquierda y el vacío a la derecha).
- Plano medio o tres cuartos; la pala forma parte de la composición.
- Elementos de la pista (red, cristal, focos del techo) apenas insinuados en el fondo, con algún punto de luz desenfocado.

## Luz
- Un solo foco cenital/lateral duro que recorta cara, brazos y pala.
- Fondo sin luz: **~92 % de la imagen por debajo de 20/255**.
- Las luces no queman: el máximo está en ~190–222/255.

## Color y tono (valores medidos)
| Parámetro | Ref 1 | Ref 2 |
|---|---|---|
| Mediana de luminancia | 0 | 0 |
| p95 / p99 / p99.9 | 42 / 165 / 222 | 65 / 144 / 190 |
| Sombras medias (lum 20–50) | R18 G36 B50 → **azul petróleo** | R29 G32 B33 → casi neutras, frías |
| Luces (lum > 180) | R221 G197 B188 → **cálidas** | R210 G188 B183 → cálidas |
| Saturación media (0–255) | 55 | 34 |

- Negros **puros** y aplastados: lo contrario del estilo retro de `ESTILO.md`, que levanta los negros.
- Virado partido teal & orange suave: frío en las sombras y cálido en la piel.
- Saturación baja; la ropa azul marino o petróleo apenas se separa del fondo.

## Textura
- Nitidez algo blanda, sin enfoque digital agresivo; grano fino casi invisible.
- Sin viñeta artificial: la oscuridad la pone la luz.

## Aplicar el estilo a otra foto
```bash
python3 tools/aplicar_estilo_padel.py mi_foto.jpg salida.jpg
```
Opciones:
- `--foco X,Y`: centro del foco en fracción de la imagen (p. ej. `0.4,0.3`). Por defecto busca la piel o la zona luminosa más centrada.
- `--radio 0.45`: tamaño del foco; un valor menor da más drama.
- `--oscuridad 1.0`: cuánto se hunde el fondo (0 = nada).
- `--saturacion 0.55`, `--virado 1.0`, `--grano 1.0`.

El filtro funciona mejor con fotos que ya tengan una luz dirigida; con una luz plana el foco es simulado. Ejemplo: [`ejemplos/prueba_padel.jpg`](ejemplos/prueba_padel.jpg).

## Prompt para generación con IA
> Low-key indoor padel sports photography, low angle shot, player lit by a single hard overhead spotlight emerging from pitch black background, off-center composition with large dark negative space, muted desaturated colors, teal-blue shadows, warm skin highlights, crushed pure blacks, unclipped highlights, faint out-of-focus arena lights and court fence, cinematic, candid mid-action moment, subtle fine grain.

## Llevar una foto de exterior al mismo espacio
Si la foto está hecha de día o en otra pista (muro, coches, sol), no basta con el filtro: hay que cambiar el fondo.
```bash
pip install "rembg[cpu]"
python3 tools/cambiar_espacio_padel.py mi_foto.jpg salida.jpg
```
El script recorta al jugador (rembg, modelo `isnet-general-use`) y recupera la bola por color. Pone de fondo la oscuridad de la pista: velo petróleo, valla tenue y focos del techo desenfocados. Deja un charco de luz con sombra de contacto bajo los pies, reilumina al jugador como bajo un foco cenital y termina con la gradación de `aplicar_estilo_padel.py`. Opciones: `--suelo 0.8` (intensidad del charco) y `--sin-bola`.
