import pygame
import random
import os
import time
import json
import sys

# Mobile ad integration placeholder
# In a real mobile app, you would use platform-specific ad libraries
class MobileAds:
    def __init__(self):
        self.app_id = "ca-app-pub-1459864659494913~1732025620"
        self.interstitial_id = "ca-app-pub-1459864659494913/9282093029"
        self.ad_loaded = False
        self.ad_shown = False
    
    def load_interstitial(self):
        """Load interstitial ad - placeholder for actual implementation"""
        print(f"Loading interstitial ad: {self.interstitial_id}")
        # In real implementation, this would load the ad
        self.ad_loaded = True
        return True
    
    def show_interstitial(self):
        """Show interstitial ad - placeholder for actual implementation"""
        if self.ad_loaded:
            print("Showing interstitial ad...")
            # In real implementation, this would show the ad
            self.ad_shown = True
            self.ad_loaded = False
            return True
        return False
    
    def is_ad_ready(self):
        return self.ad_loaded

pygame.init()

# Mobile-friendly screen dimensions
WIDTH, HEIGHT = 400, 700  # Taller for mobile
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Dodge Mobile")

# Initialize mobile ads
mobile_ads = MobileAds()

# Assets folder
ASSETS = "assets"

# Load images with error handling
def load_image(path, size):
    try:
        img = pygame.image.load(path)
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size)
        surf.fill((255, 255, 255))
        return surf

def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except:
        return None

# Load game assets
player_img = load_image(os.path.join(ASSETS, "player.png"), (60, 100))
road_img = load_image(os.path.join(ASSETS, "road.png"), (WIDTH, HEIGHT + 20))
enemy_imgs = [load_image(os.path.join(ASSETS, f"enimy{i}.png"), (60, 150)) for i in [1, 2, 3, 4, 5, 7, 8, 9]]

# Load control button images
button_size = (80, 80)

btn_up = load_image(os.path.join(ASSETS, "up.png"), button_size)
btn_down = load_image(os.path.join(ASSETS, "down.png"), button_size)
btn_left = load_image(os.path.join(ASSETS, "left.png"), button_size)
btn_right = load_image(os.path.join(ASSETS, "right.png"), button_size)



# Load sounds
crash_sound = load_sound(os.path.join(ASSETS, "crash.mp3"))
try:
    pygame.mixer.music.load(os.path.join(ASSETS, "background.mp3"))
    music_loaded = True
except:
    music_loaded = False

# Game states
MENU, PLAYING, GAME_OVER, PAUSED, SHOW_AD = 0, 1, 2, 3, 4
game_state = MENU

# Fonts - adjusted for mobile
font_large = pygame.font.SysFont("Arial", 36, bold=True)
font_medium = pygame.font.SysFont("Arial", 24)
font_small = pygame.font.SysFont("Arial", 18)
font_tiny = pygame.font.SysFont("Arial", 14)

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BLUE = (0, 0, 255)

# Mobile control buttons setup
button_margin = 20
button_bottom_margin = 30

# Position buttons for mobile interface
left_btn_rect = pygame.Rect(button_margin, HEIGHT - button_size[1] - button_bottom_margin, button_size[0], button_size[1])
right_btn_rect = pygame.Rect(button_margin + button_size[0] + 10, HEIGHT - button_size[1] - button_bottom_margin, button_size[0], button_size[1])
up_btn_rect = pygame.Rect(WIDTH - button_size[0] - button_margin, HEIGHT - button_size[1] * 2 - button_bottom_margin - 10, button_size[0], button_size[1])
down_btn_rect = pygame.Rect(WIDTH - button_size[0] - button_margin, HEIGHT - button_size[1] - button_bottom_margin, button_size[0], button_size[1])

# Touch input tracking
touch_states = {
    'left': False,
    'right': False,
    'up': False,
    'down': False
}

# Lane setup
lane_centers = [80, 160, 240, 320]
min_x = 40
max_x = 300
min_y = 50
max_y = HEIGHT - 200  # Adjusted for mobile controls

# High score
high_score = 0
games_played = 0  # Track games for ad frequency

def load_high_score():
    global high_score
    try:
        with open("highscore.json", "r") as f:
            data = json.load(f)
            high_score = data.get("score", 0)
    except:
        high_score = 0

