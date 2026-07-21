import pygame
import math
import random

# ==========================================
# CONSTANTS DEL MÓN
# ==========================================
WIDTH, HEIGHT = 1000, 600
WORLD_WIDTH, WORLD_HEIGHT = 3000, 2000
FPS = 60
OCEAN_COLOR = (20, 50, 90)

# ==========================================
# CLASSES DE L'ENTORN
# ==========================================
class Island:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        
        # Generació procedural d'arbres
        self.trees = []
        num_trees = int(radius * 0.3) # Més gran és l'illa, més arbres té
        for _ in range(num_trees):
            # Posició aleatòria dins de la zona d'herba
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, radius - 20)
            tx = math.cos(angle) * dist
            ty = math.sin(angle) * dist
            size = random.randint(10, 22)
            self.trees.append((tx, ty, size))

    def draw(self, screen, cam_x, cam_y):
        draw_x = int(self.x - cam_x)
        draw_y = int(self.y - cam_y)
        
        # Base de l'illa
        pygame.draw.circle(screen, (15, 45, 80), (draw_x, draw_y + 10), self.radius + 20) # Ombra aigua
        pygame.draw.circle(screen, (220, 190, 130), (draw_x, draw_y), self.radius + 6)    # Sorra
        pygame.draw.circle(screen, (45, 155, 70), (draw_x, draw_y), self.radius)          # Herba
        
        # Dibuixar arbres
        for tx, ty, size in self.trees:
            tree_x = int(draw_x + tx)
            tree_y = int(draw_y + ty)
            # Ombra de l'arbre
            pygame.draw.circle(screen, (30, 110, 50), (tree_x, tree_y + 3), size)
            # Copa de l'arbre
            pygame.draw.circle(screen, (25, 130, 45), (tree_x, tree_y), size)

class Port:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # El port ara està format per dos rectangles (forma de L)
        self.main_dock = pygame.Rect(x, y, 200, 40)
        self.pier = pygame.Rect(x + 60, y + 40, 40, 120)
        # Zona d'aparcament (l'aigua al costat de la passarel·la)
        self.parking_zone = pygame.Rect(x + 100, y + 40, 80, 120)

    def draw(self, screen, cam_x, cam_y):
        # 1. Dibuixar zona d'aparcament (Aigua més clara)
        park_rect = self.parking_zone.copy()
        park_rect.x -= cam_x
        park_rect.y -= cam_y
        pygame.draw.rect(screen, (30, 80, 120), park_rect)
        pygame.draw.rect(screen, (50, 150, 255), park_rect, 2) # Vora brillant

        # 2. Dibuixar fusta del moll
        for rect in [self.main_dock, self.pier]:
            draw_rect = rect.copy()
            draw_rect.x -= cam_x
            draw_rect.y -= cam_y
            
            # Fons de fusta
            pygame.draw.rect(screen, (110, 70, 40), draw_rect)
            pygame.draw.rect(screen, (70, 40, 20), draw_rect, 3)
            
            # Línies dels taulons de fusta
            if rect == self.main_dock:
                for px in range(draw_rect.x + 10, draw_rect.right, 15):
                    pygame.draw.line(screen, (80, 50, 25), (px, draw_rect.top), (px, draw_rect.bottom), 2)
            else:
                for py in range(draw_rect.y + 10, draw_rect.bottom, 15):
                    pygame.draw.line(screen, (80, 50, 25), (draw_rect.left, py), (draw_rect.right, py), 2)

        # 3. Pals d'amarratge
        poles = [(self.x + 10, self.y + 20), (self.x + 190, self.y + 20), 
                 (self.x + 80, self.y + 150), (self.x + 60, self.y + 150)]
        for px, py in poles:
            pygame.draw.circle(screen, (40, 25, 10), (int(px - cam_x), int(py - cam_y)), 6)

class Particle:
    def __init__(self, x, y, vx, vy, size, color, decay):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.alpha = 255
        self.decay = decay

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.size += 3 * dt
        self.alpha -= self.decay * dt

    def draw(self, surface, cam_x, cam_y):
        if self.alpha > 0:
            color = (*self.color, int(self.alpha))
            pygame.draw.circle(surface, color, (int(self.x - cam_x), int(self.y - cam_y)), int(self.size))

