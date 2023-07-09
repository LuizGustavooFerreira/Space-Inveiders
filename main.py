import pygame
import os
import random
from pygame import mixer
from button import Button

pygame.init()

# Constantes
WIDTH, HEIGHT = 854, 480
TELA = pygame.display.set_mode((WIDTH, HEIGHT))
CINZA = (128, 128, 128)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
icone = pygame.image.load(os.path.join("image", "player.png"))
pygame.display.set_icon(icone)  # Icone da janela

# Imagem de fundo do jogo
FUNDO = pygame.transform.smoothscale(pygame.image.load(
    os.path.join("image", "background.png")), (WIDTH, HEIGHT))

# Carregar imagem das naves
# Inimigos:
NAVE_VERMELHA = pygame.image.load(os.path.join("image", "inimigo1.png"))
NAVE_VERDE = pygame.image.load(os.path.join("image", "inimigo2.png"))
# Player
PLAYER = pygame.image.load(os.path.join("image", "player.png"))
# Lasers
LASER_VERMELHO = pygame.image.load(os.path.join("image", "laser_vermelho.png"))
LASER_VERDE = pygame.image.load(os.path.join("image", "laser_verde.png"))
LASER_AZUL = pygame.image.load(os.path.join("image", "laser_azul.png"))

# Sons do jogo
# Menu
musicaMenu = mixer.Sound(os.path.join("sound", "musicaMenu.wav"))
musicaMenu.set_volume(0.4)
# Musica de fundo
musicaBackground = mixer.Sound(os.path.join("sound", "musicaBackground.wav"))
musicaBackground.set_volume(0.05)
musicaBackground.stop()
# Tiro do player
tiro1 = mixer.Sound(os.path.join("sound", "tiro1.wav"))
tiro1.set_volume(0.2)
# Tiro dos inimigos
tiro2 = mixer.Sound(os.path.join("sound", "tiro2.wav"))
tiro2.set_volume(0.08)
tiro3 = mixer.Sound(os.path.join("sound", "tiro3.wav"))
tiro3.set_volume(0.08)
# Explosões
explosao1 = mixer.Sound(os.path.join("sound", "explosao1.wav"))
explosao1.set_volume(0.2)
explosao2 = mixer.Sound(os.path.join("sound", "explosao2.wav"))
explosao2.set_volume(0.2)
# Hit - quando o player recebe dano
hit = mixer.Sound(os.path.join("sound", "hit.wav"))
hit.set_volume(0.05)


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        # Altera onde o laser aparecerá
        window.blit(self.img, (self.x+8, self.y-25))

    def move(self, vel):
        self.y += vel  # Move o laser apenas no eixo Y (vertical)

    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Nave:
    COOLDOWN = 30  # Tempo de espera entre cada tiro

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.nave_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.nave_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            # Tira o laser da tela se ultrapassar a altura da janela
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            # Caso o laser acerte o player, ativa
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)
                hit.play()

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            tiro1.play()

    def get_width(self):
        return self.nave_img.get_width()

    def get_height(self):
        return self.nave_img.get_height()


class Player(Nave):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.nave_img = PLAYER
        self.laser_img = LASER_AZUL
        self.mask = pygame.mask.from_surface(self.nave_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)
                            # Barulho de explosão diferentes
                            explosao = random.randint(1, 2)
                            if explosao == 1:
                                explosao1.play()
                            elif explosao == 2:
                                explosao2.play()

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    # Criando a barra de vida embaixo da nave
    def healthbar(self, window):
        # Barra vermelha
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y +
                         self.nave_img.get_height() + 10, self.nave_img.get_width(), 10))
        # Barra verde
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.nave_img.get_height() +
                         10, self.nave_img.get_width() * (self.health/self.max_health), 10))
        # Vida
        live_font = pygame.font.SysFont("arial", 10)
        live_text = live_font.render(f"{self.health}", 1, (0, 0, 0))
        TELA.blit(live_text, (self.x + 22, self.y +
                  self.nave_img.get_height() + 9, self.nave_img.get_width(), 10))


