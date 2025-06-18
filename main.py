import pygame
import serial
import time
import random
import math
import os

# --- Constantes e Configurações ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PLAYER_SPEED = 50 # Velocidade do jogador ajustável

# --- Configurações do Arduino ---
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200

#==============================================================================
# CLASSE DO JOGADOR
#==============================================================================
class Player(pygame.sprite.Sprite):
    def __init__(self, player_anim_frames, bullet_image, gun_sound):
        super().__init__()
        
        self.animation_frames = player_anim_frames
        self.current_frame = 0
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 60))
        
        self.bullet_image = bullet_image
        self.gun_sound = gun_sound
        self.speed = PLAYER_SPEED
        
        self.lives = 3
        self.heat = 0.0
        self.max_heat = 100.0
        self.heat_per_shot = 13.0
        self.cooldown_rate = 2.5

        self.last_anim_update = pygame.time.get_ticks()
        self.anim_speed = 30

    def update(self, dt, screen):
        self.animate()
        self.cool_down(dt)
        self.rect.clamp_ip(screen.get_rect())

    def cool_down(self, dt):
        self.heat -= self.cooldown_rate * dt * 10
        if self.heat < 0:
            self.heat = 0
            
    def move(self, dx, dy):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

    def shoot(self, all_sprites, bullets):
        if self.heat <= (self.max_heat - self.heat_per_shot):
            self.heat += self.heat_per_shot
            if self.heat > self.max_heat:
                self.heat = self.max_heat
                
            bullet = Bullet(self.rect.centerx, self.rect.top, self.bullet_image)
            all_sprites.add(bullet)
            bullets.add(bullet)
            self.gun_sound.play()
    
    def animate(self):
        now = pygame.time.get_ticks()
        if now - self.last_anim_update > self.anim_speed:
            self.last_anim_update = now
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            old_center = self.rect.center
            self.image = self.animation_frames[self.current_frame]
            self.rect = self.image.get_rect(center=old_center)

#==============================================================================
# CLASSE DO INIMIGO
#==============================================================================
class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_anim_frames, target_player):
        super().__init__()
        self.animation_frames = enemy_anim_frames
        self.current_frame = 0
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect()
        
        self.target_player = target_player
        self.shoot_cooldown = random.randint(1500, 3500)
        self.last_shot_time = pygame.time.get_ticks()

        self.movement_type = random.choice(['straight', 'diagonal', 'curve'])
        start_x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        start_y = -self.rect.height
        self.pos = pygame.math.Vector2(start_x, start_y)
        self.vel = pygame.math.Vector2(0, 0)
        if self.movement_type == 'straight': self.vel = pygame.math.Vector2(0, 3)
        elif self.movement_type == 'diagonal': self.vel = pygame.math.Vector2(random.choice([-2, 2]), 2)
        elif self.movement_type == 'curve':
            self.vel = pygame.math.Vector2(0, 2)
            self.angle = 0
            self.angle_speed = random.choice([-1, 1]) * 2
        self.rect.topleft = self.pos
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_speed = 75

    def update(self, all_sprites_group, enemy_bullets_group):
        self.animate()
        self.pos += self.vel
        if self.movement_type == 'curve':
            self.angle += self.angle_speed
            self.pos.x += math.sin(math.radians(self.angle)) * 3
        self.rect.topleft = self.pos
        
        self.try_to_shoot(all_sprites_group, enemy_bullets_group)

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def try_to_shoot(self, all_sprites, enemy_bullets):
        now = pygame.time.get_ticks()
        if self.target_player.alive() and now - self.last_shot_time > self.shoot_cooldown:
            self.last_shot_time = now
            player_pos = pygame.math.Vector2(self.target_player.rect.center)
            enemy_pos = pygame.math.Vector2(self.rect.center)
            try:
                direction = (player_pos - enemy_pos).normalize()
            except ValueError:
                direction = pygame.math.Vector2(0, 1)
            bullet = EnemyBullet(enemy_pos, direction)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)

    def animate(self):
        now = pygame.time.get_ticks()
        if now - self.last_anim_update > self.anim_speed:
            self.last_anim_update = now
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            old_center = self.rect.center
            self.image = self.animation_frames[self.current_frame]
            self.rect = self.image.get_rect(center=old_center)

