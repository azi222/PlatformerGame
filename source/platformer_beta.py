import pygame as pg
import pytmx
import json
import sys
import os
import traceback

pg.init()

def log(message):
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")

log("Starting the game.")

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 80
TILE_SCALE = 2

def resource_path(relative_path):
    """ Получение абсолютного пути к ресурсу, работает для обычного файла (.py) и для PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    log(f"BASE_DIR: {BASE_DIR}")

    background_path = resource_path("Resources/map/background.jpg")
    log(f"Background path: {background_path}")

    background = pg.image.load(background_path)
    background = pg.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    font = pg.font.Font(None, 36)
except Exception as e:
    log(f"Error during initialization: {e}")
    log(traceback.format_exc())
    raise

class Platform(pg.sprite.Sprite):
    def __init__(self, image, x, y, width, height):
        super(Platform, self).__init__()
        log("Initializing Platform")
        self.image = pg.transform.scale(image, (width * TILE_SCALE, height * TILE_SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SCALE
        self.rect.y = y * TILE_SCALE

class Player(pg.sprite.Sprite):
    def __init__(self, map_width, map_height):
        super(Player, self).__init__()
        log("Initializing Player")
        self.hp = 10
        self.damage_timer = pg.time.get_ticks()
        self.damage_interval = 1000
        self.load_animations()
        self.current_animation = self.idle_animation_right
        self.image = self.current_animation[0]
        self.current_image = 0
        self.direction = "right"
        self.rect = self.image.get_rect()
        self.rect.center = (200, 100)

        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = 2
        self.is_jumping = False
        self.map_width = map_width * TILE_SCALE
        self.map_height = map_height * TILE_SCALE

        self.timer = pg.time.get_ticks()
        self.interval = 200

    def load_animations(self):
        log("Loading Player animations")
        tile_size = 16
        tile_scale = 4

        self.idle_animation_right = []
        num_image = 2
        try:
            spritesheet = pg.image.load(resource_path("Resources/sprites/Sprite Pack 2/1 - Onion Lad/Idle (16 x 16).png"))
        except Exception as e:
            log(f"Error loading Player idle spritesheet: {e}")
            log(traceback.format_exc())
            raise

        for i in range(num_image):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_scale * tile_size, tile_scale * tile_size))
            self.idle_animation_right.append(image)
        self.idle_animation_left = [pg.transform.flip(image, True, False) for image in self.idle_animation_right]

        self.run_animation_right = []
        num_image = 2
        try:
            spritesheet = pg.image.load(resource_path("Resources/sprites/Sprite Pack 2/1 - Onion Lad/Run_&_Jump (16 x 16).png"))
        except Exception as e:
            log(f"Error loading Player run spritesheet: {e}")
            log(traceback.format_exc())
            raise

        for i in range(num_image):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_scale * tile_size, tile_scale * tile_size))
            self.run_animation_right.append(image)
        self.run_animation_left = [pg.transform.flip(image, True, False) for image in self.run_animation_right]

    def update(self, platforms):
        keys = pg.key.get_pressed()
        if keys[pg.K_SPACE] and not self.is_jumping:
            self.jump()
        if keys[pg.K_a]:
            if self.current_animation != self.run_animation_left:
                self.current_animation = self.run_animation_left
                self.current_image = 0
                self.direction = "left"
            self.velocity_x -= 2
        elif keys[pg.K_d]:
            if self.current_animation != self.run_animation_right:
                self.current_animation = self.run_animation_right
                self.current_image = 0
                self.direction = "right"
            self.velocity_x += 2
        else:
            if self.current_animation in [self.run_animation_right, self.run_animation_left]:
                self.current_animation = self.idle_animation_right if self.current_animation == self.run_animation_right else self.idle_animation_left
                self.current_image = 0
            self.velocity_x = 0

        self.rect.x += self.velocity_x
        if self.rect.left < 0:
            self.rect.x = 0
        if self.rect.x > 1250:
            self.rect.y = 50
            self.rect.x -= 10

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity_x < 0:
                    self.rect.left = platform.rect.right

        self.velocity_y += self.gravity
        new_y = self.rect.y + self.velocity_y

        if new_y + self.rect.height > self.map_height:
            self.rect.y = self.map_height - self.rect.height
            self.velocity_y = 0
            self.is_jumping = False
        else:
            self.rect.y = new_y

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.is_jumping = False
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()

    def jump(self):
        self.velocity_y = -30
        self.is_jumping = True

    def get_damage(self):
        if pg.time.get_ticks() - self.damage_timer > self.damage_interval:
            self.hp -= 1
            self.damage_timer = pg.time.get_ticks()

class Cheese(pg.sprite.Sprite):
    def __init__(self, map_width, map_height, start_pos, final_pos):
        super(Cheese, self).__init__()
        log("Initializing Cheese")
        self.load_animations()
        self.current_animation = self.animation
        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.rect.bottomleft = start_pos

        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = 2
        self.is_jumping = False
        self.map_width = map_width * TILE_SCALE
        self.map_height = map_height * TILE_SCALE
        self.left_edge = start_pos[0]
        self.right_edge = final_pos[0] + self.image.get_width()

        self.timer = pg.time.get_ticks()
        self.interval = 200

        self.direction = "right"

    def load_animations(self):
        log("Loading Cheese animations")
        tile_scale = 4
        tile_size = 16

        self.animation = []
        image = pg.image.load(resource_path("Resources/sprites/Sprite Pack 2/8 - Comrade Cheese Puff/Hurt (16 x 16).png"))
        image = pg.transform.scale(image, (tile_scale * tile_size, tile_scale * tile_size))
        self.animation.append(image)
        self.animation.append(pg.transform.flip(image, True, False))

    def update(self, platforms):
        if self.direction == "right":
            self.velocity_x = 10
            if self.rect.right >= self.right_edge:
                self.direction = "left"
        elif self.direction == "left":
            self.velocity_x = -10
            if self.rect.left <= self.left_edge:
                self.direction = "right"

        self.rect.x += self.velocity_x

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity_x < 0:
                    self.rect.left = platform.rect.right

        self.velocity_y += self.gravity
        new_y = self.rect.y + self.velocity_y

        if new_y + self.rect.height > self.map_height:
            self.rect.y = self.map_height - self.rect.height
            self.velocity_y = 0
            self.is_jumping = False
        else:
            self.rect.y = new_y

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.is_jumping = False
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()

class Redic(pg.sprite.Sprite):
    def __init__(self, map_width, map_height, start_pos, final_pos):
        super(Redic, self).__init__()
        log("Initializing Redic")
        self.load_animations()
        self.current_animation = self.animation
        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.rect.bottomleft = start_pos

        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = 2
        self.is_jumping = False
        self.map_width = map_width * TILE_SCALE
        self.map_height = map_height * TILE_SCALE
        self.left_edge = start_pos[0]
        self.right_edge = final_pos[0] + self.image.get_width()

        self.timer = pg.time.get_ticks()
        self.interval = 200

        self.direction = "right"

    def load_animations(self):
        log("Loading Redic animations")
        tile_scale = 4
        tile_size = 16

        self.animation = []
        image = pg.image.load(resource_path("Resources/sprites/Sprite Pack 2/5 - Daikon/Hurt (16 x 32).png"))
        image = pg.transform.scale(image, (tile_scale * tile_size, tile_scale * tile_size))
        self.animation.append(image)
        self.animation.append(pg.transform.flip(image, True, False))

    def update(self, platforms):
        if self.direction == "right":
            self.velocity_x = 5
            if self.rect.right >= self.right_edge:
                self.direction = "left"
        elif self.direction == "left":
            self.velocity_x = -5
            if self.rect.left <= self.left_edge:
                self.direction = "right"

        self.rect.x += self.velocity_x

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity_x < 0:
                    self.rect.left = platform.rect.right

        self.velocity_y += self.gravity
        new_y = self.rect.y + self.velocity_y

        if new_y + self.rect.height > self.map_height:
            self.rect.y = self.map_height - self.rect.height
            self.velocity_y = 0
            self.is_jumping = False
        else:
            self.rect.y = new_y

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity_y = 0
                    self.is_jumping = False
                elif self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()

class Ball(pg.sprite.Sprite):
    def __init__(self, player_rect, direction):
        super(Ball, self).__init__()
        log("Initializing Ball")
        self.direction = direction
        self.speed = 10

        self.image = pg.image.load(resource_path("Resources/sprites/ball.png"))
        self.image = pg.transform.scale(self.image, (30, 30))

        self.rect = self.image.get_rect()
        if self.direction == "right":
            self.rect.x = player_rect.right
        else:
            self.rect.x = player_rect.left
            self.rect.y = player_rect.centery

        self.rect.y = player_rect.centery

    def update(self):
        if self.direction == "right":
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

class Coin(pg.sprite.Sprite):
    def __init__(self, x, y):
        super(Coin, self).__init__()
        log("Initializing Coin")
        self.load_animations()
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.current_image = 0
        self.timer = pg.time.get_ticks()
        self.interval = 200

    def load_animations(self):
        log("Loading Coin animations")
        tile_size = 16
        tile_scale = 2

        self.images = []

        num_images = 5
        spritesheet = pg.image.load(resource_path("Resources/Coin_Gems/MonedaP.png"))

        for i in range(num_images):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_scale * tile_size, tile_scale * tile_size))
            self.images.append(image)

    def update(self):
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image > len(self.images) - 1:
                self.current_image = 0
            self.image = self.images[self.current_image]
            self.timer = pg.time.get_ticks()

class Portal(pg.sprite.Sprite):
    def __init__(self, x, y):
        super(Portal, self).__init__()
        log("Initializing Portal")
        self.load_animations()
        self.image = self.images[0]
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

        self.current_image = 0
        self.timer = pg.time.get_ticks()
        self.interval = 100

    def load_animations(self):
        log("Loading Portal animations")
        tile_size = 64
        tile_scale = 2

        self.images = []

        num_images = 2
        spritesheet = pg.image.load(
            resource_path("Resources/sprites/greenportalspritesheet1.png")).convert_alpha()

        for i in range(num_images):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_scale * tile_size, tile_scale * tile_size))
            self.images.append(image)

    def update(self):
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image > len(self.images) - 1:
                self.current_image = 0
            self.image = self.images[self.current_image]
            self.timer = pg.time.get_ticks()

class Game:
    def __init__(self):
        log("Initializing Game")
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Платформер-бойня")
        self.clock = pg.time.Clock()
        self.level = 1
        self.allcoll_coins = 0
        self.setup()

    def setup(self):
        log("Setting up game level")
        self.mode = "game"
        self.all_sprites = pg.sprite.Group()
        self.collision = pg.sprite.Group()
        self.platrorms = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.balls = pg.sprite.Group()
        self.coins = pg.sprite.Group()
        self.portals = pg.sprite.Group()
        self.collected_coins = 0
        self.is_running = False
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 4

        self.tmx_map = pytmx.load_pygame(resource_path(f"Resources/map/level{self.level}.tmx"))

        self.map_pixel_width = self.tmx_map.width * self.tmx_map.tilewidth * TILE_SCALE
        self.map_pixel_height = self.tmx_map.height * self.tmx_map.tileheight * TILE_SCALE

        self.player = Player(self.map_pixel_width, self.map_pixel_height)
        self.all_sprites.add(self.player)

        for layer in self.tmx_map:
            if layer.name == "Game":
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * self.tmx_map.tilewidth, y * self.tmx_map.tileheight,
                                            self.tmx_map.tilewidth, self.tmx_map.tileheight)
                        self.all_sprites.add(platform)
                        self.platrorms.add(platform)
            elif layer.name == "Coins":
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        coin = Coin(x * self.tmx_map.tilewidth * TILE_SCALE,
                                    y * self.tmx_map.tileheight * TILE_SCALE)
                        self.all_sprites.add(coin)
                        self.coins.add(coin)
                self.coins_amount = len(self.coins.sprites())
            elif layer.name == "Portal":
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        portal = Portal(x * self.tmx_map.tilewidth * TILE_SCALE,
                                        y * self.tmx_map.tileheight * TILE_SCALE)
                        self.all_sprites.add(portal)
                        self.portals.add(portal)
            elif layer.name == "Collision":
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * self.tmx_map.tilewidth, y * self.tmx_map.tileheight,
                                            self.tmx_map.tilewidth, self.tmx_map.tileheight)
                        self.collision.add(platform)

        with open(resource_path(f"Resources/map/level{self.level}_enemies.json"), "r") as json_file:
            data = json.load(json_file)
        for enemy in data["enemies"]:
            if enemy["name"] == "Redic":
                x1 = enemy["start_pos"][0] * TILE_SCALE * self.tmx_map.tilewidth
                y1 = enemy["start_pos"][1] * TILE_SCALE * self.tmx_map.tilewidth
                x2 = enemy["final_pos"][0] * TILE_SCALE * self.tmx_map.tilewidth
                y2 = enemy["final_pos"][1] * TILE_SCALE * self.tmx_map.tilewidth

                redic = Redic(self.map_pixel_width, self.map_pixel_height, [x1, y1], [x2, y2])
                self.enemies.add(redic)
                self.all_sprites.add(redic)
            elif enemy["name"] == "Cheese":
                x1 = enemy["start_pos"][0] * TILE_SCALE * self.tmx_map.tilewidth
                y1 = enemy["start_pos"][1] * TILE_SCALE * self.tmx_map.tilewidth
                x2 = enemy["final_pos"][0] * TILE_SCALE * self.tmx_map.tilewidth
                y2 = enemy["final_pos"][1] * TILE_SCALE * self.tmx_map.tilewidth

                cheese = Cheese(self.map_pixel_width, self.map_pixel_height, [x1, y1], [x2, y2])
                self.enemies.add(cheese)
                self.all_sprites.add(cheese)

        self.run()

    def run(self):
        self.is_running = True
        while self.is_running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(60)
        pg.quit()
        quit()

    def event(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.is_running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_e:
                    ball = Ball(self.player.rect, self.player.direction)
                    self.balls.add(ball)
                    self.all_sprites.add(self.balls)
            if self.mode == "game over":
                if event.type == pg.KEYDOWN:
                    self.setup()

    def update(self):
        if self.player.hp < 0:
            self.mode = "game over"
            return
        for enemy in self.enemies.sprites():
            if pg.sprite.collide_mask(self.player, enemy):
                self.player.get_damage()
        self.player.update(self.platrorms)
        for enemy in self.enemies.sprites():
            enemy.update(self.platrorms)
        self.balls.update()
        for coin in self.coins.sprites():
            coin.update()
        for portal in self.portals.sprites():
            portal.update()
        hits = pg.sprite.spritecollide(self.player, self.coins, True)
        for hit in hits:
            self.collected_coins += 1
            self.allcoll_coins += 1

        hits = pg.sprite.spritecollide(self.player, self.portals, False, pg.sprite.collide_mask)
        if self.collected_coins > self.coins_amount / 2:
            for hit in hits:
                self.level += 1
                if self.level == 4:
                    quit()
                self.setup()

        pg.sprite.groupcollide(self.balls, self.enemies, True, True)
        pg.sprite.groupcollide(self.balls, self.platrorms, True, False)
        self.camera_x = self.player.rect.x - SCREEN_WIDTH // 2
        self.camera_y = self.player.rect.y - SCREEN_HEIGHT // 2

        self.camera_x = max(0, min(self.camera_x, self.map_pixel_width - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, self.map_pixel_height - SCREEN_HEIGHT))

    def draw(self):
        self.screen.blit(background, (0, 0))
        for sprite in self.collision:
            self.screen.blit(sprite.image, sprite.rect.move(-self.camera_x, -self.camera_y))
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, sprite.rect.move(-self.camera_x, -self.camera_y))
        pg.draw.rect(self.screen, pg.Color("red"), (10, 10, self.player.hp * 10, 10))
        pg.draw.rect(self.screen, pg.Color("black"), (10, 10, 100, 10), 1)
        moneytext = font.render(f"{self.allcoll_coins}", True, (0, 0, 0))
        moneytext_rect = moneytext.get_rect(center=(20, 40))
        self.screen.blit(moneytext, moneytext_rect)

        if self.mode == "game over":
            text = font.render("Вы проиграли", True, (255, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)
        pg.display.flip()

def main():
    log("Entering main")
    try:
        game = Game()
    except Exception as e:
        log(f"An error occurred: {e}")
        log(traceback.format_exc())
        raise
    log("Game finished.")

if __name__ == "__main__":
    main()
    log("Game finished.")
