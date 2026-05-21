import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("outputs", exist_ok=True)


# Carregamento da imagem
bgr = cv2.imread("imagens/dog.jpg")


# O OpenCV carrega imagens no formato BGR.
# Como o padrão mais comum para visualização é RGB, os canais são invertidos.
# O astype(np.float64) facilita os cálculos matemáticos posteriores.
img_rgb = bgr[:, :, ::-1].astype(np.float64)


# H representa a altura da imagem.
# W representa a largura da imagem.
# Esses valores são usados depois para definir limites de plotagem
# e para percorrer a imagem em algumas funções.
H, W = img_rgb.shape[:2]

# Conversão para escala de cinza
gray = (
    0.299 * img_rgb[:, :, 0] +
    0.587 * img_rgb[:, :, 1] +
    0.114 * img_rgb[:, :, 2]
)

# Kernel
# Ele reduz ruídos e pequenas variações locais antes da segmentação
# e antes da detecção de bordas.
#
# Isso é importante porque, sem suavização, o Sobel poderia detectar
# vários detalhes pequenos como se fossem bordas relevantes.
def gaussian_kernel(size: int, sigma: float) -> np.ndarray:

    ax = np.arange(-(size // 2), size // 2 + 1, dtype=np.float64)

    xx, yy = np.meshgrid(ax, ax)

    # Aplica a fórmula da gaussiana 2D.
    # Pontos mais próximos do centro recebem peso maior.
    kernel = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))

    # Normaliza o kernel para a soma dos pesos ser 1.
    # Isso evita alterar o brilho geral da imagem.
    return kernel / kernel.sum()

# Convolução 2D manual
def convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2

    padded = np.pad(image, ((ph, ph), (pw, pw)), mode="reflect")


    shape_out = (image.shape[0], image.shape[1], kh, kw)

    strides_out = (
        padded.strides[0],
        padded.strides[1],
        padded.strides[0],
        padded.strides[1]
    )

    view = np.lib.stride_tricks.as_strided(
        padded,
        shape=shape_out,
        strides=strides_out
    )
    return (view * kernel).sum(axis=(2, 3))


# Suavização Gaussiana
# Cria um kernel gaussiano 7x7 com sigma 1.8.
# O tamanho 7 permite uma suavização mais perceptível.
# O sigma controla a intensidade da suavização.
gauss_k = gaussian_kernel(size=7, sigma=1.8)

smoothed = convolve2d(gray, gauss_k)

# 7. Limiarização com Otsu  
# O método de Otsu calcula automaticamente um limiar para separar a imagem em dois grupos: pixels claros e pixels escuros.

def otsu_threshold(image_uint8: np.ndarray) -> float:
    # Calcula o histograma da imagem com 256 níveis de intensidade.
    hist, _ = np.histogram(image_uint8.ravel(), bins=256, range=(0, 256))

    total = image_uint8.size


    sum_total = np.dot(np.arange(256), hist)

    sum_bg = 0.0
    w_bg = 0
    best_thresh = 0
    best_var = 0.0

    # REVISAR! Testa todos os possíveis limiares de 0 a 255.
    for t in range(256):
        
        w_bg += hist[t]

        if w_bg == 0:
            continue

        w_fg = total - w_bg

        if w_fg == 0:
            break

        sum_bg += t * hist[t]

        mean_bg = sum_bg / w_bg

        mean_fg = (sum_total - sum_bg) / w_fg

        
        var_between = w_bg * w_fg * (mean_bg - mean_fg) ** 2

        if var_between > best_var:
            best_var = var_between
            best_thresh = t

    return float(best_thresh)


# A imagem suavizada é limitada para o intervalo 0–255
# e convertida para uint8, pois o Otsu trabalha com histograma de 8 bits.
smoothed_u8 = np.clip(smoothed, 0, 255).astype(np.uint8)

thresh_val = otsu_threshold(smoothed_u8)