#==============================================================================
# CLASSE DO BOMBARDDEIRO (COM MOVIMENTO DE CIMA PARA BAIXO)
#==============================================================================
class Bomber(pygame.sprite.Sprite):
    def __init__(self, bomber_anim_frames):
        super().__init__()
        self.animation_frames = bomber_anim_frames
        self.current_frame = 0
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect()

        # Atributos específicos do Bombardeiro
        self.health = 5
        # --- MUDANÇA 1: Trocamos a velocidade de X para Y ---
        self.speed_y = 1 # Move-se lentamente para baixo

        # --- MUDANÇA 2: Posição inicial agora é no topo da tela ---
        # Sorteia uma posição horizontal para ele aparecer
        self.rect.centerx = random.randint(self.rect.width // 2, SCREEN_WIDTH - self.rect.width // 2)
        # Posiciona a parte de baixo do avião no topo da tela, para ele "entrar" voando
        self.rect.bottom = 0

        # Lógica de tiro radial (não muda)
        self.shoot_cooldown = 1200
        self.last_shot_time = pygame.time.get_ticks()
        self.bullets_to_fire = 12

        # Lógica de animação (não muda)
        self.last_anim_update = pygame.time.get_ticks()
        self.anim_speed = 100

    def update(self, all_sprites_group, enemy_bullets_group):
        self.animate()
        # --- MUDANÇA 3: O movimento agora é no eixo Y ---
        self.rect.y += self.speed_y
        
        # --- MUDANÇA 4: A verificação de saída da tela agora é para baixo ---
        # Se sair completamente por baixo, se auto-destrói
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
        
        self.try_to_shoot(all_sprites_group, enemy_bullets_group)

    def try_to_shoot(self, all_sprites, enemy_bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_cooldown:
            self.last_shot_time = now
            angle_step = 360 / self.bullets_to_fire
            for i in range(self.bullets_to_fire):
                angle = i * angle_step
                direction = pygame.math.Vector2(1, 0).rotate(angle)
                bullet = EnemyBullet(self.rect.center, direction)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)
    
    def hit(self):
        """Chamado quando o bombardeiro é atingido."""
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True
        return False

    def animate(self):
        now = pygame.time.get_ticks()
        if now - self.last_anim_update > self.anim_speed:
            self.last_anim_update = now
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            old_center = self.rect.center
            self.image = self.animation_frames[self.current_frame]
            self.rect = self.image.get_rect(center=old_center)
#==============================================================================
# CLASSES DE PROJÉTEIS E EFEITOS
#==============================================================================
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, bullet_image):
        super().__init__()
        self.image = bullet_image
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.speed = -10

    def update(self, *args):
        self.rect.y += self.speed
        if self.rect.bottom < 0: self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, center_pos, direction_vector):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        pygame.draw.circle(self.image, (255, 80, 80), (5, 5), 5)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect(center=center_pos)
        self.pos = pygame.math.Vector2(center_pos)
        self.direction = direction_vector
        self.speed = 6

    def update(self, *args):
        self.pos += self.direction * self.speed
        self.rect.center = self.pos
        if not pygame.display.get_surface().get_rect().contains(self.rect):
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, explosion_anim_frames):
        super().__init__()
        self.animation_frames = explosion_anim_frames
        self.current_frame = 0
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect(center=center)
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 40

    def update(self, *args):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.current_frame += 1
            if self.current_frame == len(self.animation_frames):
                self.kill()
            else:
                center = self.rect.center
                self.image = self.animation_frames[self.current_frame]
                self.rect = self.image.get_rect(center=center)

