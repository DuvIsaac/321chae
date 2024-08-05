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
COLOR_BUTTONS = {
    RED: pygame.Rect(10, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
    GREEN: pygame.Rect(120, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
    BLUE: pygame.Rect(230, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT),
}
TRAIN_BUTTONS = {
    RED: pygame.Rect(10, BUTTON_Y + BUTTON_HEIGHT + 10, BUTTON_WIDTH, BUTTON_HEIGHT),
    GREEN: pygame.Rect(120, BUTTON_Y + BUTTON_HEIGHT + 10, BUTTON_WIDTH, BUTTON_HEIGHT),
    BLUE: pygame.Rect(230, BUTTON_Y + BUTTON_HEIGHT + 10, BUTTON_WIDTH, BUTTON_HEIGHT),
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
DOUBLE_CLICK_TIME = 0.5  # Time window to detect double-click

class Station:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.passengers = []
        self.connections = {}  # {color: [connected_stations]}
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
    def __init__(self, line, start_station):
        self.line = line
        self.current_station = start_station
        self.next_station = None
        self.progress = 0
        self.passengers = []
        self.x, self.y = self.current_station.x, self.current_station.y
        self.direction = 1  # 1 for forward, -1 for backward

    def move(self):
        if not self.next_station:
            self.choose_next_station()
            if not self.next_station:
                return 0

        dx = self.next_station.x - self.current_station.x
        dy = self.next_station.y - self.current_station.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance == 0:
            return 0

        self.progress += TRAIN_SPEED / distance
        if self.progress >= 1:
            self.current_station = self.next_station
            self.next_station = None
            self.progress = 0
            delivered = self.load_unload()
            self.x, self.y = self.current_station.x, self.current_station.y
            return delivered

        self.x = self.current_station.x + dx * self.progress
        self.y = self.current_station.y + dy * self.progress
        return 0

    def choose_next_station(self):
        if not self.line.stations:
            return

        current_index = self.line.stations.index(self.current_station)
        next_index = (current_index + self.direction) % len(self.line.stations)
        self.next_station = self.line.stations[next_index]

    def load_unload(self):
        delivered = sum(1 for p in self.passengers if p == self.current_station.shape)
        self.passengers = [p for p in self.passengers if p != self.current_station.shape]
        
        while len(self.passengers) < MAX_PASSENGERS and self.current_station.passengers:
            self.passengers.append(self.current_station.passengers.pop(0))

        return delivered

    def draw(self):
        pygame.draw.circle(screen, self.line.color, (int(self.x), int(self.y)), TRAIN_RADIUS)
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

    def add_station(self, station):
        if station not in self.stations:
            if self.stations:
                last_station = self.stations[-1]
                last_station.connections.setdefault(self.color, []).append(station)
                station.connections.setdefault(self.color, []).append(last_station)
            self.stations.append(station)
        elif station == self.stations[0] and len(self.stations) > 2:
            # If the added station is the start station, close the loop
            last_station = self.stations[-1]
            last_station.connections.setdefault(self.color, []).append(station)
            station.connections.setdefault(self.color, []).append(last_station)

    def remove_station(self, station):
        if station in self.stations:
            index = self.stations.index(station)
            self.stations.remove(station)
            if len(self.stations) > 1:
                prev_station = self.stations[index - 1] if index > 0 else self.stations[-1]
                next_station = self.stations[index] if index < len(self.stations) else self.stations[0]
                
                prev_station.connections[self.color].remove(station)
                next_station.connections[self.color].remove(station)
                station.connections[self.color].remove(prev_station)
                station.connections[self.color].remove(next_station)
                
                if index == 0 or index == len(self.stations):
                    # If removed station was at the start or end, connect the new endpoints
                    prev_station.connections[self.color].append(next_station)
                    next_station.connections[self.color].append(prev_station)
            
            if self.train and self.train.current_station == station:
                self.train.current_station = self.stations[0] if self.stations else None
                self.train.next_station = None

    def draw(self):
        if len(self.stations) > 1:
            points = [(station.x, station.y) for station in self.stations]
            if len(self.stations) > 2 and self.stations[0] == self.stations[-1]:
                pygame.draw.lines(screen, self.color, True, points, 4)
            else:
                pygame.draw.lines(screen, self.color, False, points, 4)
                pygame.draw.line(screen, self.color, points[-2], points[-1], 4)
        if self.train:
            self.train.draw()

    def add_train(self, start_station):
        if not self.train and start_station in self.stations:
            self.train = Train(self, start_station)
            # Connect the first and last station
            if len(self.stations) > 1:
                first_station = self.stations[0]
                last_station = self.stations[-1]
                first_station.connections.setdefault(self.color, []).append(last_station)
                last_station.connections.setdefault(self.color, []).append(first_station)

class Game:
    def __init__(self):
        self.stations = []
        self.lines = {RED: Line(RED), GREEN: Line(GREEN), BLUE: Line(BLUE)}
        self.available_connections = MAX_CONNECTIONS
        self.score = 0
        self.font = pygame.font.Font(None, 36)
        self.last_click_time = 0
        self.current_line = None
        self.start_station = None
        self.selected_color = RED  # Default selected color
        self.last_click_pos = None
        self.edge_click_time = 0

    def generate_station(self):
        shapes = ["circle", "square", "triangle"]
        x = random.randint(50, WIDTH - 50)
        y = random.randint(100, HEIGHT - 50)
        shape = random.choice(shapes)
        new_station = Station(x, y, shape)
        self.stations.append(new_station)

    def generate_passenger(self):
        for station in self.stations:
            if len(station.passengers) < MAX_PASSENGERS and random.random() < 0.001:
                shapes = ["circle", "square", "triangle"]
                shapes.remove(station.shape)
                station.passengers.append(random.choice(shapes))

    def draw_buttons(self):
        for color, rect in COLOR_BUTTONS.items():
            pygame.draw.rect(screen, color, rect)
            if color == self.selected_color:
                pygame.draw.rect(screen, BLACK, rect, 2)
    
        for color, rect in TRAIN_BUTTONS.items():
            center_x, center_y = rect.center
            pygame.draw.circle(screen, color, (center_x, center_y), 15)
            pygame.draw.rect(screen, color, (center_x - 12, center_y - 8, 24, 16))
            pygame.draw.circle(screen, BLACK, (center_x - 8, center_y + 8), 4)
            pygame.draw.circle(screen, BLACK, (center_x + 8, center_y + 8), 4)
            if not self.lines[color].train:
                pygame.draw.line(screen, WHITE, (center_x - 8, center_y - 2), (center_x + 8, center_y - 2), 2)

    def draw(self):
        screen.fill(WHITE)
        for line in self.lines.values():
            line.draw()
        for station in self.stations:
            station.draw()

        self.draw_buttons()

        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 120))

        lines_text = self.font.render(f"Available Connections: {self.available_connections}", True, BLACK)
        screen.blit(lines_text, (10, 160))

    def remove_edge(self, station1, station2, color):
        if color in station1.connections and station2 in station1.connections[color]:
            station1.connections[color].remove(station2)
            station2.connections[color].remove(station1)
            for line in self.lines.values():
                if line.color == color:
                    if station2 in line.stations:
                        index1 = line.stations.index(station1)
                        index2 = line.stations.index(station2)
                        if abs(index1 - index2) == 1 or (index1 == 0 and index2 == len(line.stations) - 1) or (index2 == 0 and index1 == len(line.stations) - 1):
                            if index1 < index2:
                                line.stations.remove(station2)
                            else:
                                line.stations.remove(station1)

    def run(self):
        clock = pygame.time.Clock()
        running = True

        for _ in range(25):  # Generate 15 stations initially
            self.generate_station()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    current_time = time.time()
                    x, y = event.pos

                    # Check if a color button was clicked
                    for color, rect in COLOR_BUTTONS.items():
                        if rect.collidepoint(x, y):
                            self.selected_color = color
                            break
                    else:
                        # Check if a train button was clicked
                        for color, rect in TRAIN_BUTTONS.items():
                            if rect.collidepoint(x, y):
                                if not self.lines[color].train and self.lines[color].stations:
                                    self.lines[color].add_train(self.lines[color].stations[0])
                                break
                        else:
                            # If no button was clicked, proceed with station logic
                            clicked_station = None
                            for station in self.stations:
                                if math.hypot(station.x - x, station.y - y) < STATION_RADIUS:
                                    clicked_station = station
                                    break
                            if clicked_station:
                                if event.button == 1:  # Left click
                                    if self.available_connections > 0:
                                        if not self.current_line:
                                            self.current_line = self.lines[self.selected_color]
                                            clicked_station.set_label("S")
                                            self.start_station = clicked_station
                                            self.current_line.add_station(clicked_station)
                                        elif clicked_station == self.start_station and len(self.current_line.stations) > 2:
                                            # Close the loop
                                            self.current_line.add_station(clicked_station)
                                            self.start_station.clear_label()
                                            self.current_line = None
                                            self.start_station = None
                                            self.available_connections -= 1
                                        elif clicked_station != self.start_station:
                                            self.current_line.add_station(clicked_station)
                                            clicked_station.set_label("E")
                                            self.start_station.clear_label()
                                            self.current_line = None
                                            self.start_station = None
                                            self.available_connections -= 1
                                elif event.button == 3:  # Right click
                                    for line in self.lines.values():
                                        if clicked_station in line.stations:
                                            line.remove_station(clicked_station)
                                            self.available_connections += 1
                                        clicked_station.clear_label()
                                    self.current_line = None
                                    self.start_station = None
                            else:
                                # Check for double-click on edge
                                if current_time - self.edge_click_time < DOUBLE_CLICK_TIME:
                                    for station in self.stations:
                                        for color, connected_stations in station.connections.items():
                                            for connected_station in connected_stations:
                                                if self.last_click_pos and self.last_click_pos != (station.x, station.y) and self.last_click_pos != (connected_station.x, connected_station.y):
                                                    if self.is_near_edge(x, y, station, connected_station):
                                                        self.remove_edge(station, connected_station, color)
                                                        self.edge_click_time = 0  # Reset edge click time
                                                        self.available_connections += 1
                                                        break
                                self.edge_click_time = current_time
                                self.last_click_pos = (x, y)

            self.generate_passenger()

            for line in self.lines.values():
                if line.train:
                    self.score += line.train.move()

            self.draw()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def is_near_edge(self, x, y, station1, station2):
        edge_center_x = (station1.x + station2.x) / 2
        edge_center_y = (station1.y + station2.y) / 2
        distance = math.hypot(edge_center_x - x, edge_center_y - y)
        return distance < 20  # Adjust this value as needed to detect clicks near the edge

if __name__ == "__main__":
    game = Game()
    game.run()