class Inimigo(Nave):
    COLOR_MAP = {
        "red": (NAVE_VERMELHA, LASER_VERMELHO),
        "green": (NAVE_VERDE, LASER_VERDE)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.nave_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.nave_img)

    # A nave inimiga só se moverá no eixo Y(vertical)
    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            # Altera onde o laser inimigo aparecerá, de acordo com a posiçao da nave dele
            laser = Laser(self.x, self.y+50, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            tiro = random.randint(1, 2)  # Barulhos de tiro diferentes
            if tiro == 1:
                tiro2.play()
            elif tiro == 2:
                tiro3.play()


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


def main():
    musicaMenu.stop()
    musicaBackground.play(-1)
    run = True
    FPS = 60
    level = 0
    lives = 5

    # Estilo da fonte, onde o segundo parâmetro é o tamanho da fonte
    # Vidas e nível
    main_font = pygame.font.SysFont("arial", 30)

    inimigos = []
    # Quantos inimigos aparecerão
    wave_length = 5
    # Velocidade da nave inimiga
    inimigo_vel = 1

    # Velocidade do player
    player_vel = 10
    # Velocidade do laser
    laser_vel = 5

    # Define onde o player aparecerá no inicio da partida (eixos x e y)
    player = Player(397, 390)

    # Velocidade do jogo
    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    # Função "restart", adiciona os inimigos e o player na tela novamente
    def redraw_window():
        TELA.blit(FUNDO, (0, 0))
        lives_label = main_font.render(f"Vidas: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Nivel: {level}", 1, (255, 255, 255))

        TELA.blit(lives_label, (10, 10))
        TELA.blit(level_label, (WIDTH-level_label.get_width()-10, 10))

        for inimigo in inimigos:
            inimigo.draw(TELA)

        player.draw(TELA)

        if lost:
            reiniciar()

        pygame.display.update()

    while run:
        pygame.display.set_caption("Space Invaders")  # Legenda da janela
        # Tempo do jogo
        clock.tick(FPS)

        redraw_window()

        # Contagem de mortes
        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS*3:
                run = False
            else:
                continue

        # Aumenta o nível se não existirem mais inimigos
        if len(inimigos) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                inimigo = Inimigo(random. randrange(
                    50, WIDTH-100), random.randrange(-1500, -100), random.choice(["red", "green"]))
                inimigos.append(inimigo)

        # Evento quit (X)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # Eventos de pressionamento de teclas
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x-player_vel > 0:
            player.x -= player_vel
        if keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width() < WIDTH:
            player.x += player_vel
        if keys[pygame.K_UP] and player.y - player_vel > 0:
            player.y -= player_vel
        if keys[pygame.K_DOWN] and player.y - player_vel+player.get_height()+15 < HEIGHT:
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()
        if keys[pygame.K_ESCAPE]:
            run = False
            main_menu()

        for inimigo in inimigos[:]:
            inimigo.move(inimigo_vel)
            inimigo.move_lasers(laser_vel, player)

            if random.randrange(0, 2*60) == 1:
                inimigo.shoot()

            if collide(inimigo, player):
                explosao1.play()
                player.health -= 10
                inimigos.remove(inimigo)

            elif inimigo.y + inimigo.get_height() > HEIGHT:
                lives -= 1
                inimigos.remove(inimigo)

        player.move_lasers(-laser_vel, inimigos)
# Menu de inicio


def main_menu():
    fonte_menu = pygame.font.SysFont("verdana", 40)
    pygame.display.set_caption("Menu")
    musicaBackground.stop()
    musicaMenu.play(-1)
    while True:
        TELA.fill(PRETO)

        MENU_MOUSE_POS = pygame.mouse.get_pos()

        PLAY_BUTTON = Button(pos=(WIDTH/2, HEIGHT/2-30), text_input="JOGAR",
                             font=fonte_menu, base_color=BRANCO, hovering_color=CINZA)
        QUIT_BUTTON = Button(pos=(WIDTH/2, HEIGHT/2+30), text_input="SAIR",
                             font=fonte_menu, base_color=BRANCO, hovering_color=CINZA)

        for button in [PLAY_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(TELA)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    main()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    exit()

        pygame.display.update()


# Menu de reinicio
def reiniciar():
    fonte_reiniciar = pygame.font.SysFont("verdana", 40)
    pygame.display.set_caption("Tela de reinicio")
    musicaBackground.stop()
    musicaMenu.play(-1)
    while True:
        MENU_MOUSE_POS = pygame.mouse.get_pos()

        RETRY_BUTTON = Button(pos=(WIDTH/2, HEIGHT/2-30), text_input="REINICIAR",
                              font=fonte_reiniciar, base_color=BRANCO, hovering_color=PRETO)
        QUIT_BUTTON = Button(pos=(WIDTH/2, HEIGHT/2+30), text_input="SAIR",
                             font=fonte_reiniciar, base_color=BRANCO, hovering_color=PRETO)
        # Mensagem "Você perdeu"
        lost_font = pygame.font.SysFont("verdana", 20)
        lost_label = lost_font.render("Voce perdeu!", 1, (255, 0, 0))
        TELA.blit(lost_label, (WIDTH/2-lost_label.get_width()/2, HEIGHT/2+65))

        for button in [RETRY_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(TELA)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if RETRY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    main()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    exit()

        pygame.display.update()


main_menu()
