import pygame

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