def save_high_score(score):
    global high_score
    try:
        with open("highscore.json", "w") as f:
            json.dump({"score": score}, f)
        high_score = score
    except:
        pass

def reset_game():
    global player_rect, enemies, score, lives, road_y1, road_y2, scroll_speed, enemy_speed
    global last_spawn_time, spawn_delay, fade_timer, fade_phase, fade_alpha, menu_fade_alpha, menu_fade_direction
    
    # Player
    player_rect = pygame.Rect(WIDTH // 2 - 30, HEIGHT - 210, 60, 100)
    
    # Road
    road_y1, road_y2 = 0, -HEIGHT
    scroll_speed = 3
    
    # Enemies
    enemy_speed = 10
    spawn_delay = 1.5
    enemies = []
    last_spawn_time = time.time()
    
    # Game vars
    score, lives = 0, 3
    fade_timer = fade_phase = fade_alpha = 0
    menu_fade_alpha = 100
    menu_fade_direction = 1

def get_difficulty():
    return 1 + (score // 10) * 0.15

def is_position_safe(new_rect, exclude_index=-1, safety_margin=60):
    """Check if a position is safe (no collision with other enemies or player)"""
    safe_rect = pygame.Rect(new_rect.x - 10, new_rect.y - safety_margin, 
                           new_rect.width + 20, new_rect.height + safety_margin * 2)
    
    if safe_rect.colliderect(player_rect):
        return False
    
    for i, enemy_data in enumerate(enemies):
        if i == exclude_index:
            continue
        rect = enemy_data[1]
        if safe_rect.colliderect(rect):
            return False
    return True

def get_current_lane_index(rect_x):
    """Get the current lane index based on car's x position"""
    car_center = rect_x + 30
    
    closest_lane = 0
    min_distance = abs(car_center - lane_centers[0])
    
    for i, lane_center in enumerate(lane_centers):
        distance = abs(car_center - lane_center)
        if distance < min_distance:
            min_distance = distance
            closest_lane = i
    
    return closest_lane

def get_safe_lane_change(enemy_index, current_lane_index):
    """Get a safe adjacent lane for enemy to change to"""
    if enemy_index >= len(enemies):
        return lane_centers[current_lane_index]
    
    current_enemy = enemies[enemy_index]
    adjacent_lanes = []
    
    if current_lane_index > 0:
        adjacent_lanes.append(current_lane_index - 1)
    
    if current_lane_index < len(lane_centers) - 1:
        adjacent_lanes.append(current_lane_index + 1)
    
    safe_lanes = []
    for lane_index in adjacent_lanes:
        lane_center = lane_centers[lane_index]
        test_rect = pygame.Rect(lane_center - 30, current_enemy[1].y, 60, 150)
        
        if is_position_safe(test_rect, enemy_index, safety_margin=80):
            safe_lanes.append(lane_center)
    
    if safe_lanes:
        return random.choice(safe_lanes)
    else:
        return lane_centers[current_lane_index]

def spawn_enemy():
    if time.time() - last_spawn_time >= max(0.8, spawn_delay / get_difficulty()):
        attempts = 0
        while attempts < 15:
            lane = random.choice(lane_centers)
            spawn_y = random.randint(-500, -200)
            test_rect = pygame.Rect(lane - 30, spawn_y, 60, 150)
            
            if is_position_safe(test_rect, safety_margin=120):
                img = random.choice(enemy_imgs)
                enemy_speed_var = enemy_speed + random.uniform(-1.5, 1.5)
                enemy_data = [img, test_rect, enemy_speed_var, 0, lane]
                enemies.append(enemy_data)
                return time.time()
            attempts += 1
        return last_spawn_time
    return last_spawn_time

def handle_touch_input(pos, pressed):
    """Handle touch input for mobile controls"""
    global touch_states
    
    if pressed:
        if left_btn_rect.collidepoint(pos):
            touch_states['left'] = True
        elif right_btn_rect.collidepoint(pos):
            touch_states['right'] = True
        elif up_btn_rect.collidepoint(pos):
            touch_states['up'] = True
        elif down_btn_rect.collidepoint(pos):
            touch_states['down'] = True
    else:
        # Reset all touch states when touch is released
        touch_states = {key: False for key in touch_states}

def draw_mobile_controls():
    """Draw mobile control buttons"""
    # Draw buttons with transparency for pressed state
    buttons = [
        (btn_left, left_btn_rect, touch_states['left']),
        (btn_right, right_btn_rect, touch_states['right']),
        (btn_up, up_btn_rect, touch_states['up']),
        (btn_down, down_btn_rect, touch_states['down'])
    ]
    
    for btn_img, btn_rect, is_pressed in buttons:
        # Create a copy of the button image
        button_surface = btn_img.copy()
        
        # Apply transparency if pressed
        if is_pressed:
            button_surface.set_alpha(150)
        else:
            button_surface.set_alpha(255)
        
        # Draw button
        win.blit(button_surface, btn_rect)
        

def draw_menu():
    global menu_fade_alpha, menu_fade_direction
    
    win.fill(BLACK)
    
    # Animated title
    menu_fade_alpha += menu_fade_direction * 3
    if menu_fade_alpha >= 255:
        menu_fade_alpha, menu_fade_direction = 255, -1
    elif menu_fade_alpha <= 100:
        menu_fade_alpha, menu_fade_direction = 100, 1
    
    title_color = (YELLOW[0], YELLOW[1], min(255, YELLOW[2] + menu_fade_alpha - 100))
    title = font_large.render("CAR DODGE", True, title_color)
    win.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//6))
    
    # High score
    high_text = font_medium.render(f"High Score: {high_score}", True, GREEN)
    win.blit(high_text, (WIDTH//2 - high_text.get_width()//2, HEIGHT//3))
    
    # Menu options - adjusted for mobile
    options = ["TAP TO START", "Swipe to move", "Avoid other cars!"]
    y = HEIGHT//2
    for i, option in enumerate(options):
        if i == 0:
            color = (255, 255, min(255, 255 - menu_fade_alpha + 100))
        else:
            color = GRAY
        text = font_small.render(option, True, color)
        win.blit(text, (WIDTH//2 - text.get_width()//2, y))
        y += 30

def draw_pause():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(128)
    overlay.fill(BLACK)
    win.blit(overlay, (0, 0))
    
    pause_text = font_large.render("PAUSED", True, YELLOW)
    win.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//3))
    
    options = ["TAP TO RESUME", "Hold to Restart"]
    y = HEIGHT//2
    for option in options:
        text = font_medium.render(option, True, WHITE)
        win.blit(text, (WIDTH//2 - text.get_width()//2, y))
        y += 40

def draw_game_over():
    win.fill(BLACK)
    
    # Game over text
    game_over_text = font_large.render("GAME OVER", True, RED)
    win.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//4))
    
    # Score
    score_text = font_medium.render(f"Score: {score}", True, WHITE)
    win.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 60))
    
    # High score check
    if score > high_score:
        new_high_text = font_medium.render("NEW HIGH SCORE!", True, GREEN)
        win.blit(new_high_text, (WIDTH//2 - new_high_text.get_width()//2, HEIGHT//2 - 30))
    
    # Options
    options = ["TAP TO PLAY AGAIN", "Hold to exit"]
    y = HEIGHT//2 + 20
    for option in options:
        text = font_small.render(option, True, WHITE)
        win.blit(text, (WIDTH//2 - text.get_width()//2, y))
        y += 30

def draw_ad_screen():
    """Draw ad loading/showing screen"""
    win.fill(BLACK)
    
    ad_text = font_large.render("LOADING AD...", True, WHITE)
    win.blit(ad_text, (WIDTH//2 - ad_text.get_width()//2, HEIGHT//2 - 50))
    
    # Simulate ad loading animation
    dots = "." * ((pygame.time.get_ticks() // 500) % 4)
    loading_text = font_medium.render(f"Please wait{dots}", True, GRAY)
    win.blit(loading_text, (WIDTH//2 - loading_text.get_width()//2, HEIGHT//2 + 20))

def check_distance_and_trigger_lane_change():
    """Check distances between cars and trigger lane changes when needed"""
    for i in range(len(enemies)):
        current_enemy = enemies[i]
        current_rect = current_enemy[1]
        current_lane = get_current_lane_index(current_rect.x)
        
        for j in range(len(enemies)):
            if i == j:
                continue
                
            other_enemy = enemies[j]
            other_rect = other_enemy[1]
            other_lane = get_current_lane_index(other_rect.x)
            
            if current_lane == other_lane:
                if (other_rect.y < current_rect.y and 
                    current_rect.y - other_rect.bottom < 100):
                    
                    if current_enemy[2] >= other_enemy[2]:
                        new_target = get_safe_lane_change(i, current_lane)
                        if new_target != lane_centers[current_lane]:
                            enemies[i][4] = new_target
                            enemies[i][3] = 0
                            break

def check_and_resolve_overlaps():
    """Check for overlapping enemies and resolve them"""
    for i in range(len(enemies)):
        if i >= len(enemies):
            break
            
        for j in range(i + 1, len(enemies)):
            if j >= len(enemies):
                break
                
            enemy1 = enemies[i]
            enemy2 = enemies[j]
            
            if enemy1[1].colliderect(enemy2[1]):
                if enemy1[1].y < enemy2[1].y:
                    front_enemy = enemy1
                    back_enemy = enemy2
                    front_index = i
                    back_index = j
                else:
                    front_enemy = enemy2
                    back_enemy = enemy1
                    front_index = j
                    back_index = i
                
                front_lane = get_current_lane_index(front_enemy[1].x)
                back_lane = get_current_lane_index(back_enemy[1].x)
                
                if abs(front_lane - back_lane) <= 1:
                    if back_index < len(enemies):
                        new_target = get_safe_lane_change(back_index, back_lane)
                        if new_target != lane_centers[back_lane]:
                            enemies[back_index][4] = new_target
                            enemies[back_index][3] = 0
                        else:
                            enemies[back_index][2] = max(1, enemies[back_index][2] - 1.5)
                            if front_index < len(enemies):
                                enemies[front_index][2] = min(8, enemies[front_index][2] + 0.5)

# Initialize
load_high_score()
reset_game()
mobile_ads.load_interstitial()  # Load ad at start
clock = pygame.time.Clock()
run = True
ad_timer = 0

while run:
    clock.tick(60)
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == PLAYING:
                handle_touch_input(event.pos, True)
            elif game_state == MENU:
                game_state = PLAYING
                if music_loaded:
                    pygame.mixer.music.play(-1)
            elif game_state == GAME_OVER:
                # Check if we should show ad before restarting
                games_played += 1
                if games_played % 3 == 0:  # Show ad every 3 games
                    game_state = SHOW_AD
                    ad_timer = 0
                    mobile_ads.show_interstitial()
                else:
                    reset_game()
                    game_state = PLAYING
                    if music_loaded:
                        pygame.mixer.music.play(-1)
            elif game_state == PAUSED:
                game_state = PLAYING
                if music_loaded:
                    pygame.mixer.music.unpause()
        elif event.type == pygame.MOUSEBUTTONUP:
            if game_state == PLAYING:
                handle_touch_input(event.pos, False)
        elif event.type == pygame.KEYDOWN:
            # Keep keyboard controls for desktop testing
            if event.key == pygame.K_SPACE:
                if game_state == MENU:
                    game_state = PLAYING
                    if music_loaded:
                        pygame.mixer.music.play(-1)
                elif game_state == GAME_OVER:
                    reset_game()
                    game_state = PLAYING
                    if music_loaded:
                        pygame.mixer.music.play(-1)
            elif event.key == pygame.K_ESCAPE:
                if game_state in [GAME_OVER, PAUSED, PLAYING]:
                    if music_loaded:
                        pygame.mixer.music.stop()
                    game_state = MENU
                elif game_state == MENU:
                    run = False
    
    # Game logic based on current state
    if game_state == MENU:
        draw_menu()
    elif game_state == SHOW_AD:
        draw_ad_screen()
        ad_timer += 1
        # Simulate ad display time (3 seconds)
        if ad_timer > 180:  # 3 seconds at 60 FPS
            reset_game()
            game_state = PLAYING
            if music_loaded:
                pygame.mixer.music.play(-1)
            mobile_ads.load_interstitial()  # Load next ad
    elif game_state == PLAYING:
        # Update speeds
        difficulty = get_difficulty()
        scroll_speed = min(12, 5 + (difficulty - 1) * 3)
        enemy_speed = min(10, 5 + (difficulty - 1) * 2)
        
        win.fill(BLACK)
        
        # Road scrolling
        road_y1 += scroll_speed
        road_y2 += scroll_speed
        if road_y1 >= HEIGHT:
            road_y1 = road_y2 - HEIGHT
        if road_y2 >= HEIGHT:
            road_y2 = road_y1 - HEIGHT
        
        win.blit(road_img, (0, road_y1))
        win.blit(road_img, (0, road_y2))
        
        # Player movement - Touch controls
        movement_speed = 6
        if touch_states['left']:
            player_rect.x = max(min_x, player_rect.x - movement_speed)
        if touch_states['right']:
            player_rect.x = min(max_x, player_rect.x + movement_speed)
        if touch_states['up']:
            player_rect.y = max(min_y, player_rect.y - movement_speed)
        if touch_states['down']:
            player_rect.y = min(max_y, player_rect.y + movement_speed)
        
        # Keyboard controls for desktop testing
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_rect.x = max(min_x, player_rect.x - movement_speed)
        if keys[pygame.K_RIGHT]:
            player_rect.x = min(max_x, player_rect.x + movement_speed)
        if keys[pygame.K_UP]:
            player_rect.y = max(min_y, player_rect.y - movement_speed)
        if keys[pygame.K_DOWN]:
            player_rect.y = min(max_y, player_rect.y + movement_speed)
        
        # Enemy spawning
        last_spawn_time = spawn_enemy()
        
        # Check distance-based lane changes
        check_distance_and_trigger_lane_change()
        
        # Check and resolve overlaps
        check_and_resolve_overlaps()
        
        # Enemy logic
        for i in range(len(enemies) - 1, -1, -1):
            if i >= len(enemies):
                continue
                
            img, rect, speed, lane_timer, target_lane = enemies[i]
            
            enemies[i][3] += 1
            
            # Natural lane changes
            if lane_timer > random.randint(180, 300):
                current_lane_index = get_current_lane_index(rect.x)
                
                if random.random() < 0.6:
                    new_target = get_safe_lane_change(i, current_lane_index)
                    if new_target != lane_centers[current_lane_index]:
                        enemies[i][4] = new_target
                enemies[i][3] = 0
            
            # Lane changing
            target_x = enemies[i][4] - 30
            if abs(rect.x - target_x) > 3:
                lane_change_speed = 2.5
                if rect.x < target_x:
                    rect.x += min(lane_change_speed, target_x - rect.x)
                else:
                    rect.x -= min(lane_change_speed, rect.x - target_x)
            else:
                rect.x = target_x
            
            # Move enemy down
            rect.y += speed
            
            # Remove if off screen
            if rect.top > HEIGHT:
                enemies.pop(i)
                score += 1
                continue
            
            # Collision with player
            if rect.colliderect(player_rect):
                if crash_sound:
                    crash_sound.play()
                fade_timer = 36
                fade_phase = 0
                fade_alpha = 255
                lives -= 1
                enemies.pop(i)
                
                if lives <= 0:
                    if music_loaded:
                        pygame.mixer.music.stop()
                    if score > high_score:
                        save_high_score(score)
                    game_state = GAME_OVER
                    continue
            
            win.blit(img, rect)
        
        # Draw player with fade effect
        if fade_timer > 0:
            if fade_phase % 2 == 0:
                fade_alpha -= 42
            else:
                fade_alpha += 42
            
            fade_alpha = max(0, min(255, fade_alpha))
            temp_img = player_img.copy()
            temp_img.set_alpha(fade_alpha)
            win.blit(temp_img, player_rect)
            
            if fade_alpha <= 0 or fade_alpha >= 255:
                fade_phase += 1
            fade_timer -= 1
        else:
            win.blit(player_img, player_rect)
        
        # Draw mobile controls
        draw_mobile_controls()
        
        # UI
        score_text = font_small.render(f"Score: {score}", True, WHITE)
        lives_text = font_small.render(f"Lives: {lives}", True, RED)
        win.blit(score_text, (10, 10))
        win.blit(lives_text, (10, 30))
        
        # Speed indicator
        speed_text = font_tiny.render(f"Speed: {difficulty:.1f}x", True, GRAY)
        win.blit(speed_text, (10, 50))
        
    elif game_state == PAUSED:
        draw_pause()
    elif game_state == GAME_OVER:
        draw_game_over()
    
    pygame.display.update()

pygame.quit()
sys.exit()