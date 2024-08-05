import pygame
import random
import math
import time

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Metro")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
COLORS = [RED, GREEN, BLUE]

# Button dimensions and positions
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
BUTTON_SPACING = 20
BUTTON_Y = 10
BUTTONS = {
    RED: pygame.Rect(10, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
    GREEN: pygame.Rect(120, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
    BLUE: pygame.Rect(230, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
}

# Game variables
STATION_RADIUS = 15
PASSENGER_RADIUS = 5
TRAIN_RADIUS = 10
MAX_PASSENGERS = 6
TRAIN_SPEED = 2
MAX_CONNECTIONS = 15

# Debounce time for clicks (in seconds)
DEBOUNCE_TIME = 0.2

class Station:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.passengers = []
        self.connections = {}  # {direction: line}
        self.label = None
        self.font = pygame.font.Font(None, 24)

    def draw(self):
        if self.shape == "circle":
            pygame.draw.circle(screen, BLACK, (self.x, self.y), STATION_RADIUS, 2)
        elif self.shape == "square":
            pygame.draw.rect(screen, BLACK, (self.x - STATION_RADIUS, self.y - STATION_RADIUS, 
                                             STATION_RADIUS * 2, STATION_RADIUS * 2), 2)
        elif self.shape == "triangle":
            points = [
                (self.x, self.y - STATION_RADIUS),
                (self.x - STATION_RADIUS, self.y + STATION_RADIUS),
                (self.x + STATION_RADIUS, self.y + STATION_RADIUS)
            ]
            pygame.draw.polygon(screen, BLACK, points, 2)

        for i, passenger in enumerate(self.passengers):
            self.draw_passenger(self.x + 20 + i * 10, self.y, passenger)

        if self.label:
            label_text = self.font.render(self.label, True, BLACK)
            screen.blit(label_text, (self.x - 20, self.y - 40))

    def draw_passenger(self, x, y, shape):
        if shape == "circle":
            pygame.draw.circle(screen, BLACK, (x, y), PASSENGER_RADIUS)
        elif shape == "square":
            pygame.draw.rect(screen, BLACK, (x - PASSENGER_RADIUS, y - PASSENGER_RADIUS, 
                                             PASSENGER_RADIUS * 2, PASSENGER_RADIUS * 2))
        elif shape == "triangle":
            points = [
                (x, y - PASSENGER_RADIUS),
                (x - PASSENGER_RADIUS, y + PASSENGER_RADIUS),
                (x + PASSENGER_RADIUS, y + PASSENGER_RADIUS)
            ]
            pygame.draw.polygon(screen, BLACK, points)

    def set_label(self, label):
        self.label = label

    def clear_label(self):
        self.label = None

class Train:
    def __init__(self, color):
        self.color = color
        self.stations = []
        self.station_index = 0
        self.progress = 0
        self.passengers = []
        self.x = 0
        self.y = 0
        self.target_station_index = 1

    def update_route(self, stations):
        self.stations = stations
        if self.stations:
            self.x, self.y = self.stations[0].x, self.stations[0].y
            self.station_index = 0
            self.target_station_index = 1

    def move(self):
        if len(self.stations) < 2:
            return 0

        current_station = self.stations[self.station_index]
        target_station = self.stations[self.target_station_index]

        dx = target_station.x - current_station.x
        dy = target_station.y - current_station.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return 0

        self.progress += TRAIN_SPEED / distance
        if self.progress >= 1:
            self.station_index = self.target_station_index
            self.progress = 0
            delivered = self.load_unload()

            self.target_station_index = (self.station_index + 1) % len(self.stations)

            return delivered

        self.x = current_station.x + dx * self.progress
        self.y = current_station.y + dy * self.progress
        return 0

    def load_unload(self):
        station = self.stations[self.station_index]
        delivered = sum(1 for p in self.passengers if p == station.shape)
        self.passengers = [p for p in self.passengers if p != station.shape]
        
        while len(self.passengers) < MAX_PASSENGERS and station.passengers:
            self.passengers.append(station.passengers.pop(0))

        return delivered

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), TRAIN_RADIUS)
        for i, passenger in enumerate(self.passengers):
            self.draw_passenger(int(self.x) + 15 + i * 8, int(self.y) - 15, passenger)

    def draw_passenger(self, x, y, shape):
        if shape == "circle":
            pygame.draw.circle(screen, BLACK, (x, y), PASSENGER_RADIUS - 2)
        elif shape == "square":
            pygame.draw.rect(screen, BLACK, (x - PASSENGER_RADIUS + 2, y - PASSENGER_RADIUS + 2, 
                                             (PASSENGER_RADIUS - 2) * 2, (PASSENGER_RADIUS - 2) * 2))
        elif shape == "triangle":
            points = [
                (x, y - PASSENGER_RADIUS + 2),
                (x - PASSENGER_RADIUS + 2, y + PASSENGER_RADIUS - 2),
                (x + PASSENGER_RADIUS - 2, y + PASSENGER_RADIUS - 2)
            ]
            pygame.draw.polygon(screen, BLACK, points)

class Line:
    def __init__(self, color, train):
        self.stations = []
        self.color = color
        self.train = train

    def add_station(self, station):
        if station not in self.stations:
            self.stations.append(station)
            self.train.update_route(self.stations)

    def remove_station(self, station):
        if station in self.stations:
            self.stations.remove(station)
            self.train.update_route(self.stations)

    def draw(self):
        if len(self.stations) > 1:
            points = [(station.x, station.y) for station in self.stations]
            pygame.draw.lines(screen, self.color, False, points, 4)
        self.train.draw()

class Game:
    def __init__(self):
        self.stations = []
        self.lines = []
        self.available_connections = MAX_CONNECTIONS
        self.score = 0
        self.font = pygame.font.Font(None, 36)
        self.last_click_time = 0
        self.current_line = None
        self.last_station = None
        self.selected_color = RED  # Default selected color

        # To keep track of trains for each color
        self.trains = {
            RED: Train(RED),
            GREEN: Train(GREEN),
            BLUE: Train(BLUE)
        }

    def generate_station(self):
        shapes = ["circle", "square", "triangle"]
        x = random.randint(50, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        shape = random.choice(shapes)
        new_station = Station(x, y, shape)
        self.stations.append(new_station)

    def generate_passenger(self):
        for station in self.stations:
            if len(station.passengers) < MAX_PASSENGERS and random.random() < 0.02:
                shapes = ["circle", "square", "triangle"]
                shapes.remove(station.shape)
                station.passengers.append(random.choice(shapes))

    def draw_buttons(self):
        for color, rect in BUTTONS.items():
            pygame.draw.rect(screen, color, rect)
            if color == self.selected_color:
                pygame.draw.rect(screen, BLACK, rect, 2)

    def draw(self):
        screen.fill(WHITE)
        for line in self.lines:
            line.draw()
        for station in self.stations:
            station.draw()

        self.draw_buttons()

        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 70))

        lines_text = self.font.render(f"Available Connections: {self.available_connections}", True, BLACK)
        screen.blit(lines_text, (10, 110))

    def run(self):
        clock = pygame.time.Clock()
        running = True

        for _ in range(25):  # Generate 25 stations initially
            self.generate_station()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    current_time = time.time()
                    if current_time - self.last_click_time < DEBOUNCE_TIME:
                        continue  # Skip this event to debounce clicks
                    self.last_click_time = current_time

                    x, y = event.pos

                    # Check if a color button was clicked
                    for color, rect in BUTTONS.items():
                        if rect.collidepoint(x, y):
                            self.selected_color = color
                            break
                    else:  # If no button was clicked, proceed with station logic
                        clicked_station = None
                        for station in self.stations:
                            if math.hypot(station.x - x, station.y - y) < STATION_RADIUS:
                                clicked_station = station
                                break
                        if clicked_station:
                            if event.button == 1:  # Left click
                                if not self.current_line:
                                    self.current_line = Line(self.selected_color, self.trains[self.selected_color])
                                    self.lines.append(self.current_line)
                                    clicked_station.set_label("S")  # 시작 라벨 설정
                                    self.last_station = clicked_station
                                    self.current_line.add_station(clicked_station)
                                else:
                                    clicked_station.set_label("E")  # 끝 라벨 설정
                                    self.current_line.add_station(clicked_station)
                                    self.last_station.clear_label()  # 이전 시작 라벨 제거
                                    self.current_line = None
                                    self.last_station = None
                                    self.available_connections -= 1
                            elif event.button == 3:  # Right click
                                for line in self.lines:
                                    if clicked_station in line.stations:
                                        line.remove_station(clicked_station)
                                clicked_station.clear_label()  # 라벨 제거
                                self.current_line = None
                                self.last_station = None

            self.generate_passenger()

            for line in self.lines:
                self.score += line.train.move()

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
