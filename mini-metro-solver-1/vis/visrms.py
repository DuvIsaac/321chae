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

TRAIN_WIDTH = 30
TRAIN_HEIGHT = 15

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
COLORS = [RED, GREEN, BLUE, YELLOW]

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
        self.connections = {}  # {line: direction}
        self.loop = None  # Reference to the loop this station is part of, if any

    def draw(self):
        color = BLACK if not self.loop else self.loop.color
        if self.shape == "circle":
            pygame.draw.circle(screen, color, (self.x, self.y), STATION_RADIUS, 2)
        elif self.shape == "square":
            pygame.draw.rect(screen, color, (self.x - STATION_RADIUS, self.y - STATION_RADIUS, 
                                             STATION_RADIUS * 2, STATION_RADIUS * 2), 2)
        elif self.shape == "triangle":
            points = [
                (self.x, self.y - STATION_RADIUS),
                (self.x - STATION_RADIUS, self.y + STATION_RADIUS),
                (self.x + STATION_RADIUS, self.y + STATION_RADIUS)
            ]
            pygame.draw.polygon(screen, color, points, 2)

        for i, passenger in enumerate(self.passengers):
            self.draw_passenger(self.x + 20 + i * 10, self.y, passenger)

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

class Train:
    def __init__(self, line):
        self.line = line
        self.station_index = 0
        self.progress = 0
        self.passengers = []
        self.x, self.y = self.line.stations[0].x, self.line.stations[0].y
        self.target_station_index = 1
        self.direction = 1  # 1 for forward, -1 for backward

    def move(self):
        if len(self.line.stations) < 2:
            return 0

        current_station = self.line.stations[self.station_index]
        target_station = self.line.stations[self.target_station_index]

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

            # Update target station index
            if self.line.loop:
                self.target_station_index = (self.station_index + self.direction) % len(self.line.stations)
            else:
                if self.station_index == len(self.line.stations) - 1:
                    self.direction = -1
                elif self.station_index == 0:
                    self.direction = 1
                self.target_station_index = self.station_index + self.direction

            return delivered

        self.x = current_station.x + dx * self.progress
        self.y = current_station.y + dy * self.progress
        return 0

    def load_unload(self):
        station = self.line.stations[self.station_index]
        # Unload all passengers who reached their destination
        delivered = sum(1 for p in self.passengers if p == station.shape)
        self.passengers = [p for p in self.passengers if p != station.shape]
        
        # Load new passengers if there's a corresponding station for them
        while len(self.passengers) < MAX_PASSENGERS and station.passengers:
            next_passenger = station.passengers[0]
            if self.line.has_station_with_shape(next_passenger):
                self.passengers.append(station.passengers.pop(0))
            else:
                station.passengers.pop(0)  # Remove the passenger from the station if no corresponding station exists

        return delivered

    def draw(self):
        train_width = TRAIN_WIDTH
        train_height = TRAIN_HEIGHT
        pygame.draw.rect(screen, self.line.color, (int(self.x) - train_width // 2, int(self.y) - train_height // 2, train_width, train_height))
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
    def __init__(self, color):
        self.stations = []
        self.color = color
        self.train = None
        self.loop = False

    def add_station(self, station, direction):
        if direction == "incoming":
            self.stations.insert(0, station)
            if self.train:
                self.train.station_index += 1
                self.train.target_station_index += 1
                if self.train.target_station_index >= len(self.stations):
                    self.train.target_station_index = 0
        else:  # "outgoing"
            self.stations.append(station)
        
        if len(self.stations) == 2 and not self.train:
            self.train = Train(self)

        # Check for loops
        if len(self.stations) > 2 and self.stations[0] == self.stations[-1]:
            self.loop = True
            loop_obj = Loop(self.stations)
            for station in self.stations:
                station.loop = loop_obj

        # Set train direction to always move forward in loops
        if len(self.stations) > 2:
            if self.train:
                self.train.direction = 1

    def remove_station(self, station):
        if station in self.stations:
            index = self.stations.index(station)
            self.stations.remove(station)
            if self.train:
                if index <= self.train.station_index:
                    self.train.station_index = max(0, self.train.station_index - 1)
                if index <= self.train.target_station_index:
                    self.train.target_station_index = max(0, self.train.target_station_index - 1)
                
                if self.train.station_index == self.train.target_station_index:
                    self.train.target_station_index = (self.train.station_index + 1) % len(self.stations)

            if len(self.stations) < 2:
                self.train = None
            else:
                # Ensure the train moves in a loop if there are more than 2 stations
                self.train.direction = 1

    def has_station_with_shape(self, shape):
        return any(station.shape == shape for station in self.stations)

    def draw(self):
        if len(self.stations) > 1:
            points = [(station.x, station.y) for station in self.stations]
            pygame.draw.lines(screen, self.color, False, points, 4)
        if self.train:
            self.train.draw()

class Loop:
    def __init__(self, stations):
        self.stations = stations
        self.color = random.choice(COLORS)
        self.assign_color_to_stations()

    def assign_color_to_stations(self):
        for station in self.stations:
            station.loop = self

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

    def draw(self):
        screen.fill(WHITE)
        for line in self.lines:
            line.draw()
        for station in self.stations:
            station.draw()

        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        lines_text = self.font.render(f"Available Connections: {self.available_connections}", True, BLACK)
        screen.blit(lines_text, (10, 50))

    def get_available_colors(self, station):
        used_colors = {line.color for line in station.connections.keys()}
        available_colors = [color for color in COLORS if color not in used_colors]

        # Check if there are any available colors that are different from existing lines
        if self.current_line is not None:
            different_colors = [color for color in available_colors if color != self.current_line.color]
            if different_colors:
                return different_colors
        
        # If no different colors are found, return all available colors
        return available_colors

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
                    clicked_station = None
                    for station in self.stations:
                        if math.hypot(station.x - x, station.y - y) < STATION_RADIUS:
                            clicked_station = station
                            break
                    if clicked_station:
                        if event.button == 1:  # Left click
                            if not self.current_line:
                                # Attempt to continue from an existing line
                                for line in self.lines:
                                    if clicked_station in line.stations:
                                        self.current_line = line
                                        break
                                if not self.current_line:
                                    # Get available colors for the clicked station
                                    available_colors = self.get_available_colors(clicked_station)
                                    if available_colors:
                                        # Create a new line if there is no existing line and available colors exist
                                        self.current_line = Line(random.choice(available_colors))
                                        self.lines.append(self.current_line)
                            # Add station to the current line if it's not the same as the last station
                            if clicked_station != self.last_station and self.current_line:
                                direction = 'outgoing' if self.last_station else 'incoming'
                                self.current_line.add_station(clicked_station, direction)
                                clicked_station.connections[self.current_line] = direction
                                if self.last_station:
                                    self.current_line = None
                                    self.last_station = None
                                    self.available_connections -= 1
                                else:
                                    self.last_station = clicked_station

            self.generate_passenger()

            for line in self.lines:
                if line.train:
                    self.score += line.train.move()

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
