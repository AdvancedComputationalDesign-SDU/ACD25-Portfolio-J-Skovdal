## Assignment 1: NumPy Array Manipulation for 2D Pattern Generatione


import numpy as np
import matplotlib.pyplot as plt


# --- Initializing canvas ---

canvas_height = 500
canvas_width = 500
canvas = np.zeros((canvas_height, canvas_width))

# --- Defining functions ---

def fade(t):  # fade function smooths the interpolation
    return 6*t**5 - 15*t**4 + 10*t**3

def lerp(a, b, t):  # linear interpolation between a and b
    return a + t * (b - a)

def generate_gradients(canvas_height, canvas_width):
    directions = np.array([[0,1], [0,-1], [1,0], [-1,0]])  # possible gradient directions (up, down, left, right)
    index = np.random.randint(0, 4, size=(canvas_height, canvas_width))  # randomly picking one of the 4 directions for each grid point
    gradients = directions[index]  # replacing each random index with its corresponding direction vector
    return gradients


# --- Computing number of grid points---

scale = 20  # Smaller scale = more detailed noise

grid_height = canvas_height // scale + 2  # adding +2 to avoid indexing issues
grid_width = canvas_width // scale + 2


gradients = generate_gradients(grid_height, grid_width)  # creating a grid of random gradient vectors


# --- Generating noise pattern ---

# Loop through each pixel on the canvas // Computing noise for each pixel individually
for i in range(canvas_height):  # vertical position (row)
    for j in range(canvas_width):  # horizontal position (column)

        # Determine which cell each pixel belongs to
        x0 = j // scale  # left grid corner (x index)
        y0 = i // scale  # top grid corner (y index)
        x1 = x0 + 1      # right grid corner
        y1 = y0 + 1      # bottom grid corner

        # Local position inside the cell (0 to 1 range)
        sx = (j % scale) / scale  # how far it is across the cell (x)
        sy = (i % scale) / scale  # how far it is down the cell (y)

        # Apply fade to smooth the interpolation
        u = fade(sx)
        v = fade(sy)

        # Distance vectors from pixel to each corner 
        dx0 = sx       # distance to left corners
        dy0 = sy       # distance to top corners
        dx1 = sx - 1   # distance to right corners
        dy1 = sy - 1   # distance to bottom corners

        # Dot products between distance and gradient vectors
        # the dot product measures how well the pixel aligns with the corner’s gradient direction
        n00 = np.dot(gradients[y0, x0], [dx0, dy0])  # top-left corner
        n10 = np.dot(gradients[y0, x1], [dx1, dy0])  # top-right corner
        n01 = np.dot(gradients[y1, x0], [dx0, dy1])  # bottom-left corner
        n11 = np.dot(gradients[y1, x1], [dx1, dy1])  # bottom-right corner

        # Interpolate along x-axis between corners
        nx0 = lerp(n00, n10, u)  # top edge interpolation
        nx1 = lerp(n01, n11, u)  # bottom edge interpolation

        # Interpolate along y-axis between top and bottom edges
        canvas[i, j] = lerp(nx0, nx1, v)  # this gives the final noise value for each pixel


# --- Normalizing values ---

# The noise can have both negative and positive values.
canvas = (canvas - canvas.min()) / (canvas.max() - canvas.min())  # rescaling to 0–1 range


# --- Display and save image (Greyscale) ---

plt.imshow(canvas, cmap="grey")
plt.axis("off")
plt.savefig('images/perlin_grey.png', bbox_inches='tight', pad_inches=0)
plt.show()


# --- Colorizing greyscale ---

canvas_rgb = np.stack((canvas, canvas, canvas), axis=2) # adds new color channel dimension

canvas_rgb[:, :, 0] = np.sin(canvas * np.pi) * 255  # red channel: strongest in mid-range
canvas_rgb[:, :, 1] = canvas * 255                  # green channel: increases with brightness
canvas_rgb[:, :, 2] = (1 - canvas) * 255            # blue channel: strongest when dark (inverse of brightness)

canvas_rgb = np.clip(canvas_rgb, 0, 255)  # limiting the values in the array to ensure a valid color range (0–255)

plt.imshow(canvas_rgb.astype(np.uint8))
plt.axis("off")
plt.savefig('images/perlin_rgb.png', bbox_inches='tight', pad_inches=0)
plt.show()