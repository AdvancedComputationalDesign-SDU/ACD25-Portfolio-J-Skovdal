import numpy as np
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import random


# -------------------------------
# GH PYTHON INPUTS
# -------------------------------
# 1. Reproducibility
# seed: int (Random seed for RNG)
# 
# 2. Canopy Size
# sizeX: float (Canopy size in Y direction)
# sizeY: float (Canopy size in X direction)
# canopy_height: float (Canopy height at lowest point)
#
# 3. Canopy Base / Resolution
# divU: int (Surface U Division count)
# divV: int (Surface V Division count)
# 
# 4. Heightmap Parameters
# amplitude: float (Heightmap scale factor)
# scale: float (Heightmap repetition rate)
#
# 5. Tessellation Type
# use_triangles: bool (if True, uses triangular panels (Design B))
#
# 6. Support Anchor
# user_anchors: list[point] (Optional: User-selected ground anchor points)
#
# 7. Recursive Branching Parameters
# rec_depth: int (Maximum recursion depth for branching)
# br_length: float (Initial length of the root branches)
# len_reduct: float (Length reduction factor for subsequent branches (0-1))
# n_branches: int (Number of children branches per node)
#
# 8. Support Geometry Thickness
# pipe_radius: float (Constant radius for the structural pipe geometry)
# -------------------------------


# -------------------------------
# Helpers
# -------------------------------

def seed_everything(seed):  # sets seeds for reproducibility
    if seed is None:
        return
    try:
        random.seed(seed)
        np.random.seed(seed)
    except Exception as e:
        print(f"Failed to set random seeds: {e}")


def uv_grid(divU, divV):  # creates uniform UV sample grids in [0,1]x[0,1] using NumPy
    u = np.linspace(0.0, 1.0, divU)
    v = np.linspace(0.0, 1.0, divV)
    
    U, V = np.meshgrid(u, v, indexing='ij')  # uses 'ij' indexing for (divU, divV) shape
    
    return U, V


def generate_random_surface_points(surf, count):  # generates 'count' random points on the surface
    if not surf or count <= 0:
        return []

    domainU = rs.SurfaceDomain(surf, 0)
    domainV = rs.SurfaceDomain(surf, 1)
    
    random_points = []
    
    while len(random_points) < count:  # generates random UV coordinates within the domain
        u_rand = random.uniform(domainU[0], domainU[1])
        v_rand = random.uniform(domainV[0], domainV[1])
        
        pt = rs.EvaluateSurface(surf, u_rand, v_rand)
        
        if pt:
            random_points.append(pt)
            
    return random_points


# -------------------------------
# Perlin Noise Helpers
# -------------------------------

def fade(t): 
    return 6*t**5 - 15*t**4 + 10*t**3  # fade function smooths the interpolation

def lerp(a, b, t): 
    return a + t * (b - a)  # linear interpolation between a and b

DIRECTIONS = np.array([[0, 1], [0, -1], [1, 0], [-1, 0]])  # define gradient directions (up, down, left, right) once


# -------------------------------
# 1) Heightmap (Perlin Noise Version)
# -------------------------------

def heightmap_perlin(U, V, amplitude=1.0, scale=10.0, seed=None):  # computes a scalar field H over U,V using Perlin Noise
    
    if seed is not None:
        np.random.seed(seed)
        
    divU, divV = U.shape
    H = np.zeros(U.shape)
    
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
# 2) Source point grid
# -------------------------------

def make_point_grid_xy(divU, divV, origin=(0.0, 0.0, 0.0), size=(10.0, 10.0)):  # creates a simple planar XY grid of points for the canopy base
    
    # Create 1D arrays for X and Y coordinates within the size domain
    x = np.linspace(origin[0], origin[0] + size[0], divU)
    y = np.linspace(origin[1], origin[1] + size[1], divV)
    
    X, Y = np.meshgrid(x, y, indexing='ij')  # creates the coordinate matrices
    
    Z = np.full(X.shape, origin[2])  # Z coordinate is always the origin's Z
    
    # Use list comprehension to create a flat list of Rhino points
    P_grid_flat = [rs.AddPoint(X.flatten()[i], Y.flatten()[i], Z.flatten()[i]) 
                   for i in range(X.size)]
    
    # Reshape the flat list back into a 2D grid structure (list of lists)
    P_grid = [P_grid_flat[i * divV:(i + 1) * divV] for i in range(divU)]
    
    return P_grid


