import pygame
import random
import os

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 1.0  # More realistic gravity
JUMP_STRENGTH = -20  # Stronger jump for gaps
SPEED = 7  # Faster movement
PLAYER_RUN_TILT = 5  # Forward lean while running

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Setup Display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bridge Runner")
clock = pygame.time.Clock()

# Load Assets
def load_assets():
    assets = {}
    try:
        # Load and verify images exist
        if os.path.exists("player.png"):
            assets['player'] = pygame.image.load('player.png').convert_alpha()
            assets['player'] = pygame.transform.scale(assets['player'], (80, 80))  # Larger, more visible player
        
        if os.path.exists("bridge.png"):
            assets['bridge'] = pygame.image.load('bridge.png').convert_alpha()
            assets['bridge'] = pygame.transform.scale(assets['bridge'], (120, 40))  # Wider planks, realistic proportions
            
        if os.path.exists("fire.png"):
            assets['fire'] = pygame.image.load('fire.png').convert_alpha()
            assets['fire'] = pygame.transform.scale(assets['fire'], (SCREEN_WIDTH, 150))
            
        if os.path.exists("background.png"):
            assets['background'] = pygame.image.load('background.png').convert()
            assets['background'] = pygame.transform.scale(assets['background'], (SCREEN_WIDTH, SCREEN_HEIGHT))
            
        # Load Game Over popup image
        if os.path.exists("amit.jpg"):
            assets['gameover_popup'] = pygame.image.load('amit.jpg').convert_alpha()
            # Scale to a nice popup size (400x400 or maintain aspect ratio)
            popup_width = 400
            popup_height = 400
            assets['gameover_popup'] = pygame.transform.scale(assets['gameover_popup'], (popup_width, popup_height))
            print("Game over popup image loaded!")
            
    except Exception as e:
        print(f"Error loading assets: {e}")
    return assets

assets = load_assets()

# Initialize audio mixer with better settings
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Audio - Background Music
background_music_loaded = False
if os.path.exists("background_music.mp3"):
    try:
        pygame.mixer.music.load("background_music.mp3")
        pygame.mixer.music.set_volume(0.3)  # Lower volume for background
        pygame.mixer.music.play(-1)  # Loop indefinitely
        background_music_loaded = True
        print("Background music loaded and playing!")
    except Exception as e:
        print(f"Could not load background music: {e}")

# Audio - Sound Effects
scream_sound = None
if os.path.exists("Game over sound.mp3"):
    try:
        scream_sound = pygame.mixer.Sound("Game over sound.mp3")
        scream_sound.set_volume(0.7)  # Good volume for sound effect
        print("Scream sound loaded successfully!")
    except Exception as e:
        print(f"Could not load Game over sound.mp3: {e}")

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        if 'player' in assets:
            self.original_image = assets['player']
            self.image = self.original_image.copy()
        else:
            self.original_image = pygame.Surface((60, 60))
            self.original_image.fill(WHITE)
            self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = 150
        self.rect.y = 300
        self.velocity_y = 0
        self.jumping = False
        self.on_ground = False
        self.animation_timer = 0
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, bridges):
        # Apply gravity with more realistic physics
        self.velocity_y += GRAVITY
        
        # Terminal velocity (realistic limit)
        if self.velocity_y > 25:
            self.velocity_y = 25
            
        self.rect.y += self.velocity_y

        # Animation: slight tilt when running
        self.animation_timer += 1
        if self.on_ground and not self.jumping:
            # Forward lean while running
            tilt_angle = PLAYER_RUN_TILT + 2 * (self.animation_timer % 10) / 10
            self.image = pygame.transform.rotate(self.original_image, -tilt_angle)
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
        elif self.jumping and self.velocity_y < 0:
            # Lean back during jump ascent
            self.image = pygame.transform.rotate(self.original_image, 10)
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
        else:
            # Forward tilt during fall
            tilt = min(15, abs(self.velocity_y) * 0.8)
            self.image = pygame.transform.rotate(self.original_image, -tilt)
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center

        # Check collision with bridges - improved collision detection
        self.on_ground = False
        hits = pygame.sprite.spritecollide(self, bridges, False)
        for bridge in hits:
            # More realistic platform collision
            if self.velocity_y > 0:  # Falling down
                # Check if player's feet are above or at the bridge top
                if self.rect.bottom >= bridge.rect.top and self.rect.top < bridge.rect.top:
                    self.rect.bottom = bridge.rect.top
                    self.velocity_y = 0
                    self.jumping = False
                    self.on_ground = True
                    break
    
    def jump(self):
        if self.on_ground:
            self.velocity_y = JUMP_STRENGTH
            self.jumping = True
            self.on_ground = False

