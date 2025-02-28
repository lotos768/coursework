import numpy as np

class Simulation:
    def __init__(self, angle, length, horizontal_length, v0, friction_incline, friction_horizontal):
        self.g = 9.81
        self.angle = np.radians(angle)
        self.L = length
        self.horizontal_length = horizontal_length
        self.v0 = v0
        self.friction_incline = friction_incline
        self.friction_horizontal = friction_horizontal
        self.c = 299792458
        self.body_radius = 0.2
        self.reset()
        self.x_plane = np.linspace(0, self.L * np.cos(self.angle), 100)
        self.y_plane = -self.x_plane * np.tan(self.angle) + self.L * np.sin(self.angle)
        self.x_horizontal = np.linspace(self.L * np.cos(self.angle),
                                        self.L * np.cos(self.angle) + self.horizontal_length, 100)
        self.y_horizontal = np.zeros_like(self.x_horizontal)

    def reset(self):
        self.t = 0
        self.dt = 0.05
        self.x_body = 0
        self.y_body = self.L * np.sin(self.angle) + self.body_radius
        self.velocity = self.v0
        self.on_inclined_plane = True
        self.v0_horizontal = 0
        self.time_points = [0]
        self.velocity_points = [self.v0]

    def update_parameters(self, angle, length, horizontal_length, v0, friction_incline, friction_horizontal):
        self.angle = np.radians(angle)
        self.L = length
        self.horizontal_length = horizontal_length
        self.v0 = v0
        self.friction_incline = friction_incline
        self.friction_horizontal = friction_horizontal
        self.x_plane = np.linspace(0, self.L * np.cos(self.angle), 100)
        self.y_plane = -self.x_plane * np.tan(self.angle) + self.L * np.sin(self.angle)
        self.x_horizontal = np.linspace(self.L * np.cos(self.angle),
                                        self.L * np.cos(self.angle) + self.horizontal_length, 100)
        self.y_horizontal = np.zeros_like(self.x_horizontal)

        self.reset()


    def step(self, dt):
        if self.on_inclined_plane:
            a = self.g * np.sin(self.angle) - self.friction_incline * self.g * np.cos(self.angle)
            if a < 0 and self.velocity == 0:
                a = 0
            v = self.velocity + a * dt
            v = max(0, min(v, self.c))
            s = self.velocity * dt + 0.5 * a * dt ** 2
            self.x_body += s * np.cos(self.angle)
            self.y_body = -self.x_body * np.tan(self.angle) + self.L * np.sin(self.angle) + self.body_radius
            if self.x_body >= self.L * np.cos(self.angle):
                self.on_inclined_plane = False
                self.v0_horizontal = v * np.cos(self.angle)
                self.v0_horizontal = max(0, min(self.v0_horizontal, self.c))
                self.t = 0
                self.x_body = self.L * np.cos(self.angle)
                self.y_body = self.body_radius

            self.velocity = v
        else:
            a = -self.friction_horizontal * self.g
            v = self.v0_horizontal + a * self.t
            v = max(0, min(v, self.c))
            s = self.v0_horizontal * self.t + 0.5 * a * self.t ** 2
            self.x_body = self.L * np.cos(self.angle) + s
            self.y_body = self.body_radius
            if self.x_body >= self.L * np.cos(self.angle) + self.horizontal_length or v <= 0:
                if v < 0 : v = 0
                self.velocity = v
                self.t += dt
                self.time_points.append(self.time_points[-1] + dt)
                self.velocity_points.append(self.velocity)
                return self.time_points[-1], self.velocity, self.x_body, self.y_body

            self.velocity = v
        self.t += dt
        self.time_points.append(self.time_points[-1] + dt)
        self.velocity_points.append(self.velocity)

        return self.time_points[-1], self.velocity, self.x_body, self.y_body

    def is_finished(self):
        if not self.on_inclined_plane:
            if self.x_body >= self.L * np.cos(self.angle) + self.horizontal_length or self.velocity <=0:
                return True
        return False

    def get_plane_coordinates(self):
        return self.x_plane, self.y_plane

    def get_horizontal_coordinates(self):
        return self.x_horizontal, self.y_horizontal