# Máscara binária
# Como o cachorro é mais escuro que o fundo, os pixels abaixo do limiar
# são marcados como 1.

# 1 = possível cachorro
# 0 = fundo
binary = (smoothed_u8 < thresh_val).astype(np.uint8)


# Operações
# Esta função implementa erosão e dilatação manualmente.

# Erosão: remove pequenos ruídos e miniui as regiões brancas;

# Dilatação: expande regiões brancas e ajuda a recuperar partes do objeto.

def morphology(image: np.ndarray, op: str, ksize: int = 3) -> np.ndarray:
    ph = ksize // 2

    padded = np.pad(image, ph, mode="constant", constant_values=0)

    shape_out = (image.shape[0], image.shape[1], ksize, ksize)

    strides_out = (
        padded.strides[0],
        padded.strides[1],
        padded.strides[0],
        padded.strides[1]
    )

    view = np.lib.stride_tricks.as_strided(
        padded,
        shape=shape_out,
        strides=strides_out
    )


    if op == "erode":
        return view.min(axis=(2, 3)).astype(np.uint8)

 
    return view.max(axis=(2, 3)).astype(np.uint8)

# Abertura = erosão seguida de dilatação, serve para remover ruídos pequenos.

opened = morphology(binary, "erode", ksize=5)
opened = morphology(opened, "dilate", ksize=5)


closed = morphology(opened, "dilate", ksize=9)
closed = morphology(closed, "erode", ksize=9)



# Após a limiarização, ainda podem existir ruídos ou manchas no fundo.

def largest_connected_component(mask: np.ndarray) -> np.ndarray:
    visited = np.zeros_like(mask, dtype=bool)
    best_mask = np.zeros_like(mask, dtype=np.uint8)
    best_size = 0

    rows, cols = np.where(mask == 1)

    if len(rows) == 0:
        return best_mask
    seed_indices = list(zip(rows[::20], cols[::20]))

    for r0, c0 in seed_indices:
        if visited[r0, c0] or mask[r0, c0] == 0:
            continue

        queue = [(r0, c0)]
        component = []

        while queue:
            r, c = queue.pop()

            if r < 0 or r >= H or c < 0 or c >= W:
                continue

            if visited[r, c] or mask[r, c] == 0:
                continue

            visited[r, c] = True
            component.append((r, c))

        
            queue.extend([
                (r + 1, c),
                (r - 1, c),
                (r, c + 1),
                (r, c - 1)
            ])

    
        if len(component) > best_size:
            best_size = len(component)
            best_mask = np.zeros_like(mask, dtype=np.uint8)

            for rr, cc in component:
                best_mask[rr, cc] = 1

    return best_mask

dog_mask = largest_connected_component(closed)


# ============================================================
# 12. REMOÇÃO MANUAL DA SOMBRA
# ============================================================
# A sombra próxima à pata estava sendo confundida com parte do cachorro.
# Para evitar que essa sombra vire borda e seja desenhada no Turtlesim,
# uma região específica da imagem é removida da máscara.
# shadow_box começa zerada e marca como 1 a região da sombra.
shadow_box = np.zeros_like(dog_mask)

shadow_box[580:, :280] = 1

dog_mask = dog_mask * (1 - shadow_box)


#Detecção de bordas com o Sobel
def sobel_edges(image: np.ndarray) -> np.ndarray:
    # Kernel para detectar variações no eixo X.
    kx = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float64)

    # Kernel para detectar variações no eixo Y.
    ky = np.array([
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1]
    ], dtype=np.float64)

    # Aplica os dois kernels usando a convolução implementada anteriormente.
    gx = convolve2d(image.astype(np.float64), kx)
    gy = convolve2d(image.astype(np.float64), ky)

    # Calcula a magnitude do gradiente.
    # Esse valor representa a força da borda.
    mag = np.sqrt(gx**2 + gy**2)

    # Evita divisão por zero caso a imagem não tenha variação.
    if mag.max() == 0:
        return mag

    # Normaliza a magnitude para o intervalo 0–1.
    return mag / mag.max()


