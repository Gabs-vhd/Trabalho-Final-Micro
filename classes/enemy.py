import pygame
import random
import math
from config import * # Importa as constantes
from classes.effects import EnemyBullet

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