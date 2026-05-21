## Descrição do projeto

Este projeto implementa uma pipeline de visão computacional para extrair o as bordas da imagem e reproduzir no Turtlesim usando ROS 2.

O sistema processa a imagem dog.jpg, identifica os pontos do contorno do cachorro, converte esses pontos para o espaço de coordenadas do Turtlesim e controla a tartaruga para desenhar o resultado na tela.

---

## Objetivo

O objetivo do projeto é transformar uma imagem em comandos de movimento para um robô simulado.

Para isso, o sistema realiza as seguintes etapas:

1. Carrega a imagem de entrada;
2. Realiza o pré-processamento da imagem;
3. Detecta os contornos do cachorro;
4. Converte os pontos extraídos para o espaço do Turtlesim;
5. Controla a tartaruga no ROS 2 para desenhar os pontos do contorno.

---

## Dependências

Para executar o projeto, é necessário ter:

- WSL com Ubuntu;
- Python 3;
- ROS 2 instalado;
- Turtlesim instalado;
- NumPy;
- Matplotlib;
- OpenCV.

Caso precise instalar as bibliotecas Python, execute:

```bash
pip install numpy matplotlib opencv-python
```
Caso o Turtlesim não esteja instalado, execute:

```bash
sudo apt install ros-humble-turtlesim
```

---

## Instruções de execução

Em um terminal, digite:
```bash
python3 img.py

```
Depois, no mesmo terminal, digite:
```bash
python3 coordenadas.py

```
Agora em um novo terminal, abra o Turtlesim:

```bash
ros2 run turtlesim turtlesim_node

```

Após abrir, entre no primeiro terminal novamente e rode: 

```bash
python3 desenhar_turtle.py
```
### **Observação:** Toda lógica da programação e motivo de decisões estão explicados na documentação técnica, e os códigos comentados para facilitar o entendimento dos blocos principais.