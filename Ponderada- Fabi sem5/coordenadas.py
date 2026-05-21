import numpy as np
import matplotlib.pyplot as plt


# Carregamento dos pontos extraídos da imagem
pts_img = np.load("outputs/contour_points.npy")


# Separa as coordenadas x e y em vetores diferentes.
xs_img = pts_img[:, 0].astype(np.float64)
ys_img = pts_img[:, 1].astype(np.float64)


# Definição dos limites do Turtlesim
TURTLE_MIN = 0.5
TURTLE_MAX = 10.5


# 3. Bounding box dos pontos

x_min, x_max = xs_img.min(), xs_img.max()
y_min, y_max = ys_img.min(), ys_img.max()

# Largura e altura reais ocupadas pelo cachorro na imagem.
img_w = x_max - x_min
img_h = y_max - y_min


# Cálculo da escala
turtle_range = TURTLE_MAX - TURTLE_MIN


# O código usa o menor dos dois valores para preservar a proporção.
# Isso evita deformar o cachorro.
#
# Se usasse escalas diferentes para x e y, o desenho poderia ficar
# esticado ou achatado.
scale = min(turtle_range / img_w, turtle_range / img_h)


cx = (TURTLE_MIN + TURTLE_MAX) / 2.0
cy = (TURTLE_MIN + TURTLE_MAX) / 2.0


# Calcula o centro da bounding box do cachorro na imagem.
# Esse centro será alinhado com o centro do Turtlesim.
cx_img = (x_min + x_max) / 2.0
cy_img = (y_min + y_max) / 2.0


# Conversão das coordenadas da imagem para o espaço do Turtlesim
# Esta é a etapa principal do arquivo.
#
# O código converte cada ponto da imagem para o espaço do Turtlesim.
#
# Para o eixo x:
# - subtrai o centro da imagem para centralizar o cachorro na origem;
# - multiplica pela escala;
# - soma o centro do Turtlesim para posicionar no meio da tela.
xs_turtle = cx + (xs_img - cx_img) * scale


# Para o eixo y, o processo é parecido, mas com uma diferença:
# o sinal é negativo.
#
# Isso acontece porque os sistemas têm orientações diferentes:
#
# Na imagem:
# y cresce para baixo.
#
# No Turtlesim:
# y cresce para cima.
#
# Por isso, é necessário inverter o eixo y.
ys_turtle = cy - (ys_img - cy_img) * scale

# Junta as coordenadas convertidas em uma matriz com formato:
# [[x1, y1],
#  [x2, y2],
#  [x3, y3],
#  ...]
# Esse é o formato esperado pelo desenhar_turtle.py.

pts_turtle = np.stack([xs_turtle, ys_turtle], axis=1)

np.save("outputs/contour_turtle.npy", pts_turtle)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor("#0d0d0d")


for ax in axes:
    ax.set_facecolor("black")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

axes[0].scatter(xs_img, ys_img, s=1.5, c="white", linewidths=0)


axes[0].set_xlim(0, xs_img.max() + 20)


axes[0].set_ylim(ys_img.max() + 20, 0)

axes[0].set_title("Espaço da imagem (px)", color="white", fontsize=11)
axes[0].set_xlabel("x (px)", color="white")
axes[0].set_ylabel("y (px)", color="white")


# Mostra os pontos já convertidos para coordenadas do Turtlesim.
axes[1].scatter(xs_turtle, ys_turtle, s=1.5, c="cyan", linewidths=0)


axes[1].set_xlim(0, 11)
axes[1].set_ylim(0, 11)

axes[1].set_title("Espaço Turtlesim (0–11)", color="white", fontsize=11)
axes[1].set_xlabel("x turtle", color="white")
axes[1].set_ylabel("y turtle", color="white")


# Essas linhas pontilhadas mostram a margem usada no mapeamento.
axes[1].axhline(TURTLE_MIN, color="#555", lw=0.8, ls="--")
axes[1].axhline(TURTLE_MAX, color="#555", lw=0.8, ls="--")
axes[1].axvline(TURTLE_MIN, color="#555", lw=0.8, ls="--")
axes[1].axvline(TURTLE_MAX, color="#555", lw=0.8, ls="--")

# Esse arquivo ajuda a conferir se o cachorro ficou centralizado,
# proporcional e dentro do espaço do Turtlesim.
plt.suptitle(
    "Mapeamento Imagem → Turtlesim",
    color="white",
    fontsize=13,
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    "outputs/coordenadas_mapeamento.png",
    dpi=130,
    bbox_inches="tight",
    facecolor="#0d0d0d"
)

plt.close()