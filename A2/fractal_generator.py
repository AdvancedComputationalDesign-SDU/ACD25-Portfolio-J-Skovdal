"""
Assignment 2: Exploring Fractals through Recursive Geometric Patterns

Author: Jakob Rasmussen
"""

import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import random

# --- Global List ---
line_list = []

# --- Utility Functions ---
def get_color(depth, max_depth):
    return plt.cm.viridis(1 - depth / max_depth)

def get_line_width(depth, initial_width, max_depth):
    return max(0.5, initial_width * (1 - depth / max_depth))

# --- Recursive Fractal Function ---
def generate_fractal(start_point, length, theta, depth, max_depth, angle, ratio, initial_width, attractor=None, field_strength=0.1, field_direction=np.pi/2):  # set base values for influences
    """
    Parameters:
    - start_point: Tuple (x, y), the current branch root coordinate.
    - length: Float, the current branch length.
    - theta: Float (radians), the orientation of the current branch.
    - depth: Int, current recursion depth.
    - max_depth: Int, maximum recursion depth of the fractal.
    - angle: Float (radians), fixed branching angle for child branches.
    - ratio: Float, scaling factor for branch length at each recursion.
    - trunk_rad: Float, base trunk radius (used for line thickness tapering).

    Geometric Influences:
    - attractor: Tuple (x, y), optional point that subtly attracts branches.
    - field_strength: Float (0–1), influence strength of the directional field.
    - field_direction: Float (radians), uniform field direction influencing growth.
    """
    if depth > max_depth:
        return

    x0, y0 = start_point
    rand_len = random.uniform(0.6 , 1) * length  # randomize branch length

    # Base end point
    x1 = x0 + rand_len * math.cos(theta)  # compute new x-coordinate
    y1 = y0 + rand_len * math.sin(theta)  # compute new y-coordinate

    # --- Apply Attractor Influence ----
    if attractor is not None:
        ax, ay = attractor
        dx, dy = ax - x0, ay - y0
        attract_angle = math.atan2(dy, dx)  # angle pointing toward attractor
        theta += (attract_angle - theta) * 0.1  # slightly bend branch toward attractor

    # --- Apply Field Influence ---
    theta += (field_direction - theta) * field_strength  # slightly bend branch toward field direction

    # Update end point after influences
    x1 = x0 + rand_len * math.cos(theta)  # recalculate x with influences
    y1 = y0 + rand_len * math.sin(theta)  # recalculate y with influences
    end_point = (x1, y1)

    # Store branch
    line_list.append((LineString([start_point, end_point]), depth, initial_width))

    # Increment depth
    next_depth = depth + 1

    # Length for child branches
    new_length = length * ratio

    # Fixed branch angles
    angle_variation = 0.15
    theta1 = theta + angle + random.uniform(-angle_variation, angle_variation)  # left branch angle
    theta2 = theta - angle + random.uniform(-angle_variation, angle_variation)  # right branch angle

    # Recurse for branches
    generate_fractal(end_point, new_length, theta1, next_depth, max_depth, angle, ratio, initial_width, attractor, field_strength, field_direction)  # recurse left branch
    generate_fractal(end_point, new_length, theta2, next_depth, max_depth, angle, ratio, initial_width, attractor, field_strength, field_direction)  # recurse right branch

# --- Main Execution ---
if __name__ == "__main__":

    # --- Parameters ---
    start_point = (0, 0)
    iterations = 10
    initial_len = 80
    initial_width = 3.5
    theta = math.radians(90)
    angle = math.radians(30)
    ratio = 0.75
    seed = 451

    # --- Geometric Influences ---
    attractor_pt = (200,250)
    field_strength_inf = 0.15
    field_dir = math.radians(90)


    # --- Record metadata ---
    RUN = dict(Depth=iterations, Angle=math.degrees(angle), Theta=math.degrees(theta), Length=initial_len, Scale=ratio, Width=initial_width, seed=seed, attractor_point=attractor_pt, field_strength=field_strength_inf, field_direction=math.degrees(field_dir))
    print("\nRun:", RUN, "\n")


    # --- Clear the line list ---
    line_list.clear()


    # --- Set random seed for reproducibility ---
    random.seed(seed)


    # --- Generate the fractal ---
    generate_fractal(start_point, initial_len, theta, 0, iterations, angle, ratio, initial_width, attractor=attractor_pt, field_strength=field_strength_inf, field_direction=field_dir)


    # --- Visualization ---
    fig, ax = plt.subplots(figsize=(6, 6))
    for line, depth, trunk_rad in line_list:
        x, y = line.xy
        ax.plot(x, y, color=get_color(depth, iterations), linewidth=get_line_width(depth, initial_width, iterations), solid_capstyle='round')  # plot branch with depth-based color and width

    ax.set_aspect('equal')
    ax.axis('off')


    # --- Save figure ---
    plt.savefig("images/fractal_experiment4.png", dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()

    print("Fractal saved!")