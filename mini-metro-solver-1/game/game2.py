import pygame
import random
import math
import time
import numpy as np
from optimization import calculate_optimal_routes

# Initialize Pygame
pygame.init()

# Set up the displays
WIDTH, HEIGHT = 800, 600
game_screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Metro Game")

optimization_screen = pygame.Surface((WIDTH, HEIGHT))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
COLORS = [RED, GREEN, BLUE]

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
        self.connections = {}  # {color: [connected_stations]}
        self.label = None
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
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
            self.draw_passenger(screen, self.x + 20 + i * 10, self.y, passenger)

        if self.label:
            label_text = self.font.render(self.label, True, BLACK)
            screen.blit(label_text, (self.x - 20, self.y - 40))

    def draw_passenger(self, screen, x, y, shape):
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
        self.wait_time = 1  # 역에서 대기하는 시간 (초)
        self.wait_start = None  # 대기 시작 시간

    def move(self):
        if self.wait_start is not None:
            if time.time() - self.wait_start >= self.wait_time:
                self.wait_start = None
                self.choose_next_station()
            return 0

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
            self.wait_start = time.time()  # 대기 시작
            return delivered

        self.x = self.current_station.x + dx * self.progress
        self.y = self.current_station.y + dy * self.progress
        return 0

    def choose_next_station(self):
        if not self.line.stations:
            return

        current_index = self.line.stations.index(self.current_station)
        if self.direction == 1 and current_index == len(self.line.stations) - 1:
            self.direction = -1
        elif self.direction == -1 and current_index == 0:
            self.direction = 1

        self.next_station = self.line.stations[current_index + self.direction]

    def load_unload(self):
        delivered = sum(1 for p in self.passengers if p == self.current_station.shape)
        self.passengers = [p for p in self.passengers if p != self.current_station.shape]
        
        available_shapes = self.line.get_available_shapes()
        remaining_passengers = []
        for passenger in self.current_station.passengers:
            if len(self.passengers) < MAX_PASSENGERS and passenger in available_shapes:
                self.passengers.append(passenger)
            else:
                remaining_passengers.append(passenger)
        self.current_station.passengers = remaining_passengers

        return delivered

    def draw(self, screen):
        pygame.draw.circle(screen, self.line.color, (int(self.x), int(self.y)), TRAIN_RADIUS)
        for i, passenger in enumerate(self.passengers):
            self.draw_passenger(screen, int(self.x) + 15 + i * 8, int(self.y) - 15, passenger)

    def draw_passenger(self, screen, x, y, shape):
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

    def add_station(self, station, game):
        if station not in self.stations:
            if self.stations:
                last_station = self.stations[-1]
                if station not in last_station.connections.get(self.color, []):
                    last_station.connections.setdefault(self.color, []).append(station)
                    station.connections.setdefault(self.color, []).append(last_station)
                    game.available_connections -= 1
            self.stations.append(station)
            return True
        return False

    def remove_station(self, station):
        if station in self.stations:
            index = self.stations.index(station)
            self.stations.remove(station)
            if index > 0:
                prev_station = self.stations[index - 1]
                prev_station.connections[self.color].remove(station)
                station.connections[self.color].remove(prev_station)
            if index < len(self.stations):
                next_station = self.stations[index]
                next_station.connections[self.color].remove(station)
                station.connections[self.color].remove(next_station)
            if self.train and self.train.current_station == station:
                self.train.current_station = self.stations[0] if self.stations else None
                self.train.next_station = None

    def draw(self, screen):
        if len(self.stations) > 1:
            points = [(station.x, station.y) for station in self.stations]
            pygame.draw.lines(screen, self.color, False, points, 4)
        if self.train:
            self.train.draw(screen)

    def add_train(self, start_station):
        if not self.train and start_station in self.stations:
            self.train = Train(self, start_station)

    def get_available_shapes(self):
        return set(station.shape for station in self.stations)

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
        self.last_double_click_time = 0
        self.double_click_interval = 0.3  # 더블클릭 간격 (초)
        self.reset_button = pygame.Rect(340, 10, 100, 40)
        self.optimal_routes = None

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

    def draw_buttons(self, screen):
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

        pygame.draw.rect(screen, BLACK, self.reset_button)
        reset_text = self.font.render("Reset", True, WHITE)
        text_rect = reset_text.get_rect(center=self.reset_button.center)
        screen.blit(reset_text, text_rect)

    def draw_game(self, screen):
        screen.fill(WHITE)
        for line in self.lines.values():
            line.draw(screen)
        for station in self.stations:
            station.draw(screen)

        self.draw_buttons(screen)

        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 120))

        lines_text = self.font.render(f"Available Connections: {self.available_connections}", True, BLACK)
        screen.blit(lines_text, (10, 160))

    def draw_optimization(self, screen):
        screen.fill(WHITE)
        if self.optimal_routes:
            for i, route in enumerate(self.optimal_routes):
                color = COLORS[i % len(COLORS)]
                pygame.draw.lines(screen, color, False, route, 4)

        for station in self.stations:
            station.draw(screen)

        optimization_text = self.font.render("Optimized Routes", True, BLACK)
        screen.blit(optimization_text, (10, 10))

    def is_point_on_line(self, x, y, line):
        for i in range(len(line.stations) - 1):
            start = line.stations[i]
            end = line.stations[i + 1]
            
            line_length = math.hypot(end.x - start.x, end.y - start.y)
            
            d1 = math.hypot(x - start.x, y - start.y)
            d2 = math.hypot(x - end.x, y - end.y)
            
            buffer = 5
            
            if abs(d1 + d2 - line_length) <= buffer:
                return True, i
        return False, -1

    def remove_connection(self, line, index):
        if 0 <= index < len(line.stations) - 1:
            station1 = line.stations[index]
            station2 = line.stations[index + 1]
            
            station1.connections[line.color].remove(station2)
            station2.connections[line.color].remove(station1)
            
            line.stations.pop(index + 1)
            
            self.available_connections += 1

    def reset_lines(self):
        for line in self.lines.values():
            for station in line.stations:
                station.connections[line.color] = []
            line.stations = []
            if line.train:
                line.train = None
        self.available_connections = MAX_CONNECTIONS
        self.current_line = None
        self.start_station = None
        self.clear_all_labels()

    def clear_all_labels(self):
        for station in self.stations:
            station.clear_label()

    def calculate_optimal_routes(self):
        station_positions = [(station.x, station.y) for station in self.stations]
        station_shapes = [station.shape for station in self.stations]
        number_of_lines = len(self.lines)
        
        self.optimal_routes, _ = calculate_optimal_routes(station_positions, station_shapes, number_of_lines)

    def run(self):
        clock = pygame.time.Clock()
        running = True

        for _ in range(15):  # Generate 15 stations initially
            self.generate_station()

        self.calculate_optimal_routes()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    current_time = time.time()
                    x, y = event.pos

                    if event.button == 1:  # 왼쪽 클릭
                        if current_time - self.last_double_click_time < self.double_click_interval:
                            # 더블클릭 감지
                            for color, line in self.lines.items():
                                on_line, index = self.is_point_on_line(x, y, line)
                                if on_line:
                                    self.remove_connection(line, index)
                                    break
                        else:
                            # 단일 클릭 처리
                            if current_time - self.last_click_time < DEBOUNCE_TIME:
                                continue  # Skip this event to debounce
                            self.last_click_time = current_time

                            if self.reset_button.collidepoint(x, y):
                                self.reset_lines()
                            else:
                                # Check if a color button was clicked
                                for color, rect in COLOR_BUTTONS.items():
                                    if rect.collidepoint(x, y):
                                        self.selected_color = color
                                        self.current_line = None
                                        self.start_station = None
                                        self.clear_all_labels()
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
                                            if self.available_connections > 0:
                                                if not self.current_line:
                                                    self.current_line = self.lines[self.selected_color]
                                                    self.clear_all_labels()
                                                    clicked_station.set_label("S")
                                                    self.start_station = clicked_station
                                                    self.current_line.add_station(clicked_station, self)
                                                else:
                                                    if self.current_line.add_station(clicked_station, self):
                                                        clicked_station.set_label("E")
                                                        if clicked_station == self.start_station:
                                                            self.current_line = None
                                                            self.start_station = None

                        self.last_double_click_time = current_time

                    elif event.button == 3:  # 오른쪽 클릭
                        clicked_station = None
                        for station in self.stations:
                            if math.hypot(station.x - x, station.y - y) < STATION_RADIUS:
                                clicked_station = station
                                break
                        if clicked_station:
                            for line in self.lines.values():
                                if clicked_station in line.stations:
                                    line.remove_station(clicked_station)
                                    self.available_connections += 1
                            clicked_station.clear_label()
                            self.current_line = None
                            self.start_station = None

            self.generate_passenger()

            for line in self.lines.values():
                if line.train:
                    self.score += line.train.move()

            self.draw_game(game_screen)
            pygame.display.flip()

            self.draw_optimization(optimization_screen)
            optimization_window.blit(optimization_screen, (0, 0))
            pygame.display.flip()

            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
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

    # Create two separate windows
    game_screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mini Metro Game")

    optimization_window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE, 32)
    pygame.display.set_caption("Optimized Routes")

    game = Game()
    game.run()