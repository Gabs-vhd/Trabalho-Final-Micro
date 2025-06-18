import pygame
from config import * # Importa as constantes
from classes.effects import Bullet 


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
        self.anim_speed = 10

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