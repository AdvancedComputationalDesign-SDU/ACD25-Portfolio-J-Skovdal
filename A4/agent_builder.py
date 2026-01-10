import rhinoscriptsyntax as rs
import random
import numpy as np
import uuid
import sys

# increase recursion depth for Grasshopper recompute loops
try:
    sys.setrecursionlimit(2000)
except Exception:
    pass


# -------------------------------
# GH PYTHON INPUTS
# -------------------------------
# seed: int (Random seed for reproducibility)
# N: int (Initial number of agents spawned on the surface)

# reset: bool (Reinitialize the simulation when True)

# start_surface: Surface (Base surface on which agents are spawned and constrained)

# vision_radius: float (Neighbor sensing radius for agent interaction)
# max_speed: float (Maximum agent movement speed per step)
# max_slope: float (Slope threshold used to slow agents (resistance))
# alignment_weight: float (Strength of alignment to principal curvature direction)
# separation_weight: float (Strength of repulsion from nearby agents)
# jitter: float (Random perturbation applied when agents become stationary)
# -------------------------------


# -------------------------------
# Utility functions
# -------------------------------

def seed_everything(seed):  # seed random + numpy
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

seed_everything(42)


# -------------------------------
# Helper functions
# -------------------------------

def generate_random_point_on_surface(surface):  # random UV sample
    if not surface:
        return None
    domainU = rs.SurfaceDomain(surface, 0)
    domainV = rs.SurfaceDomain(surface, 1)
    u = random.uniform(domainU[0], domainU[1])
    v = random.uniform(domainV[0], domainV[1])
    pt = rs.EvaluateSurface(surface, u, v)
    return pt if pt else None

def get_uv(surface, point):  # closest UV on surface
    if not surface or point is None:
        return None
    return rs.SurfaceClosestPoint(surface, point)

def sample_curvature(surface, uv):  # mean curvature + principal dir
    if not surface or not uv:
        return 0.0, (0.0, 0.0, 0.0)
    try:
        curv = rs.SurfaceCurvature(surface, uv)
        if not curv or len(curv) < 5:
            return 0.0, (0.0, 0.0, 0.0)
        k1 = curv[2] or 0.0
        k2 = curv[3] or 0.0
        mean_c = 0.5 * (k1 + k2)
        dir1 = tuple(curv[4]) if curv[4] else (0.0, 0.0, 0.0)
        return float(mean_c), dir1
    except Exception:
        return 0.0, (0.0, 0.0, 0.0)

def sample_slope(surface, uv, step=1e-3):  # finite diff slope
    if not surface or not uv:
        return (0.0, 0.0, 0.0), 0.0
    u, v = uv
    try:
        p0 = rs.EvaluateSurface(surface, u, v)
        pu = rs.EvaluateSurface(surface, u + step, v)
        pv = rs.EvaluateSurface(surface, u, v + step)
        if not p0 or not pu or not pv:
            return (0.0, 0.0, 0.0), 0.0
        p0 = np.array([p0.X, p0.Y, p0.Z])
        pu = np.array([pu.X, pu.Y, pu.Z])
        pv = np.array([pv.X, pv.Y, pv.Z])
    except Exception:
        return (0.0, 0.0, 0.0), 0.0

    slope_vec = (pu - p0) + (pv - p0)
    slope_mag = float(np.linalg.norm(slope_vec))
    return (slope_vec[0], slope_vec[1], slope_vec[2]), slope_mag


# Agent spawning helper
def spawn_agent_near(agent, surface, offset=0.2):  # spawn near parent
    try:
        jitter = (
            random.uniform(-offset, offset),
            random.uniform(-offset, offset),
            0.0
        )
        new_pos = rs.PointAdd(agent.position, jitter)
        uv = rs.SurfaceClosestPoint(surface, new_pos)
        if uv:
            new_pos = rs.EvaluateSurface(surface, uv[0], uv[1])
        vx = random.uniform(-0.05, 0.05)
        vy = random.uniform(-0.05, 0.05)
        return Agent(new_pos, (vx, vy, 0.0))
    except Exception:
        return None


# -------------------------------
# Core agent class
# -------------------------------

