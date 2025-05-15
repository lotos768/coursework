import numpy as np


class RollupSimulation:
    def __init__(self, angle_deg, length, v0_val,
                 fric_inc, fric_hor, init_h_dist_param):

        self.g = 9.81
        self.angle = np.radians(angle_deg)
        self.L = length
        self.h_len_display = float(init_h_dist_param) + 5.0
        self.v0_input = abs(v0_val)
        self.friction_incline = fric_inc
        self.friction_horizontal = fric_hor
        self.c = 299792458
        self.body_radius = 0.2
        self.init_h_dist = float(init_h_dist_param)

        self.base_x = 0.0
        self.base_y = 0.0

        if self.L > 0 and self.angle < np.pi / 2 - 0.01:
            self.peak_x = -self.L * np.cos(self.angle)
        elif self.L > 0 and self.angle >= np.pi / 2 - 0.01:
            self.peak_x = 0.0
        else:
            self.peak_x = 0.0

        self.peak_y = self.L * np.sin(self.angle)

        self.x_plane = np.array([])
        self.y_plane = np.array([])
        self.x_horizontal = np.array([])
        self.y_horizontal = np.array([])

        self.reset()

    def _setup_display_planes(self):
        if self.L > 0:
            self.x_plane = np.linspace(self.peak_x, self.base_x, 100)
            if abs(self.peak_x - self.base_x) > 1e-9:
                slope = (self.peak_y - self.base_y) / \
                        (self.peak_x - self.base_x)
                self.y_plane = slope * (self.x_plane - self.base_x) + self.base_y
            elif self.L > 0:
                self.y_plane = np.linspace(self.base_y, self.peak_y, 100)
                self.x_plane = np.full_like(self.y_plane, self.base_x)
        else:
            self.x_plane = np.array([self.base_x])
            self.y_plane = np.array([self.base_y])

        _start_h_coord = self.base_x
        _end_h_coord = self.h_len_display

        if abs(_start_h_coord - _end_h_coord) < 1e-9:
             _end_h_coord = _start_h_coord + 1.0

        self.x_horizontal = np.linspace(_start_h_coord, _end_h_coord, 100)
        self.y_horizontal = np.zeros_like(self.x_horizontal)


        if self.x_plane.size == 0:
            self.x_plane = np.array([self.base_x])
        if self.y_plane.size == 0:
            self.y_plane = np.array([self.base_y])
        if self.x_horizontal.size == 0:
            self.x_horizontal = np.array([self.base_x])
            self.y_horizontal = np.array([self.base_y])

    def reset(self):
        self._setup_display_planes()

        self.t_global = 0.0
        self.dt = 0.05
        self.on_approach = True
        self.on_incline = False
        self.x_body = self.init_h_dist
        self.y_body = self.body_radius

        if self.v0_input > 1e-9 and self.init_h_dist > 1e-9:
            self.velocity = -self.v0_input
        else:
            self.velocity = 0.0

        self._finished = False

        if abs(self.init_h_dist) < 1e-9:
            self.on_approach = False
            self.on_incline = True
            self.x_body = self.base_x
            if abs(self.v0_input) > 1e-9:
                self.velocity = self.v0_input * np.cos(self.angle)
                if self.velocity <= 1e-6:
                    self._finished = True
            else:
                self.velocity = 0.0
                self._finished = True


        self.v_at_base = 0.0
        self.dist_incline = 0.0
        self.time_points = [0.0]
        self.velocity_points = [abs(self.velocity)]
        self.t_segment = 0.0

    def step(self, dt_param):
        if self._finished:
            self.t_global += dt_param
            self.time_points.append(self.time_points[-1] + dt_param)
            self.velocity_points.append(abs(self.velocity))
            return self.time_points[-1], self.velocity, self.x_body, self.y_body

        if self.on_approach:
            if abs(self.velocity) < 1e-6 and self.x_body > self.base_x + 1e-6:
                self._finished = True
            elif self.velocity == 0 and self.x_body <= self.base_x + 1e-6:
                self._finished = True
                self.x_body = self.base_x
                self.on_approach = False
                self.on_incline = True
                self.v_at_base = 0.0
                self.velocity = 0.0

            if not self._finished:
                a_h = 0.0
                if self.velocity < -1e-9:
                    a_h = self.friction_horizontal * self.g

                v_i = self.velocity
                v_f = v_i + a_h * dt_param

                stopped_on_approach = False
                if v_i < -1e-9 and v_f >= -1e-9 and a_h > 1e-9:
                    dt_s = -v_i / a_h
                    if 0 < dt_s < dt_param:
                        s = v_i * dt_s + 0.5 * a_h * dt_s ** 2
                        self.x_body += s
                        self.velocity = 0.0
                        self.t_segment += dt_s
                        stopped_on_approach = True
                        self._finished = True

                if not stopped_on_approach:
                    s = v_i * dt_param + 0.5 * a_h * dt_param ** 2
                    self.x_body += s
                    self.velocity = v_f
                    self.t_segment += dt_param

                self.y_body = self.body_radius

                if self.velocity >= -1e-9 and self.x_body > self.base_x + 1e-6:
                    self._finished = True
                    self.velocity = 0.0

                if self.x_body <= self.base_x + 1e-6 and not self._finished:
                    self.x_body = self.base_x
                    self.on_approach = False
                    self.on_incline = True
                    self.v_at_base = self.velocity
                    self.velocity = abs(self.v_at_base) * np.cos(self.angle)
                    self.velocity = max(0.0, min(self.velocity, self.c))
                    if self.velocity <= 1e-6:
                        self._finished = True
                        self.velocity = 0.0
                    else:
                         self._finished = False

                    self.dist_incline = 0.0
                    self.t_segment = 0.0

        elif self.on_incline:
            if abs(self.velocity) < 1e-6 and self.dist_incline < self.L - 1e-6:
                self._finished = True

            if not self._finished:
                a_i = -self.g * np.sin(self.angle) - self.friction_incline * self.g * np.cos(self.angle)
                v_i = self.velocity
                v_f = v_i + a_i * dt_param

                stopped_on_incline = False
                if v_f <= 1e-6 and v_i > 1e-6:
                    if abs(a_i) > 1e-9:
                        dt_s_inc = -v_i / a_i
                        if 0 < dt_s_inc < dt_param:
                            s_stop = v_i * dt_s_inc + 0.5 * a_i * dt_s_inc ** 2
                            self.dist_incline += s_stop
                            self.t_segment += dt_s_inc
                            stopped_on_incline = True
                            self.velocity = 0.0
                            self._finished = True

                if not stopped_on_incline and v_i > 1e-6 :
                    s = v_i * dt_param + 0.5 * a_i * dt_param ** 2
                    self.dist_incline += s
                    self.velocity = v_f
                    self.velocity = max(0.0, min(self.velocity, self.c))
                    self.t_segment += dt_param

                    if self.dist_incline >= self.L - 1e-6:
                        self.dist_incline = self.L
                        self._finished = True
                    elif self.velocity <= 1e-6:
                        self._finished = True
                elif v_i <= 1e-6:
                    self.t_segment += dt_param
                    self.velocity = 0.0
                    self._finished = True


            self.x_body = self.base_x - self.dist_incline * np.cos(self.angle)
            self.y_body = self.base_y + self.dist_incline * np.sin(self.angle) + self.body_radius

            if self.x_body < self.peak_x - 1e-6:
                self.x_body = self.peak_x
            if self.dist_incline > self.L + 1e-6:
                self.y_body = self.peak_y + self.body_radius


        self.t_global += dt_param
        self.time_points.append(self.t_global)
        self.velocity_points.append(abs(self.velocity) if not (self._finished and abs(self.velocity) < 1e-6) else 0.0)

        return self.time_points[-1], self.velocity, self.x_body, self.y_body

    def is_finished(self):
        return self._finished

    def get_plane_coordinates(self):
        return self.x_plane, self.y_plane

    def get_horizontal_coordinates(self):
        return self.x_horizontal, self.y_horizontal