# -------------------------------
# 3) Deform point grid
# -------------------------------

def manipulate_points_z(point_grid, H):  # returns a deformed copy of a planar point_grid by offsetting along +Z

    rows = len(point_grid)
    cols = len(point_grid[0])
    
    P_def = []
    
    # Iterate through the 2D grid structure
    for i in range(rows):
        row = []
        for j in range(cols):
            # reads point p and height h
            p = point_grid[i][j]
            h = H[i, j]
            
            p_def = rs.PointAdd(p, (0, 0, h))  # creates a new point by adding h along the Z axis (0,0,h)
            row.append(p_def)
        P_def.append(row)
        
    return P_def


# -------------------------------
# 4) Construct canopy surface from points
# -------------------------------

def surface_from_point_grid(point_grid, canopy_height): 
    
    if not point_grid:
        return None
        
    rows = len(point_grid)
    cols = len(point_grid[0])
    
    # Flatten the points in row-major order for rs.AddSrfPtGrid
    flat_points = [p for row in point_grid for p in row]
    
    surf = rs.AddSrfPtGrid((rows, cols), flat_points)  # rs.AddSrfPtGrid requires (rows, columns) dimensions

    if surf:
        
        bbox = rs.BoundingBox(surf)  # gets the lowest point (Min Z)
        if bbox:
            min_z = bbox[0].Z 
            
            translation_distance = canopy_height - min_z  # calculates the movement vector
            
            rs.MoveObject(surf, [0, 0, translation_distance])
        
    return surf


# -------------------------------
# 5) Uniform sampling for panelization
# -------------------------------

def sample_surface_uniform(surf, divU, divV):  # samples a grid of 3D points from a surface using U,V domain divisions
    
    U, V = uv_grid(divU, divV)  # U, V grid is normalized [0, 1]
    rows, cols = U.shape
    
    Sgrid = []
    
    # 1. Get the domain of the surface
    domainU = rs.SurfaceDomain(surf, 0)
    domainV = rs.SurfaceDomain(surf, 1)
    
    # 2. Iterate and map the coordinates
    for i in range(rows):
        row = []
        for j in range(cols):
            # maps normalized U[i, j] to the real domain [domainU[0], domainU[1]]
            u_norm = U[i, j]
            v_norm = V[i, j]
            
            u_coord = domainU[0] + u_norm * (domainU[1] - domainU[0])
            v_coord = domainV[0] + v_norm * (domainV[1] - domainV[0])
            
            pt = rs.EvaluateSurface(surf, u_coord, v_coord)
            
            if pt:  # ensure point evaluation succeeded
                row.append(pt)
            else:
                row.append(rs.AddPoint(0,0,0))
                
        Sgrid.append(row)
        
    return Sgrid


# -------------------------------
# 6.1) Tessellate into panels (Quad) (Design A)
# -------------------------------

def tessellate_quads_from_grid(Sgrid):  # generates a list of quadrilateral surfaces from a point grid
    
    if not Sgrid:
        return []

    rows = len(Sgrid)
    cols = len(Sgrid[0])
    panels = []
    
    for i in range(rows - 1):
        for j in range(cols - 1):
            
            # Define the four corner points of the current panel (quad)
            p00 = Sgrid[i][j]       # Top-Left
            p01 = Sgrid[i][j+1]     # Top-Right
            p10 = Sgrid[i+1][j]     # Bottom-Left
            p11 = Sgrid[i+1][j+1]   # Bottom-Right
            
            flat_points = [p00, p01, p10, p11]  # the points is flattened in row-major order: p00, p01, p10, p11
            
            panel_surf = rs.AddSrfPtGrid((2, 2), flat_points)  # uses rs.AddSrfPtGrid to create a 2x2 panel directly from the points
            
            if panel_surf:
                panels.append(panel_surf)
            
    return panels