class Bridge(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        if 'bridge' in assets:
            self.image = assets['bridge']
        else:
            # Fallback with realistic wooden color
            self.image = pygame.Surface((120, 40))
            self.image.fill((139, 90, 43))  # Brown wood color
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= SPEED
        if self.rect.right < 0:
            self.kill()

class Fire(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        if 'fire' in assets:
            self.image = assets['fire']
        else:
            self.image = pygame.Surface((SCREEN_WIDTH, 100))
            self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

def main():
    running = True
    game_over = False
    scream_played = False  # Track if scream has been played
    
    player = Player()
    
    bridges = pygame.sprite.Group()
    
    # Initialize platform with realistic spacing
    bridge_width = 120  # Match new bridge width
    bridge_y = 460  # Lower position for better view
    for i in range(10): # Initial platform
        bridge = Bridge(i * bridge_width, bridge_y)
        bridges.add(bridge)
    
    last_bridge_x = 9 * bridge_width

    # Font
    font_name = pygame.font.match_font('arial')
    font = pygame.font.Font(font_name, 74)
    score_font = pygame.font.Font(font_name, 30)

    score = 0
    bg_x = 0

    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not game_over:
                        player.jump()
                    else:
                        # Reset game
                        game_over = False
                        scream_played = False  # Reset scream flag for new game
                        player = Player()
                        bridges.empty()
                        for i in range(10):
                            bridge = Bridge(i * bridge_width, bridge_y)
                            bridges.add(bridge)
                        last_bridge_x = 9 * bridge_width
                        score = 0
                        # Try to reload sound if it was missing before (optional)
        
        if not game_over:
            # Update Logic
            score += 1
            
            # Spawn bridges
            # We want to maintain a stream of bridges coming from the right
            # The rightmost bridge is at last_bridge_x
            # We need to spawn new ones as the old ones move left
            # Actually last_bridge_x is fixed in world space? No, everything moves left.
            # So last_bridge_x should act as a virtual cursor?
            # Easier: Find the rightmost bridge sprite
            if bridges:
                rightmost = max(bridges, key=lambda b: b.rect.right)
                if rightmost.rect.right < SCREEN_WIDTH + 200:
                    # Spawn next segment
                    # Chance for gap - more realistic difficulty curve
                    if random.random() < 0.25 and score > 150: # 25% gap chance after warm-up
                         gap_size = random.randint(130, 220) # Challenging but jumpable gaps
                         new_x = rightmost.rect.right + gap_size
                         bridge = Bridge(new_x, bridge_y)
                         bridges.add(bridge)
                    else:
                         # Sometimes add small gaps even in continuous sections
                         small_gap = random.randint(0, 15) if score > 100 else 0
                         bridge = Bridge(rightmost.rect.right + small_gap, bridge_y)
                         bridges.add(bridge)
            else:
                 # Fallback if empty (shouldn't happen on reset)
                 bridge = Bridge(SCREEN_WIDTH, bridge_y)
                 bridges.add(bridge)

            player.update(bridges)
            bridges.update()

            # Check Game Over
            if player.rect.y > SCREEN_HEIGHT:
                game_over = True
                if scream_sound and not scream_played:
                    scream_sound.play()
                    scream_played = True  # Only play once per game over
                print("Game Over!")

        # Drawing
        if 'background' in assets:
            # Scrolling background logic could go here
            screen.blit(assets['background'], (0, 0))
        else:
            screen.fill((20, 20, 40))

        bridges.draw(screen)
        screen.blit(player.image, player.rect)
        
        # Draw Fire
        if 'fire' in assets:
            screen.blit(assets['fire'], (0, SCREEN_HEIGHT - 100))
        else:
            pygame.draw.rect(screen, RED, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
            
        # Draw Score
        score_text = score_font.render(f"Distance: {score // 10}m", True, WHITE)
        screen.blit(score_text, (10, 10))

        if game_over:
            # Create semi-transparent overlay for popup effect
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)  # Semi-transparent
            overlay.fill((0, 0, 0))  # Black overlay
            screen.blit(overlay, (0, 0))
            
            # Display amit.jpg popup image if loaded
            if 'gameover_popup' in assets:
                popup_rect = assets['gameover_popup'].get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
                
                # Optional: Add white border/shadow for popup effect
                border_rect = pygame.Rect(popup_rect.x - 5, popup_rect.y - 5, popup_rect.width + 10, popup_rect.height + 10)
                pygame.draw.rect(screen, WHITE, border_rect, 5, border_radius=10)
                
                # Draw the popup image
                screen.blit(assets['gameover_popup'], popup_rect)
            
            # Game over text below the image
            text = font.render("GAME OVER", True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 100))
            screen.blit(text, text_rect)
            
            subtext = score_font.render("Press SPACE to Restart", True, WHITE)
            subtext_rect = subtext.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT - 50))
            screen.blit(subtext, subtext_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
