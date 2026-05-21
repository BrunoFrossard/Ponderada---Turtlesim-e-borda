import rclpy
from rclpy.node import Node

from turtlesim.srv import SetPen, TeleportAbsolute
from geometry_msgs.msg import Twist

import numpy as np
import time


# Classe principal do nó ROS 2.
# Ela herda de Node, permitindo criar publishers, clientes de serviço
# e controlar a tartaruga dentro do ambiente do Turtlesim.
class TurtlePointDrawer(Node):
    def __init__(self):
        super().__init__("turtle_point_drawer")

        # Cria um publisher no tópico /turtle1/cmd_vel.
        # Esse tópico recebe mensagens Twist, usadas para controlar
        # velocidade linear e angular da tartaruga.
        #
        # Neste projeto, ele é usado para fazer uma pequena marca no ponto,
        # simulando um ponto desenhado na tela.
        self.cmd_pub = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)

        # Cria um cliente para o serviço /turtle1/set_pen.
        # Esse serviço permite ligar e desligar a caneta da tartaruga.
        self.pen_cli = self.create_client(SetPen, "/turtle1/set_pen")

        # Cria um cliente para o serviço /turtle1/teleport_absolute.
        # Esse serviço permite mover a tartaruga diretamente para uma posição
        # específica do Turtlesim, sem precisar andar até ela.
        self.teleport_cli = self.create_client(
            TeleportAbsolute,
            "/turtle1/teleport_absolute"
        )

        # Espera os serviços ficarem disponíveis.
        # Isso é necessário porque o código só funciona depois que o
        # turtlesim_node está aberto.
        self.pen_cli.wait_for_service()
        self.teleport_cli.wait_for_service()

        # Carrega os pontos do contorno já convertidos para o espaço do Turtlesim.
        # Esse arquivo é gerado pelo coordenadas.py.
        #
        # Cada ponto tem o formato:
        # [x_turtle, y_turtle]
        try:
            self.pontos = np.load("outputs/contour_turtle.npy")
        except FileNotFoundError:
            
            raise SystemExit(1)

        # Depois de carregar os pontos, inicia o desenho.
        self.desenhar_pontos()

    def set_pen(self, ligada=True, largura=3):
      
        req = SetPen.Request()

        # Define a cor da caneta como branca.
        req.r = 255
        req.g = 255
        req.b = 255

        # Define a espessura da caneta.
        # Uma largura maior ajuda a marca aparecer melhor como ponto.
        req.width = largura

        # req.off controla se a caneta está desligada.
        #
        # off = 0 → caneta ligada
        # off = 1 → caneta desligada
        req.off = 0 if ligada else 1

        # Envia a chamada ao serviço.
        future = self.pen_cli.call_async(req)

        # Aguarda o serviço responder antes de continuar.
        # Isso evita que o próximo comando seja executado antes da caneta mudar.
        rclpy.spin_until_future_complete(self, future, timeout_sec=1.0)

    def teleportar(self, x, y):
        req = TeleportAbsolute.Request()

        req.x = float(x)
        req.y = float(y)
    
        req.theta = 0.0

        future = self.teleport_cli.call_async(req)

        rclpy.spin_until_future_complete(self, future, timeout_sec=1.0)

    def parar(self):
        
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0

        self.cmd_pub.publish(msg)

    def fazer_ponto(self):
        # O Turtlesim não tem um comando específico para desenhar um ponto parado.
        # Então a estratégia usada é fazer a tartaruga andar muito pouco
        # com a caneta ligada.
        
        msg = Twist()
        msg.linear.x = 0.15
        msg.angular.z = 0.0

        # Publica o pequeno movimento para frente.
        self.cmd_pub.publish(msg)

        # Mantém esse movimento por um tempo muito curto.
        time.sleep(0.03)

        self.parar()

    def desenhar_pontos(self):
        # Percorre todos os pontos extraídos do contorno.
        for ponto in self.pontos:
            x, y = ponto

            # desliga a caneta para evitar linhas entre pontos.
            
            self.set_pen(ligada=False)

            # Move a tartaruga diretamente para a coordenada do ponto.
            self.teleportar(x, y)

            self.set_pen(ligada=True, largura=3)
            self.fazer_ponto()

            self.set_pen(ligada=False)

        self.parar()


def main(args=None):
    # Inicializa o sistema ROS 2 para este script.
    rclpy.init(args=args)

    try:
        # Cria o nó responsável por desenhar os pontos.
        # A execução do desenho acontece dentro do construtor da classe.
        node = TurtlePointDrawer()
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == "__main__":
    main()