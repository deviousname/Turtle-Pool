import pygame, math, time
from pygame.locals import QUIT, KEYDOWN, MOUSEBUTTONDOWN
import numpy as np
from pygame.math import Vector2
import pygame.gfxdraw
import mido, threading

class Ball:
    def __init__(self, pos, color, is_striped=False):
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.color = color
        self.is_striped = is_striped
        self.radius = 10
        self.angle = 0  # rotation angle of the stripes
        self.offset = 0 # distance from the center to the beginning of the stripe
        self.offset_direction = 1  # controls the direction of stripe offset (1 for outward, -1 for inward)

    def move(self):
        self.pos += self.vel
        self.vel *= 0.98  # Friction
        self.angle += self.vel.length() * 0.05
        
        # Only adjust the stripe offset when the ball is in motion
        if self.vel.length() > 0.1:  # Change 0.1 to a suitable threshold if needed
            self.offset += self.offset_direction / 4
            if self.offset > self.radius or self.offset < -self.radius:
                self.offset_direction *= -1

    def draw(self, screen):        
        # Draw the ball
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        
        if self.is_striped:
            stripe_width = 5

            # Calculate the effective radius and rotated stripe positions based on the offset
            effective_radius = self.radius - abs(self.offset)
            x1 = effective_radius * math.cos(self.angle)
            y1 = effective_radius * math.sin(self.angle)
            
            # Calculate tangent point on the circle's perimeter
            tangent_angle = math.asin(effective_radius / self.radius)
            end_angle_1 = self.angle + tangent_angle
            end_angle_2 = self.angle - tangent_angle

            # Determine the end points of the stripe where it touches the circle's perimeter
            end_x1 = self.pos.x + self.radius * math.cos(end_angle_1)
            end_y1 = self.pos.y + self.radius * math.sin(end_angle_1)
            end_x2 = self.pos.x + self.radius * math.cos(end_angle_2)
            end_y2 = self.pos.y + self.radius * math.sin(end_angle_2)
            
            pygame.draw.line(screen, (255, 255, 255), (end_x1, end_y1), (end_x2, end_y2), stripe_width)

            # Determine the position opposite to the stripe's center for the small circle
            opposite_angle = self.angle + math.pi
            circle_x = self.pos.x + effective_radius * math.cos(opposite_angle)
            circle_y = self.pos.y + effective_radius * math.sin(opposite_angle)
            
            # Adjust the circle's radius based on its distance from the ball's center
            max_circle_radius = stripe_width
            circle_radius = max_circle_radius * (1 - (effective_radius / self.radius))

            # Draw the small circle opposite to the stripe
            pygame.draw.circle(screen, (255, 255, 255), (int(circle_x), int(circle_y)), int(circle_radius))

        # Draw the outline
        pygame.draw.circle(screen, (0, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius + 2, 2)

class Hole:
    def __init__(self, pos):
        self.pos = Vector2(pos)
        self.radius = 12  # Slightly larger than a ball
        self.color = (3, 4, 14)  # Dark color for the hole

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        
class PoolStick:
    def __init__(self):
        self.start_position = Vector2(0, 0)
        self.end_position = Vector2(0, 0)
        self.is_visible = False

    def set_start_position(self, pos):
        self.start_position = Vector2(pos)
    
    def set_end_position(self, pos):
        self.end_position = Vector2(pos)

    def draw(self, screen):
        if self.is_visible:
            # Calculate the direction and magnitude of the pool stick
            direction = self.end_position - self.start_position
            magnitude = direction.length()

            # Calculate a normalized direction vector
            direction.normalize_ip()

            # Draw the pool stick with a tapered effect using polygons
            thickness_tip = 3 
            thickness_base = 10 

            offset_base = direction.rotate(90) * (thickness_base / 2)
            offset_tip = direction.rotate(90) * (thickness_tip / 2)

            # Define the four corners of the polygon for the border
            p1_border = self.end_position + offset_base + direction.rotate(90)
            p2_border = self.end_position - offset_base - direction.rotate(90)
            p3_border = self.start_position - offset_tip - direction.rotate(90)
            p4_border = self.start_position + offset_tip + direction.rotate(90)
            
            # Draw the border first
            border_color = (40, 40, 40)  # Slightly off black/brown
            pygame.draw.polygon(screen, border_color, [p1_border, p2_border, p3_border, p4_border])
            
            # Define the four corners of the polygon
            p1 = self.end_position + offset_base
            p2 = self.end_position - offset_base
            p3 = self.start_position - offset_tip
            p4 = self.start_position + offset_tip

            # Color gradients for the wood grain
            base_color = (139, 69, 19)  # Brown
            gradient_colors = [
                (160, 82, 45),
                (205, 133, 63),
                (210, 105, 30)
            ]

            # Draw the main body of the stick with gradients
            step = magnitude / len(gradient_colors)
            for i, color in enumerate(gradient_colors):
                start_frac = i / len(gradient_colors)
                end_frac = (i + 1) / len(gradient_colors)

                current_thickness_start = thickness_base * (1 - start_frac) + thickness_tip * start_frac
                current_thickness_end = thickness_base * (1 - end_frac) + thickness_tip * end_frac

                offset_start = direction.rotate(90) * (current_thickness_start / 2)
                offset_end = direction.rotate(90) * (current_thickness_end / 2)

                pygame.draw.polygon(screen, color, [
                    self.end_position - direction * magnitude * start_frac + offset_start,  # Starting from end_position
                    self.end_position - direction * magnitude * start_frac - offset_start,
                    self.end_position - direction * magnitude * end_frac - offset_end,
                    self.end_position - direction * magnitude * end_frac + offset_end
                ])

            # Draw the ferrule: a small circle slightly behind the tip
            ferrule_offset = 5  # Adjust this to control the length of the ferrule
            ferrule_position = self.start_position + direction * ferrule_offset
            pygame.draw.circle(screen, (255, 255, 255), ferrule_position, 3.5)  # White color for the ferrule

            # Draw the pool stick tip at the start_position
            pygame.draw.circle(screen, (127, 127, 255), self.start_position, 3)

            # Draw the butt of the pool stick at the end_position
            pygame.draw.circle(screen, (40, 40, 40), self.end_position, thickness_base / 2)

class Turtle_Pool:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        
        # Constants
        self.WIDTH, self.HEIGHT = 768, 768
        self.WHITE = (255,255,255)
        self.GREEN = (0, 255, 0)
        
        # Screen initialization
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Turtle Pool")
        
        # State
        self.init_game_state()

        # Data - Spectre tile
        self.n = np.arange(1, 15)
        self.m_values = np.cos(1.6 * self.n) + 2
        self.divisors = np.array([0.5, 2, -2, 3, 2, 3, -2, 3, 2, -3, 2, -3, 2, 3])
        self.a_values = np.cumsum(np.pi / self.divisors)
        self.current_table_points = []
        self.flip_x = False
        self.flip_y = False
        self.rotation_angle = 0
        self.p = 0.0
        self.direction = 1
        self.delta_p = 0.001
        self.polygon_surface = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)  # Ensure it supports transparency
        self.last_click_time = 0
        self.is_dragging = False
        self.drag_start = Vector2(0, 0)
        self.FRICTION = 0.98
        
        # Cue ball
        self.cue_ball = Ball(Vector2(self.WIDTH / 2, self.HEIGHT - (self.HEIGHT //2 + 60)), (255, 255, 255))  # White color

        # Pool stick
        self.pool_stick = PoolStick()

        # Setup pool balls
        self.setup_balls()

        # Create 7 holes
        self.holes = self.generate_holes(7)

        # Start sound engine
        self.midi_instrument = MidiInstrument()

    def init_game_state(self):
        self.current_player = 1
        self.score_player1 = 0
        self.score_player2 = 0

    def setup_balls(self):
        self.init_game_state()
        self.balls = [self.cue_ball]
        
        # Defining solid and striped colors
        solid_colors = [
            (255, 255, 0),  # Yellow
            (0, 0, 255),   # Blue
            (255, 0, 0),   # Red
            (128, 0, 128), # Purple
            (255, 165, 0), # Orange
            (0, 255, 0),   # Green
            (128, 0, 0)    # Maroon
        ]

        start_x, start_y = self.WIDTH / 2, self.HEIGHT / 2
        spacing = 22  # Spacing between balls
        
        # Order of the balls in the rack
        order = [
            0, 
            1, 2, 
            4, 3, 5,
            7, 6, 8, 9,
            14, 13, 12, 10, 11
        ]

        idx = 0
        ball_idx = 0
        for row in range(1, 6):  # Adjusted range to account for 15 balls + 1 cue ball
            for col in range(row):
                if order[ball_idx] == 8:  # For the black ball
                    color = (0, 0, 0)
                    is_striped = False
                else:
                    color = solid_colors[order[ball_idx] % 7]
                    is_striped = order[ball_idx] >= 7

                x = start_x + col * spacing - (row-1) * spacing / 2
                y = start_y + (row-1) * spacing
                self.balls.append(Ball(Vector2(x, y), color, is_striped))
                
                ball_idx += 1

    def switch_player(self):
        self.current_player = 3 - self.current_player  # switches between 1 and 2

    def get_free_position(self):
        """Get a free position at the center of the table that doesn't overlap with other balls."""
        center_pos = Vector2(self.WIDTH / 2, self.HEIGHT / 2)
        while any(ball.pos.distance_to(center_pos) < 2 * ball.radius for ball in self.balls):
            center_pos += Vector2(5, 5)  # Adjust the position slightly
        return center_pos
        
    def get_polygon_points(self, p):
        x, y = self.f(p)
        for i in range(len(x)):
            if self.flip_x:
                x[i] = -x[i]
            if self.flip_y:
                y[i] = -y[i]
            x[i], y[i] = self.rotate_point(x[i], y[i], self.rotation_angle, 0, 0)
        
        normalized_x = (x - x.min()) / (x.max() - x.min()) * (self.WIDTH - 40) + 20
        normalized_y = (y - y.min()) / (y.max() - y.min()) * (self.HEIGHT - 40) + 20
        
        return normalized_x, normalized_y
    
    def generate_holes(self, num_holes):
        # This function generates holes spread around the polygon
        points = list(zip(*self.get_polygon_points(0.5)))  # Mid points
        step = len(points) // num_holes
        return [Hole(Vector2(points[i % len(points)])) for i in range(0, len(points), step)]
            
    def draw_wooden_edge(self, screen, points):
        BORDER_WIDTH = 16  # Adjust as per preference
        border_color = (42, 42, 42)  # Slightly off black/brown

        # Draw the base border
        pygame.draw.lines(screen, border_color, closed=True, points=points, width=BORDER_WIDTH)

        # Color gradients for the wood grain
        gradient_colors = [
            (160, 82, 45),
            (205, 133, 63),
            (210, 105, 30)
        ]

        # Draw each segment with gradient colors
        for i in range(len(points)):
            start_point = pygame.Vector2(points[i])
            end_point = pygame.Vector2(points[(i + 1) % len(points)])  # Loop back to the start for the last segment

            for color in gradient_colors:
                pygame.draw.line(screen, color, start_point, end_point, BORDER_WIDTH - 1)  # Adjust width to fit within the base border

                # Draw rounded ends using a pie slice (arc)
                angle_to_end = int(start_point.angle_to(end_point))
                pygame.gfxdraw.pie(screen, int(start_point.x), int(start_point.y), (BORDER_WIDTH - 1) // 2, angle_to_end - 90, angle_to_end + 90, color)
                pygame.gfxdraw.pie(screen, int(end_point.x), int(end_point.y), (BORDER_WIDTH - 1) // 2, angle_to_end + 90, angle_to_end - 90, color)

                # Fill in the gaps at the corners
                pygame.gfxdraw.filled_circle(screen, int(start_point.x), int(start_point.y), (BORDER_WIDTH - 1) // 2, color)
                pygame.gfxdraw.filled_circle(screen, int(end_point.x), int(end_point.y), (BORDER_WIDTH - 1) // 2, color)

    def generate_holes_from_points(self, points, num_holes, offset = 12):
        step = len(points) // num_holes
        holes = []

        for i in range(0, len(points), step):
            # Current vertex for the hole
            current_vertex = Vector2(points[i % len(points)])
            
            # Previous and next vertices
            prev_vertex = Vector2(points[(i - 1) % len(points)])
            next_vertex = Vector2(points[(i + 1) % len(points)])
            
            # Calculate the vectors pointing from the current vertex to its adjacent vertices
            vec_to_prev = prev_vertex - current_vertex
            vec_to_next = next_vertex - current_vertex
            
            # Normalize these vectors
            vec_to_prev.normalize_ip()
            vec_to_next.normalize_ip()
            
            # Calculate the mid-angle direction (it's the normalized sum of the two vectors)
            mid_angle_dir = (vec_to_prev + vec_to_next).normalize()

            # Offset the hole by 12 pixels in the mid-angle direction
            hole_position = current_vertex + mid_angle_dir * offset

            # If the hole is outside the polygon, invert its offset
            if not self.is_point_inside_polygon(hole_position, points):
                hole_position = current_vertex - mid_angle_dir * offset  # Invert offset
            
            holes.append(Hole(hole_position))

        return holes
    
    def is_point_inside_polygon(self, point, polygon):
        """Check if point is inside the polygon using the ray-casting algorithm."""
        x, y = point
        odd_nodes = False
        j = len(polygon) - 1  # The last vertex is the previous one to the first

        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if yi < y and yj >= y or yj < y and yi >= y:
                if xi + (y - yi) / (yj - yi) * (xj - xi) < x:
                    odd_nodes = not odd_nodes
            j = i

        return odd_nodes
    
    def point_inside_polygon(self, x, y, polygon):
        n = len(polygon)
        oddNodes = False
        j = n - 1

        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if yi < y and yj >= y or yj < y and yi >= y:
                if xi + (y - yi) / (yj - yi) * (xj - xi) < x:
                    oddNodes = not oddNodes
            j = i
        return oddNodes

    def rotate_point(self, x, y, angle, center_x, center_y):
        s, c = np.sin(angle), np.cos(angle)
        x, y = x - center_x, y - center_y
        new_x = x * c - y * s + center_x
        new_y = x * s + y * c + center_y
        return new_x, new_y

    def f(self, p):
        x_coords = np.cumsum((1-p + p*self.m_values) * np.cos(self.a_values))
        y_coords = np.cumsum((1-p + p*self.m_values) * np.sin(self.a_values))
        return x_coords, y_coords
    
    def draw_polygon(self, p=0.5): # draws the pool table, p is the transformation normal
        x, y = self.f(p)
        
        for i in range(len(x)):
            if self.flip_x:
                x[i] = -x[i]
            if self.flip_y:
                y[i] = -y[i]
            x[i], y[i] = self.rotate_point(x[i], y[i], self.rotation_angle, 0, 0)
        
        normalized_x = (x - x.min()) / (x.max() - x.min()) * (self.WIDTH - 40) + 20
        normalized_y = (y - y.min()) / (y.max() - y.min()) * (self.HEIGHT - 40) + 20
        
        points = list(zip(normalized_x, normalized_y))
        self.current_table_points = points
        self.holes = self.generate_holes_from_points(points, 7)
        
        # Clear the polygon surface and redraw the polygon on it
        self.polygon_surface.fill((0, 0, 0, 0))  # Clear with full transparency
        pygame.draw.polygon(self.polygon_surface, (0, 255, 0, 255), points)  # Draw with white color
        
        pygame.draw.polygon(self.screen, self.GREEN, points)
        self.draw_wooden_edge(self.screen, points)

        # Draw the holes
        for hole in self.holes:
            hole.draw(self.screen)

        return points
    
    def draw_ball(self):
        pygame.draw.circle(self.screen, self.WHITE, (int(self.ball_pos.x), int(self.ball_pos.y)), self.ball_radius)
            
    def move_ball(self, ball):
        ball.move()
        if ball.pos.x - ball.radius <= 0 or ball.pos.x + ball.radius >= self.WIDTH:
            ball.vel.x = -ball.vel.x

        if ball.pos.y - ball.radius <= 0 or ball.pos.y + ball.radius >= self.HEIGHT:
            ball.vel.y = -ball.vel.y

    def collides_with_segment(self, ball_pos, ball_radius, segment_start, segment_end):
        # Adjusted to handle a specific ball's position and radius
        line = segment_end - segment_start
        t = max(0, min(1, (ball_pos - segment_start).dot(line) / line.length_squared()))
        closest_point = segment_start + t * line
        return ball_pos.distance_to(closest_point) <= ball_radius
    
    def handle_ball_polygon_overlap(self, ball):
        polygon_points = list(zip(*self.get_polygon_points(self.p)))
        next_polygon_points = list(zip(*self.get_polygon_points(self.p + self.direction * self.delta_p)))  # Next frame's polygon points

        for i in range(len(polygon_points)):
            segment_start = Vector2(polygon_points[i])
            segment_end = Vector2(polygon_points[(i + 1) % len(polygon_points)])
            
            next_segment_start = Vector2(next_polygon_points[i])
            next_segment_end = Vector2(next_polygon_points[(i + 1) % len(next_polygon_points)])
            
            if self.collides_with_segment(ball.pos, ball.radius, segment_start, segment_end):
                segment_midpoint = (segment_start + segment_end) / 2
                next_segment_midpoint = (next_segment_start + next_segment_end) / 2
                
                move_direction = (next_segment_midpoint - segment_midpoint).normalize()
                
                # Push the ball out of the edge
                while self.collides_with_segment(ball.pos, ball.radius, segment_start, segment_end):
                    ball.pos += move_direction

                # Impart momentum to the ball
                ball.vel += move_direction * 2  # Adjust the multiplier for desired momentum

    def handle_ball_polygon_collision(self, ball):
        polygon_points = list(zip(*self.get_polygon_points(self.p)))
        for i in range(len(polygon_points)):
            segment_start = Vector2(polygon_points[i])
            segment_end = Vector2(polygon_points[(i + 1) % len(polygon_points)])

            if self.collides_with_segment(ball.pos, ball.radius, segment_start, segment_end):
                segment_normal = (segment_end - segment_start).rotate(90).normalize()
                reflection = 2 * ball.vel.dot(segment_normal) * segment_normal
                
                ball.vel -= reflection

                # Ensure the ball is outside of the segment after reflection.
                while self.collides_with_segment(ball.pos, ball.radius, segment_start, segment_end):
                    ball.pos += segment_normal
                return True

    def handle_ball_collision(self, ball1, ball2):
        # Check for collision between two balls
        distance = ball1.pos.distance_to(ball2.pos)
        if distance < ball1.radius + ball2.radius:
            
            # Push the balls out of each other to avoid overlap
            overlap = (ball1.radius + ball2.radius) - distance
            direction = (ball1.pos - ball2.pos).normalize()
            ball1.pos += direction * (overlap / 2)
            ball2.pos -= direction * (overlap / 2)

            # Calculate the normal and tangent vectors
            normal = direction
            tangent = Vector2(normal.y, -normal.x)

            # Calculate the velocity components along the normal and tangent
            v1n = ball1.vel.dot(normal)
            v1t = ball1.vel.dot(tangent)
            v2n = ball2.vel.dot(normal)
            v2t = ball2.vel.dot(tangent)

            # Use the conservation of momentum to calculate the new velocities along the normal
            v1n_new = v1n * (ball1.radius - ball2.radius) / (ball1.radius + ball2.radius) + v2n * 2 * ball2.radius / (ball1.radius + ball2.radius)
            v2n_new = v2n * (ball2.radius - ball1.radius) / (ball1.radius + ball2.radius) + v1n * 2 * ball1.radius / (ball1.radius + ball2.radius)

            # Update the velocities using the new normal velocities and the unchanged tangent velocities
            ball1.vel = v1n_new * normal + v1t * tangent
            ball2.vel = v2n_new * normal + v2t * tangent
            return True

    def draw_score(self):
        # Adjusting font size
        if self.current_player == 1:
            font1 = pygame.font.SysFont(None, 50)
            font2 = pygame.font.SysFont(None, 36)
            color1 = (255, 0, 0)  # Red for active player
            color2 = (0, 0, 255)  # Blue for inactive player
            self.screen.blit(font1.render(f'Player 1: {self.score_player1}', True, color1), (self.WIDTH - 250, 10))
            self.screen.blit(font2.render(f'Player 2: {self.score_player2}', True, color2), (self.WIDTH - 230, 60))
        else:
            font1 = pygame.font.SysFont(None, 36)
            font2 = pygame.font.SysFont(None, 50)
            color1 = (255, 0, 0)
            color2 = (0, 0, 255)
            self.screen.blit(font1.render(f'Player 1: {self.score_player1}', True, color1), (self.WIDTH - 230, 60))
            self.screen.blit(font2.render(f'Player 2: {self.score_player2}', True, color2), (self.WIDTH - 250, 10))

        # Display the value of self.p on the bottom right corner
        p_font = pygame.font.SysFont(None, 36)
        p_color = (0, 255, 0)
        p_text = f"P = {str(int(self.p*100)/100).replace('.', '.')}"
        p_text_surface = p_font.render(p_text, True, p_color)
        # Position the text to start at the bottom right corner. Adjust the -10 for fine-tuning the vertical position.
        p_position = (self.WIDTH - (self.WIDTH//7), self.HEIGHT - p_text_surface.get_height() -  (self.WIDTH//32))
        self.screen.blit(p_text_surface, p_position)
        
        if self.display_menu:  
            # Re-Rack button
            rerack_font = pygame.font.SysFont(None, 40)
            rerack_color = (255, 255, 255)  # White color for the text
            rerack_bg = (50, 50, 50)  # Dark grey color for the button background
            rerack_text = rerack_font.render('Re-Rack', True, rerack_color)
            rerack_text_width, rerack_text_height = rerack_text.get_size()
            
            # Button dimensions
            button_width = rerack_text_width + 20
            button_height = rerack_text_height + 10
            button_x = (self.WIDTH - button_width) // 2
            button_y = 10
            
            # Draw button background
            pygame.draw.rect(self.screen, rerack_bg, (button_x, button_y, button_width, button_height))
            # Draw the text on the button
            self.screen.blit(rerack_text, (button_x + 10, button_y + 5))

            # Check if the button is clicked
            mouse = pygame.mouse.get_pos()
            click = pygame.mouse.get_pressed()
            if button_x <= mouse[0] <= button_x + button_width and button_y <= mouse[1] <= button_y + button_height:
                if click[0]:  # If left mouse button is pressed
                    self.setup_balls()
              
            # End-Turn button
            endturn_font = pygame.font.SysFont(None, 40)
            endturn_color = (255, 255, 255)  # White color for the text
            endturn_bg = (50, 50, 50)  # Dark grey color for the button background
            endturn_text = endturn_font.render('Change-Player', True, endturn_color)
            endturn_text_width, endturn_text_height = endturn_text.get_size()
            
            # Button dimensions (positioned below Re-Rack button)
            button_width_endturn = endturn_text_width + 20
            button_height_endturn = endturn_text_height + 10
            button_x_endturn = (self.WIDTH - button_width_endturn) // 2
            button_y_endturn = button_y + button_height + 10  # 10 pixels below the Re-Rack button
            
            # Draw button background
            pygame.draw.rect(self.screen, endturn_bg, (button_x_endturn, button_y_endturn, button_width_endturn, button_height_endturn))

            # Draw the text on the button
            self.screen.blit(endturn_text, (button_x_endturn + 10, button_y_endturn + 5))

            # Check if the End-Turn button is clicked
            mouse = pygame.mouse.get_pos()
            click = pygame.mouse.get_pressed()

            # Get current time
            current_time = pygame.time.get_ticks()

            # Check if the Re-Rack button is clicked
            if button_x <= mouse[0] <= button_x + button_width and button_y <= mouse[1] <= button_y + button_height:
                if click[0] and current_time - self.last_click_time > 500:  # 500 milliseconds cooldown
                    self.setup_balls()
                    self.last_click_time = current_time

            # Check if the End-Turn button is clicked
            if button_x_endturn <= mouse[0] <= button_x_endturn + button_width_endturn and button_y_endturn <= mouse[1] <= button_y_endturn + button_height_endturn:
                if click[0] and current_time - self.last_click_time > 500:  # 500 milliseconds cooldown
                    if self.current_player == 1:
                        self.current_player = 2
                    else:
                        self.current_player = 1
                    self.last_click_time = current_time

            # Instrument-Change button
            instr_font = pygame.font.SysFont(None, 40)
            instr_color = (255, 255, 255)  # White color for the text
            instr_bg = (50, 50, 50)  # Dark grey color for the button background
            
            instr_name = GM_INSTRUMENTS[self.midi_instrument.instrument]
            instr_text = instr_font.render('< {} >'.format(instr_name), True, instr_color)
            instr_text_width, instr_text_height = instr_text.get_size()
            
            # Button dimensions (positioned below Change-Player button)
            button_width_instr = instr_text_width + 20
            button_height_instr = instr_text_height + 10
            button_x_instr = (self.WIDTH - button_width_instr) // 2
            button_y_instr = button_y_endturn + button_height_endturn + 10  # 10 pixels below the Change-Player button
            
            # Draw button background
            pygame.draw.rect(self.screen, instr_bg, (button_x_instr, button_y_instr, button_width_instr, button_height_instr))
            
            # Draw the text on the button
            self.screen.blit(instr_text, (button_x_instr + 10, button_y_instr + 5))
            
            # Check if the Instrument Up button is clicked
            if button_x_instr <= mouse[0] <= button_x_instr + instr_text_width // 3 and button_y_instr <= mouse[1] <= button_y_instr + button_height_instr:
                if click[0] and current_time - self.last_click_time > 500:  # 500 milliseconds cooldown
                    self.midi_instrument.instrument_down()
                    self.last_click_time = current_time

            # Check if the Instrument Down button is clicked
            if button_x_instr + 2 * instr_text_width // 3 <= mouse[0] <= button_x_instr + button_width_instr and button_y_instr <= mouse[1] <= button_y_instr + button_height_instr:
                if click[0] and current_time - self.last_click_time > 500:  # 500 milliseconds cooldown
                    self.midi_instrument.instrument_up()
                    self.last_click_time = current_time
                    
    def handle_ball_drag(self, event, ball):
        all_balls_stopped = all(ball.vel == Vector2(0, 0) for ball in self.balls)
        if self.player_shots > 0:            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ball.pos.distance_to(Vector2(event.pos)) <= ball.radius:
                    self.is_dragging = True
                    self.drag_start = Vector2(event.pos)
                    self.pool_stick.set_start_position(ball.pos)
                    self.pool_stick.set_end_position(self.drag_start)
                    self.pool_stick.is_visible = True

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:  # Right click
                self.cue_ball.pos = Vector2(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP or (event.type == pygame.ACTIVEEVENT and not event.gain and self.is_dragging):
                # The additional condition checks if the window lost focus while dragging
                if self.is_dragging:
                    drag_end = Vector2(pygame.mouse.get_pos())  # Use the current mouse position instead
                    ball.vel = (self.drag_start - drag_end) * 0.1  # Adjust this for different shot power
                    self.pool_stick.is_visible = False
                    self.is_dragging = False

            elif self.is_dragging:  # When dragging, constantly update pool stick's position
                self.pool_stick.set_end_position(Vector2(event.pos))
                
    def get_polygon_centroid(self, polygon):
        centroid = Vector2(0, 0)
        n = len(polygon)
        for point in polygon:
            centroid.x += point[0]
            centroid.y += point[1]
        centroid.x /= n
        centroid.y /= n
        return centroid
    
    def adjust_balls_after_rotation(self):
        # Calculate the centroid of the current table
        table_centroid = self.get_polygon_centroid(self.current_table_points)
        
        # Rotate ball positions and check their positions
        for ball in self.balls:
            ball.pos.x, ball.pos.y = self.rotate_point(ball.pos.x, ball.pos.y, np.pi / 6, self.WIDTH / 2, self.HEIGHT / 2)
            
            # If ball is outside table, adjust its position
            while not self.point_inside_polygon(ball.pos.x, ball.pos.y, self.current_table_points):
                # Move ball towards the centroid of the table
                direction_to_centroid = table_centroid - ball.pos
                direction_to_centroid = direction_to_centroid.normalize()  # Get unit vector towards centroid
                ball.pos += direction_to_centroid  # Move ball slightly towards the centroid
            
            # Rotate ball velocities to adjust trajectories
            ball.vel.x, ball.vel.y = self.rotate_point(ball.vel.x, ball.vel.y, np.pi / 6, 0, 0)
            
    def run(self):
        running = True
        self.ball_was_moving = False
        self.player_scored = False
        self.display_menu = False
        self.mouse_button_up  = False
        self.player_shots = 3 # need to do something with this still
        while running:
            try:
                self.screen.fill(self.WHITE) # fill the background whatever color
                polygon_points = self.draw_polygon(self.p) # draw the board

                for event in pygame.event.get():
                    if event.type == QUIT:
                        running = False
                    elif event.type == KEYDOWN:
                        if event.key == pygame.K_UP:
                            self.midi_instrument.note_up()
                        elif event.key == pygame.K_DOWN:
                            self.midi_instrument.note_down()
                        elif event.key == pygame.K_LEFT:
                            self.midi_instrument.instrument_down()
                        elif event.key == pygame.K_RIGHT:
                            self.midi_instrument.instrument_up()
                        elif event.key == pygame.K_r:
                            self.rotation_angle += np.pi / 6
                            self.adjust_balls_after_rotation()
                        elif event.key == pygame.K_q:
                            self.flip_x = not self.flip_x
                        elif event.key == pygame.K_e:
                            self.flip_y = not self.flip_y
                        elif event.key == pygame.K_ESCAPE:
                            self.display_menu = not self.display_menu
                    if event.type == MOUSEBUTTONDOWN:
                        self.mouse_button_up  = True
                    elif event.type == MOUSEBUTTONUP:
                        self.mouse_button_up  = False
                self.handle_ball_drag(event, self.cue_ball)

                # When a collision occurs:
                for ball in self.balls:
                    self.move_ball(ball)
                    self.handle_ball_polygon_collision(ball)  # wall collide
                    self.handle_ball_polygon_overlap(ball)  # Check and handle ball overlap with polygon
                    for hole in self.holes:
                        if ball.pos.distance_to(hole.pos) < hole.radius:
                            self.balls.remove(ball)
                            if ball == self.cue_ball:  # If cue ball goes into the hole
                                ball.pos = self.get_free_position()
                                ball.vel = Vector2(0, 0)
                                self.balls.append(ball)  # Add back the cue ball
                            elif self.current_player == 1:
                                self.score_player1 += 1  # Opponent gets the point
                            else:
                                self.score_player2 += 1
                            self.player_scored = True  # Set the flag when a player scores

                # Check if all balls have stopped moving
                all_balls_stopped = all(ball.vel == Vector2(0, 0) for ball in self.balls)

                if all_balls_stopped and self.ball_was_moving:  
                    if not self.player_scored:  # Only switch players if the current player did not score
                        if self.current_player == 1:
                            self.current_player = 2
                        else:
                            self.current_player = 1
                    self.player_scored = False  # Reset the flag for the next turn

                # Update the ball_was_moving flag for the next frame
                self.ball_was_moving = not all_balls_stopped
        
                for hole in self.holes:
                    hole.draw(self.screen)
                    
                for i, ball1 in enumerate(self.balls):
                    for ball2 in self.balls[i+1:]:
                        if self.handle_ball_collision(ball1, ball2):
                            average_velocity = (ball1.vel + ball2.vel) / 2  # Compute the average velocity
                            midi_note = self.get_midi_note_from_velocity(average_velocity)
                            self.midi_instrument.play_collision_sound(midi_note)  # Play the note based on average velocity
                    ball1.draw(self.screen)

                try:
                    self.pool_stick.draw(self.screen)
                except:
                    pass
                
                self.draw_score()
                pygame.display.flip()

                pygame.display.update()
                self.p += self.direction * self.delta_p
                if self.p > 1:
                    self.p = 1
                    self.direction = -1
                elif self.p < 0:
                    self.p = 0
                    self.direction = 1

                self.clock.tick(60)
            except:
                pass
        pygame.quit()
        
    def get_midi_note_from_velocity(self, velocity, max_velocity=127, midpoint=25, scale_factor=3):  
        # The scale_factor controls the sensitivity around the midpoint
        midpoint_normalized = midpoint / 127.0
        x = (velocity.magnitude() / max_velocity) - midpoint_normalized
        y = np.tanh(x * scale_factor)
        midi_note = int((y + 1) / 2 * 127)
        return midi_note

class MidiInstrument:
    # Sound effect engine using mido's midi capabilities along with threading.
    def __init__(self):
        # Initialize your midi port here
        self.outport = mido.open_output()  # Use your MIDI port details here
        self.current_notes = {}
        self.instrument = 96
        self.current_note = 64  # Starting with Middle C
        self.change_instrument(self.instrument)
        self.note_lock = threading.Lock()
        
    def change_instrument(self, instrument):
        # Creates a 'program_change' MIDI message that changes the instrument.
        program_change = mido.Message('program_change', program=instrument)
        # Sends the 'program_change' MIDI message to the output port.
        self.outport.send(program_change)
        # Prints a statement indicating that the instrument has been changed.
        #print(f"Changed instrument to {GM_INSTRUMENTS[instrument], self.instrument}")

    def instrument_up(self):
        # Increases the instrument number by 1, but wraps around to 0 if the current instrument is the last one.
        self.instrument = (self.instrument + 1) % 128
        # Changes to the newly selected instrument.
        threading.Thread(target=self.change_instrument, args=(self.instrument,)).start()

    def instrument_down(self):
        # Decreases the instrument number by 1, but wraps around to the last instrument if the current instrument is the first one.
        self.instrument = (self.instrument - 1) % 128
        # Changes to the newly selected instrument.
        threading.Thread(target=self.change_instrument, args=(self.instrument,)).start()

    def note_on(self, original_note, shifted_note): 
        if original_note not in self.current_notes:
            note_on = mido.Message('note_on', note=shifted_note)
            self.outport.send(note_on)
            self.current_notes[original_note] = True

    def note_off(self, original_note, shifted_note):
        with self.note_lock:
            if original_note in self.current_notes:
                note_off_msg = mido.Message('note_off', note=shifted_note)
                self.outport.send(note_off_msg)
                del self.current_notes[original_note]
                
    def stop_sound(self, midi_note):
        shifted_note = (midi_note + 12) % 128
        self.note_off(midi_note, shifted_note)

    def note_up(self):
        # Increase the current note value
        if self.current_note < 127:  # 127 is the highest valid MIDI note value
            self.current_note += 1

    def note_down(self):
        # Decrease the current note value
        if self.current_note > 0:  # 0 is the lowest valid MIDI note value
            self.current_note -= 1

    def play_collision_sound(self, midi_note):
        # Start the sound effect in a new thread, passing the midi_note as an argument
        threading.Thread(target=self._play_collision_sound_thread, args=(midi_note,)).start()

    def _play_collision_sound_thread(self, midi_note):
        shifted_note = (midi_note + 12) % 128  # Increase by an octave for the sound effect
        self.note_on(midi_note, shifted_note)
        time.sleep(0.0625)
        self.note_off(midi_note, shifted_note)
        
GM_INSTRUMENTS = {
    0: 'Acoustic Grand Piano', 1: 'Bright Acoustic Piano', 2: 'Electric Grand Piano', 
    3: 'Honky-tonk Piano', 4: 'Electric Piano 1', 5: 'Electric Piano 2',
    6: 'Harpsichord', 7: 'Clavinet', 8: 'Celesta', 9: 'Glockenspiel',
    10: 'Music Box', 11: 'Vibraphone', 12: 'Marimba', 13: 'Xylophone',
    14: 'Tubular Bells', 15: 'Dulcimer', 16: 'Drawbar Organ', 17: 'Percussive Organ',
    18: 'Rock Organ', 19: 'Church Organ', 20: 'Reed Organ', 21: 'Accordion',
    22: 'Harmonica', 23: 'Tango Accordion', 24: 'Acoustic Guitar (nylon)',
    25: 'Acoustic Guitar (steel)', 26: 'Electric Guitar (jazz)', 
    27: 'Electric Guitar (clean)', 28: 'Electric Guitar (muted)', 
    29: 'Overdriven Guitar', 30: 'Distortion Guitar', 31: 'Guitar Harmonics', 
    32: 'Acoustic Bass', 33: 'Electric Bass (finger)', 34: 'Electric Bass (pick)', 
    35: 'Fretless Bass', 36: 'Slap Bass 1', 37: 'Slap Bass 2', 
    38: 'Synth Bass 1', 39: 'Synth Bass 2', 40: 'Violin', 41: 'Viola',
    42: 'Cello', 43: 'Contrabass', 44: 'Tremolo Strings', 45: 'Pizzicato Strings', 
    46: 'Orchestral Harp', 47: 'Timpani', 48: 'String Ensemble 1', 
    49: 'String Ensemble 2', 50: 'Synth Strings 1', 51: 'Synth Strings 2', 
    52: 'Choir Aahs', 53: 'Voice Oohs', 54: 'Synth Voice', 55: 'Orchestra Hit',
    56: 'Trumpet', 57: 'Trombone', 58: 'Tuba', 59: 'Muted Trumpet', 
    60: 'French Horn', 61: 'Brass Section', 62: 'Synth Brass 1', 
    63: 'Synth Brass 2', 64: 'Soprano Sax', 65: 'Alto Sax', 
    66: 'Tenor Sax', 67: 'Baritone Sax', 68: 'Oboe', 69: 'English Horn', 
    70: 'Bassoon', 71: 'Clarinet', 72: 'Piccolo', 73: 'Flute', 
    74: 'Recorder', 75: 'Pan Flute', 76: 'Blown Bottle', 
    77: 'Shakuhachi', 78: 'Whistle', 79: 'Ocarina', 80: 'Lead 1 (square)', 
    81: 'Lead 2 (sawtooth)', 82: 'Lead 3 (calliope)', 83: 'Lead 4 (chiff)', 
    84: 'Lead 5 (charang)', 85: 'Lead 6 (voice)', 86: 'Lead 7 (fifths)', 
    87: 'Lead 8 (bass + lead)', 88: 'Pad 1 (new age)', 89: 'Pad 2 (warm)', 
    90: 'Pad 3 (polysynth)', 91: 'Pad 4 (choir)', 92: 'Pad 5 (bowed)', 
    93: 'Pad 6 (metallic)', 94: 'Pad 7 (halo)', 95: 'Pad 8 (sweep)', 
    96: 'FX 1 (rain)', 97: 'FX 2 (soundtrack)', 98: 'FX 3 (crystal)', 
    99: 'FX 4 (atmosphere)', 100: 'FX 5 (brightness)', 101: 'FX 6 (goblins)', 
    102: 'FX 7 (echoes)', 103: 'FX 8 (sci-fi)', 104: 'Sitar', 105: 'Banjo', 
    106: 'Shamisen', 107: 'Koto', 108: 'Kalimba', 109: 'Bagpipe', 
    110: 'Fiddle', 111: 'Shanai', 112: 'Tinkle Bell', 113: 'Agogo', 
    114: 'Steel Drums', 115: 'Woodblock', 116: 'Taiko Drum', 
    117: 'Melodic Tom', 118: 'Synth Drum', 119: 'Reverse Cymbal', 
    120: 'Guitar Fret Noise', 121: 'Breath Noise', 122: 'Seashore', 
    123: 'Bird Tweet', 124: 'Telephone Ring', 125: 'Helicopter', 
    126: 'Applause', 127: 'Gunshot'
}
# Run the program
if __name__ == '__main__':
    turtle = Turtle_Pool()
    turtle.run()