# -------------------------------
# 6.2) Tessellate into panels (Triangular) (Design B)
# -------------------------------

def tessellate_triangles_from_grid(Sgrid):  # generates a list of triangular surfaces from a point grid
    
    if not Sgrid:
        return []

    rows = len(Sgrid)
    cols = len(Sgrid[0])
    panels = []
    
    for i in range(rows - 1):
        for j in range(cols - 1):
            
            # Define the four corner points of the current cell
            p00 = Sgrid[i][j]       # Top-Left
            p01 = Sgrid[i][j+1]     # Top-Right
            p10 = Sgrid[i+1][j]     # Bottom-Left
            p11 = Sgrid[i+1][j+1]   # Bottom-Right
            
            # Triangle 1 (Bottom-Left split): p00, p10, p11
            tri1_surf = rs.AddSrfPt([p00, p10, p11])  # rs.AddSrfPt creates a surface from 3 or 4 points
            
            # Triangle 2 (Top-Right split): p00, p11, p01
            tri2_surf = rs.AddSrfPt([p00, p11, p01])
            
            if tri1_surf:
                panels.append(tri1_surf)
            if tri2_surf:
                panels.append(tri2_surf)
            
    return panels


# -------------------------------
# 7) Choose support anchors
# -------------------------------

def get_user_or_random_anchors(user_anchors, surf, fallback_count=4):
    """
    If user_anchors are provided, use them. Otherwise, it generates random points 
    on the surface as a fallback.
    """
    
    valid_coords = []
    
    if user_anchors:
        for anchor in user_anchors:
            if anchor is None:
                continue

            # Case 1: Already a valid RhinoScript Point (GUID or tuple)
            if rs.IsPoint(anchor):
                valid_coords.append(anchor)
                
            # Case 2: Rhino.Geometry.Point3d object (Common Grasshopper output)
            elif hasattr(anchor, 'X') and hasattr(anchor, 'Y') and hasattr(anchor, 'Z'):  # extracts coordinates into a tuple (X, Y, Z)
                coords = (anchor.X, anchor.Y, anchor.Z)
                valid_coords.append(coords) 
                
    if not valid_coords:  # fallback generates coordinates, using the helper function
        valid_coords = generate_random_surface_points(surf, fallback_count)
    
    final_anchors = []  # converts all tuples into Rhino Point GUIDs
    
    for pt in valid_coords:
        # determines coordinates regardless of whether pt is a tuple or a Rhino Point3d
        if hasattr(pt, 'X'):
            x = pt.X
            y = pt.Y
        else:
            x = pt[0]
            y = pt[1]
            
        # resets Z coordinate to 0.0
        ground_coords = (x, y, 0.0) 
        
        point_guid = rs.AddPoint(ground_coords) # creates the ground point

        if point_guid:
            final_anchors.append(point_guid)

    return final_anchors


# -------------------------------
# 8) Generate supports
# -------------------------------

