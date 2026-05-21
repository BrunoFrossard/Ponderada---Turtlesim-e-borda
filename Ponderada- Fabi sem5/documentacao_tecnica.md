# Relatório Técnico — Ponderada de Programação: Semana 5

## 1. Visão geral do projeto

Este projeto tem como objetivo implementar uma pipeline completa de visão computacional para extrair os contornos de uma imagem e reproduzi-los no Turtlesim utilizando ROS 2.

A imagem utilizada no projeto é `dog.jpg`, localizada na pasta `imagens/`. A partir dessa imagem, o sistema faz o pré-processamento, identifica o cachorro, extrai os pontos de borda, converte esses pontos para o espaço de coordenadas do Turtlesim e controla a tartaruga para desenhar o resultado na tela.

---

## 2. Pré-processamento da imagem

A primeira etapa da pipeline ocorre no arquivo `img.py`. A imagem é carregada com OpenCV por meio da função `cv2.imread`. Após o carregamento, a imagem é convertida manualmente de BGR para RGB, porque o OpenCV utiliza a ordem de canais BGR por padrão.

Em seguida, a imagem RGB é convertida para escala de cinza. Essa conversão reduz a imagem para uma matriz bidimensional de intensidades, o que simplifica as etapas seguintes de segmentação e detecção de bordas.

Depois da conversão, foi aplicada uma suavização gaussiana implementada manualmente com NumPy. O objetivo da suavização é reduzir ruídos e pequenas variações locais da imagem antes da segmentação e da detecção de bordas.

O filtro gaussiano foi criado por meio de uma função própria que gera o kernel 2D, e a aplicação do filtro foi feita com uma função de convolução implementada manualmente.

---

## 3. Segmentação do cachorro

Após o pré-processamento, foi necessário separar o cachorro do fundo da imagem. Para isso, foi utilizada uma limiarização automática com o método de Otsu, também implementado manualmente.

O método de Otsu analisa o histograma da imagem em escala de cinza e escolhe um limiar que separa os pixels em dois grupos. No caso da imagem utilizada, o cachorro possui regiões mais escuras que o fundo. Por isso, os pixels com intensidade abaixo do limiar calculado foram classificados como parte do objeto principal.

A máscara binária inicial gerada pela limiarização ainda podia conter ruídos e pequenas regiões indesejadas. Para corrigir isso, foram aplicadas operações morfológicas implementadas com NumPy:

- erosão, para remover pequenos ruídos;
- dilatação, para recuperar regiões relevantes;
- abertura, para eliminar componentes pequenas;
- fechamento, para preencher falhas internas na máscara.

Depois dessas operações, foi selecionada a maior componente conectada da máscara. Essa decisão foi tomada porque o cachorro é o principal objeto da imagem e ocupa a maior região escura conectada. Assim, pequenos ruídos ou partes do fundo que ainda permaneceram na imagem foram descartados.

Também foi necessário remover uma região de sombra próxima à pata do cachorro. Essa sombra estava sendo interpretada como parte do objeto, gerando pontos indesejados no desenho final. Para resolver isso, foi criada uma máscara específica para eliminar essa região da segmentação antes da detecção de bordas.

Essa etapa foi importante porque, se a sombra permanecesse na máscara, ela também seria processada pelo Sobel e enviada para o Turtlesim como se fosse parte do contorno do cachorro.

---

## 4. Detecção de bordas

A detecção de bordas foi feita com o operador de Sobel, implementado manualmente com NumPy.

Foram utilizados dois kernels:

- um kernel para detectar variações horizontais;
- um kernel para detectar variações verticais.

A partir desses dois resultados, foi calculada a magnitude do gradiente. A magnitude representa a intensidade da variação entre pixels vizinhos. Regiões com variação mais forte são interpretadas como bordas.

Antes de aplicar o Sobel, a imagem em escala de cinza foi multiplicada pela máscara do cachorro. Dessa forma, a detecção de bordas ficou limitada à região do objeto principal. Essa decisão foi importante para evitar que bordas do fundo ou da sombra fossem detectadas como parte do desenho.

Depois do cálculo do gradiente, foi aplicada uma limiarização nas bordas. Apenas os pixels com magnitude acima do limiar definido foram mantidos. O resultado foi uma imagem binária contendo os pontos de borda do cachorro.

Por fim, os pontos do contorno foram extraídos com `np.where`, que retorna as posições dos pixels classificados como borda. Como o número de pontos poderia ser muito grande para o Turtlesim, foi feita uma subamostragem para limitar a quantidade de coordenadas enviadas ao robô simulado.

O resultado dessa etapa é salvo em:

```bash
outputs/contour_points.npy
```

Esse arquivo contém os pontos do contorno no espaço da imagem.