#==============================================================================
# CLASSE PRINCIPAL DO JOGO
#==============================================================================
class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mustang P-51")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 74)
        self.hud_font = pygame.font.Font(None, 40)
        self.running = True
        self.ser = None
        
        self.assets = {}
        self.load_assets()
        self.setup_serial()

        self.game_state = "intro"
        
        button_img = self.assets['play_button']
        self.play_button_rect = button_img.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 170))
        
        # NOVO: Controle de animação do fundo
        self.bg_current_frame = 0
        self.bg_last_update = pygame.time.get_ticks()
        self.bg_anim_speed = 100 # Milissegundos entre cada frame do fundo

    def load_assets(self):
        main_dir = os.path.dirname(__file__)
        # --- Definição dos diretórios de assets ---
        # É uma boa prática definir todos os caminhos no início do método.
        wallpaper_dir = os.path.join(main_dir, "wallpaper")
        enemy_dir = os.path.join(main_dir, "frame_enemy") # <-- CORREÇÃO: Variável definida aqui.
        plane_dir = os.path.join(main_dir, "frame_plane")
        shot_dir = os.path.join(main_dir, "frame_shot")
        explosion_dir = os.path.join(main_dir, "explosion_flame")
        sound_dir = os.path.join(main_dir, "Sound")

        # --- Carregamento dos assets ---
    
        # CORRIGIDO: Carregamento da animação de fundo
        self.assets['background_anim'] = []
        for i in range(1, 15):
            filename = f"wallpaper{i}.png"
            img = pygame.image.load(os.path.join(wallpaper_dir, filename)).convert()
            # CORRIGIDO: A linha de 'append' agora está DENTRO do loop
            self.assets['background_anim'].append(img)

        self.assets['intro_background'] = pygame.image.load(os.path.join(main_dir, "wallpaper_intro.png")).convert()
        self.assets['play_button'] = pygame.image.load(os.path.join(main_dir, "play_button.png")).convert_alpha()
        self.assets['bullet_img'] = pygame.image.load(os.path.join(shot_dir, "bullet.png")).convert_alpha()
        self.assets['player_anim'] = [pygame.image.load(os.path.join(plane_dir, f"Avi{i}.png")).convert_alpha() for i in range(1, 13)]
        self.assets['enemy_anim'] = [pygame.image.load(os.path.join(enemy_dir, f"enemy{i}.png")).convert_alpha() for i in range(1, 9)]
        self.assets['explosion_anim'] = [pygame.transform.scale(pygame.image.load(os.path.join(explosion_dir, f"boom_flame{i}.png")).convert_alpha(), (75, 75)) for i in range(1, 10)]
    
        # CORRIGIDO: Carregamento do bombardeiro
        self.assets['bomber_anim'] = []
        for i in range(1, 7):
            filename = f"bombardeiro{i}.png"
            # Agora 'enemy_dir' está definido e o caminho será encontrado corretamente
            img = pygame.image.load(os.path.join(enemy_dir, filename)).convert_alpha()
            self.assets['bomber_anim'].append(img)

        # Carregamento de sons
        self.assets['engine_sound'] = pygame.mixer.Sound(os.path.join(sound_dir, "engine.wav"))
        self.assets['explosion_sound'] = pygame.mixer.Sound(os.path.join(sound_dir, "explosion.wav"))
        self.assets['gun_sound'] = pygame.mixer.Sound(os.path.join(sound_dir, "gun_sound.wav"))

    def setup_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
            print(f"Conectado ao Arduino em {SERIAL_PORT}")
        except serial.SerialException:
            print(f"AVISO: Arduino não encontrado. Controle via teclado habilitado.")
            self.ser = None

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()

            if self.game_state == "intro":
                self.handle_intro_events(events)
                self.draw_intro_screen()
            elif self.game_state == "playing":
                self.handle_playing_events(events)
                self.update_playing_state(dt)
                self.draw_playing_screen()
            elif self.game_state == "game_over":
                self.handle_game_over_events(events)
                self.draw_game_over_screen()

            pygame.display.flip()
        
        self.quit()

    def handle_intro_events(self, events):
        for event in events:
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.play_button_rect.collidepoint(event.pos):
                    self.start_new_game()
    
    def draw_intro_screen(self):
        self.screen.blit(self.assets['intro_background'], (0, 0))
        self.screen.blit(self.assets['play_button'], self.play_button_rect)

    def start_new_game(self):
        self.score = 0
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.player = Player(self.assets['player_anim'], self.assets['bullet_img'], self.assets['gun_sound'])
        self.all_sprites.add(self.player)
        self.enemy_spawn_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_spawn_timer, 1100)
        # NOVO: Timer para o Bombardeiro (a cada 60 segundos)
        self.bomber_spawn_timer = pygame.USEREVENT + 2 # Um número de evento diferente
        pygame.time.set_timer(self.bomber_spawn_timer, 60000)
        self.assets['engine_sound'].play(loops=-1)
        self.game_state = "playing"

    def handle_playing_events(self, events):
        for event in events:
            if event.type == pygame.QUIT: self.running = False
            if event.type == self.enemy_spawn_timer and self.game_state == "playing":
                new_enemy = Enemy(self.assets['enemy_anim'], self.player)
                self.all_sprites.add(new_enemy)
                self.enemies.add(new_enemy)
            
            if event.type == self.bomber_spawn_timer and self.game_state == "playing":
                # Só cria um bombardeiro se não houver outro na tela
                if not any(isinstance(sprite, Bomber) for sprite in self.enemies):
                    new_bomber = Bomber(self.assets['bomber_anim'])
                    self.all_sprites.add(new_bomber)
                    self.enemies.add(new_bomber) # Adiciona ao grupo de inimigos gerais
        self.handle_controls()
                
    def handle_controls(self):
        if self.ser is None:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT]: dx = -1
            if keys[pygame.K_RIGHT]: dx = 1
            if keys[pygame.K_UP]: dy = -1
            if keys[pygame.K_DOWN]: dy = 1
            self.player.move(dx, dy)
            if keys[pygame.K_SPACE]:
                self.player.shoot(self.all_sprites, self.bullets)
        elif self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                parts = line.split(',')
                if len(parts) == 4:
                    joy_x, joy_y, joy_btn, shoot_btn = map(int, parts)
                    dx, dy = 0, 0
                    if joy_x < 400: dx = -1
                    elif joy_x > 600: dx = 1
                    if joy_y < 400: dy = -1 
                    elif joy_y > 600: dy = 1 
                    self.player.move(dx, dy)
                    if shoot_btn == 0:
                        self.player.shoot(self.all_sprites, self.bullets)
            except (ValueError, IndexError, UnicodeDecodeError):
                pass
                
    def update_playing_state(self, dt):
        self.player.update(dt, self.screen)
        self.bullets.update()
        self.enemies.update(self.all_sprites, self.enemy_bullets)
        self.enemy_bullets.update()
        self.explosions.update()

        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, True)
    
        # Agora, processamos cada inimigo que foi atingido
        for enemy_hit in hits:
            # Cria uma pequena explosão no ponto de impacto
            explosion_point = hits[enemy_hit][0].rect.center
            explosion = Explosion(explosion_point, self.assets['explosion_anim'])
            self.all_sprites.add(explosion)
            self.explosions.add(explosion)
        
            # Verifica se o inimigo é um Bombardeiro
            if isinstance(enemy_hit, Bomber):
                # Chama o método 'hit()' do bombardeiro. Se retornar True, ele foi destruído.
                if enemy_hit.hit():
                    self.score += 50 # Adiciona 50 pontos
                    self.assets['explosion_sound'].play() # Som de explosão maior
            else:
                # Se for um inimigo comum, ele é destruído na hora
                enemy_hit.kill()
                self.score += 10 # Adiciona 10 pontos
                self.assets['explosion_sound'].play()
        
        enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, True, pygame.sprite.collide_circle)
        bullet_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_circle)
        if enemy_hits or bullet_hits:
            self.player_hit()

    def draw_playing_screen(self):
        # --- MODIFICAÇÃO PARA O FUNDO ANIMADO ---
        now = pygame.time.get_ticks()
        if now - self.bg_last_update > self.bg_anim_speed:
            self.bg_last_update = now
            self.bg_current_frame = (self.bg_current_frame + 1) % len(self.assets['background_anim'])
        current_bg_image = self.assets['background_anim'][self.bg_current_frame]
        self.screen.blit(current_bg_image, (0, 0))
    
        self.all_sprites.draw(self.screen)
    
        # --- CÓDIGO FALTANDO PARA A PONTUAÇÃO ---
        # Re-adicione este bloco ao seu método:
        score_text = f"Pontos: {self.score}"
        text_surface = self.hud_font.render(score_text, True, WHITE)
        text_rect = text_surface.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
        self.screen.blit(text_surface, text_rect)
        # -----------------------------------------
    
        self.send_data_to_arduino()

    def player_hit(self):
        if self.player.alive():
            self.player.lives -= 1
            self.assets['explosion_sound'].play()
            explosion = Explosion(self.player.rect.center, self.assets['explosion_anim'])
            self.all_sprites.add(explosion)
            self.explosions.add(explosion)
            if self.player.lives <= 0:
                self.end_game()

    def end_game(self):
        self.assets['engine_sound'].stop()
        if self.player.alive(): self.player.kill() 
        self.game_state = "game_over"

    def handle_game_over_events(self, events):
        for event in events:
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: self.game_state = "intro"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self.game_state = "intro"
                
    def draw_game_over_screen(self):
        self.screen.blit(self.assets['background_anim'][0], (0, 0))
        self.all_sprites.draw(self.screen)
        
        text = self.font.render("Killed in Action", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40))
        self.screen.blit(text, text_rect)

        final_score_text = f"Sua pontuacao: {self.score}"
        score_surface = self.hud_font.render(final_score_text, True, WHITE)
        score_rect = score_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40))
        self.screen.blit(score_surface, score_rect)
        
        small_font = pygame.font.Font(None, 36)
        restart_text = small_font.render("Clique ou pressione ENTER para voltar", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50))
        self.screen.blit(restart_text, restart_rect)

    def send_data_to_arduino(self):
        if self.ser and self.player.alive():
            try:
                heat_level = int(self.player.heat)
                lives_count = self.player.lives
                data_string = f"H:{heat_level},L:{lives_count}\n"
                self.ser.write(data_string.encode('utf-8'))
            except Exception: pass

    def quit(self):
        if self.ser: self.ser.close()
        pygame.quit()

#==============================================================================
# PONTO DE ENTRADA DO PROGRAMA
#==============================================================================
if __name__ == '__main__':
    game = Game()
    game.run()