def generate_supports(roots, surf, depth=3, length=5.0, length_reduction=0.7, n_children=2, seed=None, pipe_radius=0.1):
    if seed is not None:
        random.seed(seed)

    supports = []

    canopy_brep = rs.coercebrep(surf)
    if not canopy_brep:
        return []

    # Internal recursive function
    def recursive_branch(start_pt, vec_dir, curr_depth, curr_len):
        
        segment_results = [] 
        
        if curr_depth == 0:
            return segment_results

        # 1. Construct the geometry mathematically (Ray Casting)
        vec_dir = rs.VectorUnitize(vec_dir)
        vec_scaled = rs.VectorScale(vec_dir, curr_len)
        
        start_pt_3d = rs.coerce3dpoint(start_pt)
        candidate_end = start_pt_3d + vec_scaled
        
        ray_line = rg.Line(start_pt_3d, candidate_end)
        ray_curve = ray_line.ToNurbsCurve()

        # 2. Intersection Check (RhinoCommon)
        res = rg.Intersect.Intersection.CurveBrep(ray_curve, canopy_brep, 0.001)
        
        hit_points = []
        if res and len(res) > 0:
            hit_points = res[-1]

        hit_roof = False
        final_end_pt = candidate_end

        if hit_points and hit_points.Count > 0:
            hit_roof = True
            closest_dist = float('inf')
            real_hit = None
            
            for pt in hit_points:
                dist = start_pt_3d.DistanceTo(pt)
                if dist < closest_dist:
                    closest_dist = dist
                    real_hit = pt
            
            if real_hit:
                final_end_pt = real_hit

        # 3. Geometry Creation (Constant Thickness)
        segment_length = start_pt_3d.DistanceTo(final_end_pt)
        MIN_LENGTH_THRESHOLD = 0.001 

        if segment_length > MIN_LENGTH_THRESHOLD:  # checks if segment is long enough to draw a valid pipe
            
            segment_guid = rs.AddLine(start_pt_3d, final_end_pt)
            
            # constant Radii
            r_start = pipe_radius
            r_end   = pipe_radius

            # add Pipe (creates a brep)
            domain = rs.CurveDomain(segment_guid)
            pipes = rs.AddPipe(segment_guid, [domain[0], domain[1]], [r_start, r_end], cap=2) 
            
            if pipes:
                segment_results.extend(pipes) 
                rs.DeleteObject(segment_guid)
            else:
                segment_results.append(segment_guid)  # fall back to line if pipe fails

        # 4. Recursive Step
        if not hit_roof and curr_depth > 1:
            new_len = curr_len * length_reduction
            
            for _ in range(n_children):
                jitter = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 0.5]
                new_dir = rs.VectorAdd(vec_dir, jitter)
                
                child_guids = recursive_branch(final_end_pt, new_dir, curr_depth - 1, new_len)  # continues from the end of the current segment
                segment_results.extend(child_guids)

        return segment_results

    # --- Start Recursion ---
    for root in roots:
        root_guids = recursive_branch(root, [0,0,1], depth, length)  # initial vector is up (0,0,1)
        supports.extend(root_guids)

    return supports


# -------------------------------
# Pipeline
# -------------------------------

# 1. Seed RNG
seed_everything(seed)

# 2. Build UV grids
U, V = uv_grid(divU, divV)

# 3. Heightmap
H = heightmap_perlin(U, V, amplitude=amplitude, scale=scale, seed=seed)

# 4. Source point grid (choose planar base)
P_src = make_point_grid_xy(divU, divV, origin=(0,0,0), size=(sizeX,sizeY))

# 5. Deform points (choose planar deformation)
P_def = manipulate_points_z(P_src, H)

# 6. Construct canopy surface
surf = surface_from_point_grid(P_def, canopy_height)

# 7. Uniform sampling for panelization
Sgrid = sample_surface_uniform(surf, divU, divV)

# 8. Tessellate into panels
if use_triangles:
    # Design B: Triangular panels
    panels = tessellate_triangles_from_grid(Sgrid)
else:
    # Design A: Quadrilateral panels
    panels = tessellate_quads_from_grid(Sgrid)

# 9. Choose support anchors
# if user_anchors is empty, the function defaults to 4 random points on the surface
roots = get_user_or_random_anchors(user_anchors, surf, fallback_count=4)

# 10. Generate supports
supports = generate_supports( 
    roots=roots,
    surf=surf,
    depth=rec_depth,
    length=br_length,
    length_reduction=len_reduct,
    n_children=n_branches,
    seed=seed,
    pipe_radius=pipe_radius
)

# 11. Set GhPython outputs
out_surface      = surf
out_tessellation = panels
out_supports     = supports