---

## 5. Mapeamento para o espaço do Turtlesim

O arquivo `coordenadas.py` é responsável por transformar os pontos extraídos da imagem em coordenadas compatíveis com o Turtlesim.

Na imagem, as coordenadas seguem o padrão de pixels:

- o eixo `x` cresce para a direita;
- o eixo `y` cresce para baixo.

Já no Turtlesim, o espaço de coordenadas vai aproximadamente de `0` a `11`, e o eixo `y` cresce para cima. Por isso, foi necessário inverter o eixo vertical durante o mapeamento.

Além disso, o código calcula a bounding box dos pontos do cachorro, ou seja, a menor região que contém todos os pontos extraídos. Isso evita mapear a imagem inteira e permite centralizar melhor o cachorro na janela do Turtlesim.

O fator de escala é calculado usando o menor valor entre a escala horizontal e a escala vertical. Essa escolha preserva a proporção do cachorro.

O mapeamento segue a lógica:

```python
x_turtle = centro_turtle_x + (x_img - centro_img_x) * escala
y_turtle = centro_turtle_y - (y_img - centro_img_y) * escala
```

O sinal negativo no cálculo de `y_turtle` é usado para inverter o eixo vertical.

O resultado é salvo em:

```bash
outputs/contour_turtle.npy
```

Esse arquivo contém os pontos do contorno já convertidos para o espaço do Turtlesim.

---

## 6. Controle da tartaruga com ROS 2

O arquivo `desenhar_turtle.py` implementa o controle da tartaruga no Turtlesim usando ROS 2.

O código cria um nó com `rclpy` e utiliza três recursos principais do Turtlesim:

- o tópico `/turtle1/cmd_vel`, usado para enviar comandos de velocidade;
- o serviço `/turtle1/set_pen`, usado para ligar e desligar a caneta;
- o serviço `/turtle1/teleport_absolute`, usado para posicionar a tartaruga em coordenadas específicas.

Como os pontos extraídos representam uma nuvem de pontos do contorno, e não uma trajetória contínua perfeitamente ordenada, a solução adotada foi desenhar ponto por ponto. Para cada coordenada, a tartaruga levanta a caneta, teleporta até o ponto, abaixa a caneta e faz uma pequena marca.

Essa estratégia foi escolhida porque tentar ligar todos os pontos em sequência gerava linhas artificiais entre partes desconectadas do contorno. Ao desenhar os pontos individualmente, o resultado visual fica mais fiel ao contorno extraído da imagem.

Embora a tartaruga não percorra uma única linha contínua, ela percorre as coordenadas extraídas do contorno e reproduz a forma do cachorro por meio de marcas discretas no espaço do Turtlesim.

---

## 7. Dificuldades encontradas

Uma das principais dificuldades foi separar corretamente o cachorro da sombra próxima à pata. A sombra possuía intensidade semelhante a algumas partes do cachorro e, por isso, era inicialmente interpretada como parte do objeto. Diferente do resto das sombras da imagem, essa em específica colada na pata da direita, sempre era interpretada como parte do corpo do cachorro.

Para resolver esse problema, foi feita uma etapa de remoção da região da sombra na máscara do objeto. Essa decisão melhorou a segmentação e reduziu a presença de pontos indesejados.

Outra dificuldade foi transformar os pontos extraídos em uma trajetória contínua. Como a extração de bordas gera uma nuvem de pontos, os pontos não ficam naturalmente ordenados como um caminho único. Quando a tartaruga tentava ligar os pontos em sequência, o desenho ficava incorreto, pois surgiam linhas entre regiões que não deveriam estar conectadas e a tartaruga alucinava e criava linhas que pareciam aleatórias.

Por esse motivo, a estratégia final foi desenhar os pontos individualmente, evitando conexões falsas entre partes diferentes do contorno. Essa abordagem priorizou a fidelidade visual do resultado em vez de forçar uma trajetória contínua artificial.

---

## 8. Conclusão

O projeto implementa uma pipeline completa de visão computacional e controle robótico em ambiente simulado. A imagem é carregada, pré-processada, segmentada, tem seus contornos extraídos e convertidos para coordenadas do Turtlesim.

A implementação respeita a restrição de usar OpenCV apenas para carregar a imagem, enquanto as etapas de processamento, segmentação, morfologia, convolução e detecção de bordas foram implementadas com NumPy.

O controle da tartaruga foi feito com ROS 2, utilizando serviços e tópicos do Turtlesim para reproduzir o contorno extraído. Apesar das limitações relacionadas à ordenação dos pontos, a solução permite visualizar o cachorro no Turtlesim de forma coerente com os contornos obtidos pela pipeline de visão computacional.