# ==========================================
# CLASSE VAIXELL
# ==========================================
class Boat:
    def __init__(self, x, y):
        try:
            self.original_image = pygame.transform.scale(pygame.image.load('boat.png').convert_alpha(), (120, 120))
        except:
            self.original_image = pygame.Surface((120, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(self.original_image, (220, 220, 220), (0, 0, 120, 50))
            pygame.draw.rect(self.original_image, (150, 50, 50), (80, 15, 30, 20)) 

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.rotation = 0.0
        self.angular_velocity = 0.0
        self.radius = 35 
        
        self.acceleration = 300.0
        self.drag = 1.5 
        self.turn_speed = 150.0
        
        self.is_parked = False
        self.particles = []
        self.particle_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def handle_input(self, keys, dt, port):
        speed = math.hypot(self.vx, self.vy)
        
        # Comprovar si el centre del vaixell està dins de la zona d'aparcament
        in_parking_zone = port.parking_zone.collidepoint(self.x, self.y)
        
        if keys[pygame.K_SPACE] and speed < 60 and in_parking_zone:
            self.is_parked = True
            self.vx = 0
            self.vy = 0
            self.angular_velocity = 0
        
        if self.is_parked:
            if keys[pygame.K_w] or keys[pygame.K_s]:
                self.is_parked = False
            else:
                return

        if keys[pygame.K_a]: self.angular_velocity += self.turn_speed * dt
        if keys[pygame.K_d]: self.angular_velocity -= self.turn_speed * dt
            
        rad = math.radians(self.rotation)
        if keys[pygame.K_w]:
            self.vx += math.cos(rad) * self.acceleration * dt
            self.vy -= math.sin(rad) * self.acceleration * dt
        if keys[pygame.K_s]:
            self.vx -= math.cos(rad) * (self.acceleration * 0.4) * dt
            self.vy += math.sin(rad) * (self.acceleration * 0.4) * dt

    def update(self, dt, islands, port):
        if self.is_parked: return

        self.vx -= self.vx * self.drag * dt
        self.vy -= self.vy * self.drag * dt
        self.angular_velocity -= self.angular_velocity * self.drag * dt

        self.rotation += self.angular_velocity * dt

        next_x = self.x + self.vx * dt
        next_y = self.y + self.vy * dt

        # Col·lisions Marges
        if next_x < self.radius: next_x = self.radius; self.vx *= -0.5
        elif next_x > WORLD_WIDTH - self.radius: next_x = WORLD_WIDTH - self.radius; self.vx *= -0.5
        if next_y < self.radius: next_y = self.radius; self.vy *= -0.5
        elif next_y > WORLD_HEIGHT - self.radius: next_y = WORLD_HEIGHT - self.radius; self.vy *= -0.5

        # Col·lisions Illes
        for island in islands:
            dist = math.hypot(next_x - island.x, next_y - island.y)
            min_dist = self.radius + island.radius
            if dist < min_dist:
                angle = math.atan2(next_y - island.y, next_x - island.x)
                next_x = island.x + math.cos(angle) * min_dist
                next_y = island.y + math.sin(angle) * min_dist
                self.vx *= 0.5; self.vy *= 0.5

        # Col·lisions Port (Moll principal i passarel·la)
        for rect in [port.main_dock, port.pier]:
            closest_x = max(rect.left, min(next_x, rect.right))
            closest_y = max(rect.top, min(next_y, rect.bottom))
            dist_port = math.hypot(next_x - closest_x, next_y - closest_y)
            
            if dist_port < self.radius:
                angle_port = math.atan2(next_y - closest_y, next_x - closest_x)
                next_x = closest_x + math.cos(angle_port) * self.radius
                next_y = closest_y + math.sin(angle_port) * self.radius
                self.vx *= 0.5; self.vy *= 0.5

        self.x = next_x
        self.y = next_y

        # Partícules
        speed = math.hypot(self.vx, self.vy)
        if speed > 20:
            movement_angle = math.atan2(self.vy, self.vx)
            spawn_x = self.x - math.cos(movement_angle) * 45
            spawn_y = self.y - math.sin(movement_angle) * 45
            self.particles.append(Particle(
                spawn_x + random.uniform(-6, 6), spawn_y + random.uniform(-6, 6),
                self.vx * -0.15, self.vy * -0.15, 
                random.uniform(4, 7), (220, 240, 255), 120
            ))

        for p in self.particles[:]:
            p.update(dt)
            if p.alpha <= 0:
                self.particles.remove(p)

    def draw(self, screen, cam_x, cam_y, port):
        self.particle_surface.fill((0, 0, 0, 0))
        for p in self.particles:
            p.draw(self.particle_surface, cam_x, cam_y)
        screen.blit(self.particle_surface, (0, 0))

        rotated = pygame.transform.rotate(self.original_image, self.rotation)
        rect = rotated.get_rect(center=(int(self.x - cam_x), int(self.y - cam_y)))
        screen.blit(rotated, rect)
        
        # Mostrar missatges
        font = pygame.font.SysFont(None, 24)
        if self.is_parked:
            text = font.render("AMARRAT (W per sortir)", True, (50, 255, 50))
            screen.blit(text, (rect.x - 20, rect.y - 25))
        elif port.parking_zone.collidepoint(self.x, self.y):
            text = font.render("Prem ESPAI per aparcar", True, (255, 255, 50))
            screen.blit(text, (rect.x - 20, rect.y - 25))

# ==========================================
# MINI-MAPA
# ==========================================
def draw_minimap(screen, boat, islands, port):
    map_w, map_h = 240, 160
    map_x, map_y = WIDTH - map_w - 20, HEIGHT - map_h - 20
    
    pygame.draw.rect(screen, (10, 30, 60, 200), (map_x, map_y, map_w, map_h))
    pygame.draw.rect(screen, (255, 255, 255), (map_x, map_y, map_w, map_h), 2)
    
    scale_x = map_w / WORLD_WIDTH
    scale_y = map_h / WORLD_HEIGHT
    
    # Port (Moll i passarel·la)
    pygame.draw.rect(screen, (150, 80, 40), (map_x + port.main_dock.x * scale_x, map_y + port.main_dock.y * scale_y, port.main_dock.width * scale_x, port.main_dock.height * scale_y))
    pygame.draw.rect(screen, (150, 80, 40), (map_x + port.pier.x * scale_x, map_y + port.pier.y * scale_y, port.pier.width * scale_x, port.pier.height * scale_y))
    
    for island in islands:
        pygame.draw.circle(screen, (40, 150, 70), (int(map_x + island.x * scale_x), int(map_y + island.y * scale_y)), int(island.radius * scale_x))
        
    pygame.draw.circle(screen, (255, 50, 50), (int(map_x + boat.x * scale_x), int(map_y + boat.y * scale_y)), 4)

# ==========================================
# BUCLE PRINCIPAL
# ==========================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Món Obert - Port i Illes Realistes")
    clock = pygame.time.Clock()

    boat = Boat(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
    
    # Posem el port just al costat d'on comença el vaixell
    port = Port(WORLD_WIDTH / 2 - 250, WORLD_HEIGHT / 2 - 100)
    
    islands = [
        Island(500, 600, 120),
        Island(2200, 400, 150),
        Island(1500, 1400, 200),
        Island(800, 1700, 90)
    ]

    deep_currents = []
    for _ in range(60):
        deep_currents.append({
            'x': random.randint(0, WORLD_WIDTH),
            'y': random.randint(0, WORLD_HEIGHT),
            'radius': random.randint(100, 300),
            'speed': random.uniform(5, 15),
            'color': (random.randint(15, 25), random.randint(45, 55), random.randint(85, 95))
        })
    ocean_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        
        boat.handle_input(keys, dt, port)
        boat.update(dt, islands, port)

        cam_x = max(0, min(boat.x - WIDTH / 2, WORLD_WIDTH - WIDTH))
        cam_y = max(0, min(boat.y - HEIGHT / 2, WORLD_HEIGHT - HEIGHT))

        screen.fill(OCEAN_COLOR)
        ocean_surface.fill((0, 0, 0, 0))
        
        for current in deep_currents:
            current['x'] -= current['speed'] * dt
            if current['x'] < -current['radius']:
                current['x'] = WORLD_WIDTH + current['radius']
            
            draw_x = current['x'] - cam_x
            draw_y = current['y'] - cam_y
            if -current['radius'] < draw_x < WIDTH + current['radius'] and -current['radius'] < draw_y < HEIGHT + current['radius']:
                pygame.draw.circle(ocean_surface, current['color'], (int(draw_x), int(draw_y)), current['radius'])
            
        screen.blit(ocean_surface, (0, 0))

        port.draw(screen, cam_x, cam_y)
        for island in islands:
            island.draw(screen, cam_x, cam_y)
            
        boat.draw(screen, cam_x, cam_y, port)
        draw_minimap(screen, boat, islands, port)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()