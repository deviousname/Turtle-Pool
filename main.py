import pygame
from pygame.locals import QUIT, KEYDOWN
import numpy as np
from pygame.math import Vector2
import pygame.gfxdraw

class Ball:
    def __init__(self, pos, color):
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.color = color
        self.radius = 10

    def move(self):
        self.pos += self.vel
        self.vel *= 0.98  # Friction

    def draw(self, screen):
        # Draw the outline first
        pygame.draw.circle(screen, (0, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius + 1)
        
        # Then draw the ball over the outline
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

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
        
        self.flip_x = False
        self.flip_y = False
        self.rotation_angle = 0
        self.p = 0.0
        self.direction = 1
        self.delta_p = 0.001

        self.is_dragging = False
        self.drag_start = Vector2(0, 0)
        self.FRICTION = 0.98
        
        # Cue ball
        self.cue_ball = Ball(Vector2(self.WIDTH / 2, self.HEIGHT - 100), (255, 255, 255))  # White color

        # Pool stick
        self.pool_stick = PoolStick()

        # Setup pool balls
        self.setup_balls()

        # Create 6 holes
        self.holes = self.generate_holes(7)
        
    def init_game_state(self):
        self.current_player = 1
        self.score_player1 = 0
        self.score_player2 = 0

    def setup_balls(self):
        self.balls = [self.cue_ball]
        colors = [(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 0), (0, 255, 255), (255, 0, 255), (255, 165, 0)]
        start_x, start_y = self.WIDTH / 2, self.HEIGHT / 2
        spacing = 22  # Spacing between balls
        for row in range(1, 7):
            for col in range(row):
                x = start_x + col * spacing - (row-1) * spacing / 2
                y = start_y + (row-1) * spacing
                color = colors[(row + col) % len(colors)]
                self.balls.append(Ball(Vector2(x, y), color))

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
        self.holes = self.generate_holes_from_points(points, 7)

        pygame.draw.polygon(self.screen, self.GREEN, points)
        self.draw_wooden_edge(self.screen, points)

        # Draw the holes
        for hole in self.holes:
            hole.draw(self.screen)
            
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

    def draw_ball(self):
        pygame.draw.circle(self.screen, self.WHITE, (int(self.ball_pos.x), int(self.ball_pos.y)), self.ball_radius)

    def handle_ball_drag(self, event, ball):
        all_balls_stopped = all(ball.vel == Vector2(0, 0) for ball in self.balls)

        if not all_balls_stopped:
            # Exit this function immediately if any ball is moving.
            return 
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

    def run(self):
        running = True
        self.ball_was_moving = False
        self.player_scored = False
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        running = False
                    elif event.type == KEYDOWN:
                        if event.key == pygame.K_r:
                            self.rotation_angle += np.pi / 6
                        elif event.key == pygame.K_q:
                            self.flip_x = not self.flip_x
                        elif event.key == pygame.K_e:
                            self.flip_y = not self.flip_y
                    self.handle_ball_drag(event, self.cue_ball)

                self.screen.fill(self.WHITE)
                self.draw_polygon(self.p)
                
                for ball in self.balls:
                    self.move_ball(ball)
                    self.handle_ball_polygon_collision(ball)
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
                        self.handle_ball_collision(ball1, ball2)
                    ball1.draw(self.screen)
            
                self.pool_stick.draw(self.screen)
                self.draw_score()
                pygame.display.flip()

                self.p += self.direction * self.delta_p
                if self.p > 1:
                    self.p = 1
                    self.direction = -1
                elif self.p < 0:
                    self.p = 0
                    self.direction = 1

                self.clock.tick(60)
            except Exception as e:
                print(e)
                pass
        pygame.quit()

# Run the program
if __name__ == '__main__':
    visualizer = Turtle_Pool()
    visualizer.run()
    
# End of the line, partner.
