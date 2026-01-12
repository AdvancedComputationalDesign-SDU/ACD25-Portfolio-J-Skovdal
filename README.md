# Jakob Skovdal Rasmussen — ACD-E25 Portfolio

## Overview
This portfolio documents four computational design studies developed for *Advanced Computational Design*. Across the series, I investigate procedural control simulation through NumPy array programming, recursive algorithms, and agent-based modeling, iterating through prototypes, parameter sweeps, and visual evaluation.


## Assignments

### A1: NumPy Array Manipulation for 2D Pattern Generation
In A1, I implemented a 2D Perlin Noise field generator to explore procedural patterning with NumPy. I constructed a grid of gradient vectors, blending their influence using ``fade(t)`` and ``lerp(a, b, t)`` functions to create a seamless continuous pattern. The system expands this 2D scalar data into a 3D RGB array using ``np.stack()``, where I applied channel-specific mathematical transformations (sine, linear, and inverse mappings) to visualize the noise intensity as a complex colorized field.

### A2: Exploring Fractals through Recursive Geometric Patterns
In A2, I build a recursive geometric fractal generator using Matplotlib and Shapely to simulate organic, tree-like structures. The core logic relies on a recursive function, generate_fractal, which applies scaling ratios and branching angles ($\theta_{new} = \theta_{old} \pm \text{angle}$) to achieve self-similarity. To avoid rigid symmetry, I introduced stochastic branch lengths and two geometric forces: a Point Attractor that subtly bends branches toward a target coordinate ($x, y$), and a Uniform Directional Field that biases growth orientation. The final visualization maps line width and color (using the viridis colormap) to the recursion depth, visually distinguishing the hierarchical structure from trunk to tip.

### A3: Parametric Structural Canopy
In A3, I designed a canopy system driven by a Perlin Noise heightmap and implemented in Grasshopper/GhPython. The project leveraged NumPy to generate and deform a planar point grid according to the heightmap, which was then used to construct a continuous NURBS surface. This deformed surface was tessellated into planar triangular panels. Crucially, the structural support system was generated using a recursive branching algorithm that starts at ground-level anchors and employs ray-casting to ensure each support member accurately truncates upon intersecting the non-planar canopy surface.

### A4: Agent-Based Modeling for Surface Panelization
In A4, I implemented an Agent-Based Model (ABM) in GhPython to rationalize the surface geometry from A3 into a panelized system. Agents' movement is fundamentally driven by surface geometry: they use the Principal Curvature Direction for Alignment, ensuring trajectories follow the surface's flow lines. They also apply Resistance proportional to Slope Magnitude, causing them to slow down in steep areas and thereby increasing point density for smaller, more appropriate panels in those zones. A final Separation force manages distribution, and the resulting collected agent paths define the final panelization geometry, where orientation and density are emergent properties of the localized behaviors.


## Highlights
- **Key Focus:** My core interest lies in applying computational systems to directly inform physical and structural solutions in architecture.
- **Computational Challenge:** Managing Simulation Stability in A4. Overcoming the Python ``RecursionError`` in the continuous Grasshopper simulation loop by manually increasing the recursion limit (``sys.setrecursionlimit(2000)``) to maintain state persistence across steps.
- **Next step:** Integrating the depth-based thickness tapering into the recursive support generation (A3) that was initially simplified, allowing the structural members to thin out logically towards the terminal branches.

## Contact
- Email: jakra22@student.sdu.dk