class Agent:  

    def __init__(self, position, velocity):  # initialize agent
        self.id = uuid.uuid4().hex
        self.position = position
        self.velocity = velocity
        self.age = 0
        self.is_alive = True
        self.path = [position]

        self.uv = None
        self.curvature_mean = 0.0
        self.curvature_dir = (0.0, 0.0, 0.0)
        self.slope_vector = (0.0, 0.0, 0.0)
        self.slope_magnitude = 0.0
        self.neighbors = []

    def sense(self, agents, surface, vision_radius):  # sample geometry + neighbors
        self.uv = get_uv(surface, self.position)
        if self.uv:
            self.curvature_mean, self.curvature_dir = sample_curvature(surface, self.uv)
            self.slope_vector, self.slope_magnitude = sample_slope(surface, self.uv)

        self.neighbors = []
        if vision_radius is None:
            return
        for other in agents:
            if other.id == self.id:
                continue
            try:
                d = rs.Distance(self.position, other.position)
            except Exception:
                continue
            if d is not None and d <= vision_radius:
                self.neighbors.append((other, float(d)))

    def decide(self, max_speed=0.5, max_slope=0.8,
               alignment_weight=0.05, separation_weight=0.12,
               jitter=0.01):  # update velocity
        if not self.is_alive:
            return

        # slope resistance
        slope_mag = self.slope_magnitude or 0.0
        resistance = max(0.2, 1.0 - slope_mag / max_slope) if max_slope else 1.0
        self.velocity = tuple(rs.VectorScale(self.velocity, resistance))

        # curvature alignment
        if rs.VectorLength(self.curvature_dir) > 1e-6:
            align_w = alignment_weight * (4.0 if abs(self.curvature_mean) < 0.1 else 1.0)
            c_dir = rs.VectorUnitize(self.curvature_dir)
            self.velocity = tuple(rs.VectorAdd(self.velocity, rs.VectorScale(c_dir, align_w)))

        # separation
        if self.neighbors:
            away = (0.0, 0.0, 0.0)
            for other, dist in self.neighbors:
                vec = rs.VectorCreate(self.position, other.position)
                if rs.VectorLength(vec) > 1e-9:
                    away = rs.VectorAdd(away, rs.VectorScale(rs.VectorUnitize(vec), 1.0 / max(dist, 1e-6)))
            if rs.VectorLength(away) > 1e-9:
                self.velocity = tuple(rs.VectorAdd(
                    self.velocity,
                    rs.VectorScale(rs.VectorUnitize(away), separation_weight)
                ))

        # clamp speed
        speed = rs.VectorLength(self.velocity)
        if speed > max_speed:
            self.velocity = tuple(rs.VectorScale(rs.VectorUnitize(self.velocity), max_speed))

        # jitter if stuck
        if rs.VectorLength(self.velocity) < 1e-4:
            self.velocity = tuple(rs.VectorAdd(
                self.velocity,
                (random.uniform(-jitter, jitter), random.uniform(-jitter, jitter), 0.0)
            ))

    def move(self, surface):  # move + project to surface
        if not self.is_alive:
            return
        new_pos = rs.PointAdd(self.position, self.velocity)
        uv = rs.SurfaceClosestPoint(surface, new_pos) if surface else None
        self.position = rs.EvaluateSurface(surface, uv[0], uv[1]) if uv else new_pos
        self.path.append(self.position)

    def update(self, agents, surface,
               vision_radius=1.0, max_speed=0.5,
               max_slope=0.8, alignment_weight=0.05,
               separation_weight=0.12, jitter=0.01,
               max_age=200, slope_kill=1.2,
               curvature_spawn=0.15, spawn_chance=0.02,
               max_neighbors=6):  # full lifecycle update

        if not self.is_alive:
            return None

        self.sense(agents, surface, vision_radius)
        self.decide(max_speed, max_slope, alignment_weight, separation_weight, jitter)
        self.move(surface)
        self.age += 1

        # death rules
        if self.age > max_age or self.slope_magnitude > slope_kill:
            self.is_alive = False
            return None

        # spawn rules
        prob = spawn_chance
        if abs(self.curvature_mean) > curvature_spawn:
            prob *= 3.0
        if len(self.neighbors) > max_neighbors:
            prob = 0.0

        if random.random() < prob:
            return spawn_agent_near(self, surface)

        return None


# -------------------------------
# Factory for creating agents
# -------------------------------

def build_agents(num_agents, start_surface):  # initial population
    if not start_surface or not rs.IsSurface(start_surface):
        return []
    agents = []
    for _ in range(num_agents):
        pos = generate_random_point_on_surface(start_surface)
        if pos:
            agents.append(Agent(pos, (random.uniform(-0.05, 0.05),
                                      random.uniform(-0.05, 0.05), 0.0)))
    return agents


# -------------------------------
# Grasshopper script instance (Pipeline)
# -------------------------------

class MyComponent(Grasshopper.Kernel.GH_ScriptInstance):

    def RunScript(self, seed:int, N:int, reset:bool,
                  start_surface,
                  vision_radius:float=1.0,
                  max_speed:float=0.5,
                  max_slope:float=0.8,
                  alignment_weight:float=0.05,
                  separation_weight:float=0.12,
                  jitter:float=0.01):

        seed_everything(seed)

        if reset or not hasattr(self, "agents") or self.agents is None:
            self.agents = build_agents(N, start_surface)

        active_agents = []
        new_agents = []

        for agent in self.agents:
            spawned = agent.update(
                self.agents, start_surface,
                vision_radius, max_speed, max_slope,
                alignment_weight, separation_weight, jitter
            )
            if agent.is_alive:
                active_agents.append(agent)
            if spawned:
                new_agents.append(spawned)

        self.agents = active_agents + new_agents

        return self