#Aplicação do Sobel no cachorro
gray_masked = gray * dog_mask

# Calcula a magnitude das bordas.
edge_mag = sobel_edges(gray_masked)


#Limiarização
edge_thresh = 0.20
edges_bin = (edge_mag > edge_thresh).astype(np.uint8)

# A máscara é dilatada para permitir bordas próximas ao limite externo
# do cachorro. Isso evita cortar partes importantes do contorno.
dog_mask_dilated = morphology(dog_mask, "dilate", ksize=7)

# Mantém apenas bordas dentro ou próximas da máscara do cachorro.
edges_final = edges_bin * dog_mask_dilated
edge_external = edges_final.copy()


#Extração de pontos do contorno
# np.where retorna as coordenadas dos pixels onde existe borda.
# ys são as linhas e xs são as colunas.
ys, xs = np.where(edge_external > 0)

# Define uma quantidade aproximada de pontos.

n_points = 3000

# step define o intervalo de amostragem.
step = max(1, len(xs) // n_points)

xs_sub = xs[::step]
ys_sub = ys[::step]

# Cria uma figura com as principais etapas do processamento.
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.patch.set_facecolor("#0d0d0d")

for ax in axes.ravel():
    ax.set_facecolor("#0d0d0d")
    ax.axis("off")


# Função auxiliar para exibir uma imagem em um dos subplots.
def show(ax, data, cmap, title, vmin=None, vmax=None):
    ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(title, color="white", fontsize=11, pad=6)
    ax.axis("off")


# Mostra cada etapa da pipeline.
show(axes[0, 0], img_rgb.astype(np.uint8), None, "Original")
show(axes[0, 1], smoothed_u8, "gray", "Escala de Cinza + Gaussiana")
show(axes[0, 2], binary, "gray", "Limiarização")
show(axes[1, 0], dog_mask, "gray", "Máscara")
show(axes[1, 1], edge_mag, "hot", "Gradiente Sobel")


# Último gráfico: pontos finais do contorno.
ax_final = axes[1, 2]
ax_final.set_facecolor("black")
ax_final.scatter(xs_sub, ys_sub, s=10.0, c="white", linewidths=0, marker="o")
ax_final.set_xlim(0, W)

# O eixo y é invertido para manter a mesma orientação da imagem original.
ax_final.set_ylim(H, 0)
ax_final.set_title("Contorno em Pontos", color="white", fontsize=11, pad=6)
ax_final.axis("off")

plt.suptitle(
    "Pipeline de Visão Computacional",
    color="white",
    fontsize=13,
    fontweight="bold",
    y=1.01
)

plt.tight_layout()

# Salva a visualização completa da pipeline.
plt.savefig(
    "outputs/dog_pipeline.png",
    dpi=150,
    bbox_inches="tight",
    facecolor="#0d0d0d"
)

# Esta imagem mostra apenas os pontos que serão usados
fig2, ax2 = plt.subplots(figsize=(W / 100, H / 100), dpi=100)
fig2.patch.set_facecolor("black")
ax2.set_facecolor("black")

# Desenha os pontos do contorno em branco sobre fundo preto.
ax2.scatter(xs_sub, ys_sub, s=12.0, c="white", linewidths=0, marker="o")
ax2.set_xlim(0, W)
ax2.set_ylim(H, 0)
ax2.axis("off")

plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Salva a imagem final dos pontos.
plt.savefig(
    "outputs/dog_pontos.png",
    dpi=100,
    bbox_inches="tight",
    facecolor="black"
)

plt.close("all")

# Esse arquivo será lido pelo coordenadas.py,
# que converterá os pontos da imagem para o espaço do Turtlesim.
contour_points = np.stack([xs_sub, ys_sub], axis=1)
np.save("outputs/contour_points.npy", contour_points)