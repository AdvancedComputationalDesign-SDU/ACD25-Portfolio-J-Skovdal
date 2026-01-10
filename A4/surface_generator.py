import numpy as np
import rhinoscriptsyntax as rs
import random

# -------------------------------
# GH PYTHON INPUTS
# -------------------------------
# 1. Surface Dimensions
# sizeX: float (Size in X direction)
# sizeY: float (Size in Y direction)
#
# 2. Resolution
# divU: int (Number of divisions in U)
# divV: int (Number of divisions in V)
#
# 3. Heightmap Parameters
# amplitude: float (Heightmap scale factor)
# scale: float (Noise frequency/scale)
# seed: int (Random seed for reproducibility)
# -------------------------------


# -------------------------------
# Helpers
# -------------------------------

def seed_everything(seed):  # sets random seeds for reproducibility
    if seed is None:
        return
    try:
        random.seed(seed)
        np.random.seed(seed)
    except Exception as e:
        print(f"Failed to set random seeds: {e}")


# -------------------------------
# Perlin Noise Helpers
# -------------------------------

def fade(t):
    return 6 * t**5 - 15 * t**4 + 10 * t**3  # fade function smooths the interpolation

def lerp(a, b, t):
    return a + t * (b - a)  # linear interpolation between a and b

DIRECTIONS = np.array([[0, 1], [0, -1], [1, 0], [-1, 0]])  # define gradient directions (up, down, left, right) once

# -------------------------------
# 1) Heightmap Generation
# -------------------------------

def generate_heightmap(U, V, amplitude=1.0, scale=10.0, seed=None):  # computes a scalar field H over U,V using Perlin Noise
    
    if seed is not None:
        np.random.seed(seed)
        
    H = np.zeros((divU, divV))
    
    # --- Prepare Gradient Grid ---
    # Determine grid size based on scale
    grid_height = int(divU // scale) + 2
    grid_width = int(divV // scale) + 2
    
    # Generate random gradients once for the whole grid
    index = np.random.randint(0, 4, size=(grid_height, grid_width))
    gradients = DIRECTIONS[index]
    
    # --- Compute Noise ---
    for i in range(divU):  # vertical position (row)
        for j in range(divV):  # horizontal position (column)

            # Map the (i, j) index to a coordinate between 0 and 1, then scale it
            scaled_i = i / divU * scale
            scaled_j = j / divV * scale

            # Determine which cell the point belongs to (x0, y0, x1, y1)
            x0 = int(scaled_j)  # left grid corner (x index)
            y0 = int(scaled_i)  # top grid corner (y index)
            x1 = x0 + 1         # right grid corner
            y1 = y0 + 1         # bottom grid corner
            
            # Local position inside the cell (0 to 1 range)
            sx = scaled_j - x0  
            sy = scaled_i - y0  

            # Apply fade to smooth the interpolation
            u = fade(sx)
            v = fade(sy)

            # Distance vectors from point to each corner 
            dx0 = sx       
            dy0 = sy       
            dx1 = sx - 1   
            dy1 = sy - 1   

            # Dot products between distance and gradient vectors
            n00 = np.dot(gradients[y0, x0], [dx0, dy0])  # top-left corner
            n10 = np.dot(gradients[y0, x1], [dx1, dy0])  # top-right corner
            n01 = np.dot(gradients[y1, x0], [dx0, dy1])  # bottom-left corner
            n11 = np.dot(gradients[y1, x1], [dx1, dy1])  # bottom-right corner

            # Interpolate along x-axis
            nx0 = lerp(n00, n10, u)  
            nx1 = lerp(n01, n11, u)  

            H[i, j] = lerp(nx0, nx1, v)  # interpolate along y-axis

    # Normalization and Amplitude scaling
    # Recenter to -1 to 1 range, then apply amplitude
    H_normalized = (H - H.min()) / (H.max() - H.min())
    H_scaled = (H_normalized * 2 - 1) * amplitude
    
    return H_scaled


# -------------------------------
# 2) Base Grid Generation
# -------------------------------

def make_flat_grid(divU, divV, sizeX, sizeY):  # creates a flat 2D list of Rhino Points on the XY plane
    
    x_vals = np.linspace(0.0, sizeX, divU)
    y_vals = np.linspace(0.0, sizeY, divV)
    X, Y = np.meshgrid(x_vals, y_vals, indexing='ij')
    Z = np.zeros(X.shape)
    
    grid = []
    for i in range(divU):
        row = []
        for j in range(divV):
            pt = rs.AddPoint(X[i, j], Y[i, j], Z[i, j])
            row.append(pt)
        grid.append(row)
        
    return grid

# -------------------------------
# 3) Grid Manipulation
# -------------------------------

def manipulate_point_grid(point_grid, heightmap):
    """
    Deforms a point grid based on the provided heightmap.
    Returns a new list of lists containing Rhino Points.
    """
    rows = len(point_grid)
    cols = len(point_grid[0])
    
    new_grid = []
    
    for i in range(rows):
        row_pts = []
        for j in range(cols):
            old_pt = point_grid[i][j]
            h = heightmap[i, j]
            
            # Create new point shifted in Z
            new_pt = rs.PointAdd(old_pt, [0, 0, h])
            row_pts.append(new_pt)
        new_grid.append(row_pts)
        
    return new_grid

# -------------------------------
# 4) Surface Construction
# -------------------------------

def build_surface(point_grid):

    if not point_grid:
        return None
        
    rows = len(point_grid)
    cols = len(point_grid[0])
    
    # Flatten the points in row-major order for rs.AddSrfPtGrid
    flat_points = [p for row in point_grid for p in row]
    
    # Create Surface
    surf = rs.AddSrfPtGrid((rows, cols), flat_points)  # rs.AddSrfPtGrid requires (rows, columns) dimensions
    
    return surf

# -------------------------------
# Pipeline
# -------------------------------

if __name__ == "__main__":
    
    # 1. Seed RNG
    seed_everything(seed)
    
    # 2. Generate Heightmap (Data)
    H = generate_heightmap(divU, divV, amplitude=amplitude, scale=scale)
    
    # 3. Create Base Grid (Geometry)
    flat_grid = make_flat_grid(divU, divV, sizeX, sizeY)
    
    # 4. Apply Heightmap
    deformed_grid = manipulate_point_grid(flat_grid, H)
    
    # 5. Build Final Surface
    surface = build_surface(deformed_grid)
    
    # 6. Outputs
    out_surface = surface