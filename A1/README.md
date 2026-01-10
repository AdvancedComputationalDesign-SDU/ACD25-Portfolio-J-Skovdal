---
layout: default
title: Project Documentation
parent: "A1: NumPy Array Manipulation for 2D Pattern Generation"
nav_order: 2
nav_exclude: false
search_exclude: false
---

# Assignment 1: NumPy Array Manipulation for 2D Pattern Generation

[View on GitHub]({{ site.github.repository_url }})

## Table of Contents

- [Pseudo-Code](#pseudo-code)
- [Technical Explanation](#technical-explanation)
- [Results](#results)
- [References](#references)

---

## Pseudo-Code

1. **Initialize Variables**
   - Set canvas height and width.
   - Choose a scale value to control the detail level of the pattern.

2. **Define Helper Functions**
   - **Fade function**: smooths transitions between values for continuity.
        - `fade`: Applies a smoothing curve to the relative distance coordinates to ease the transition near grid edges.
   - **Interpolation function**: blends between two values.
        - `lerp`: detailed weighted averaging:
            - Blend the top two corners together based on the horizontal position.
            - Blend the bottom two corners together based on the horizontal position.
            - Blend those two results together based on the vertical position.
   - **Gradient generator**: assigns a random direction to each grid point; gradients influence pixel values to shape the noise.

3. **Prepare the Grid**
   - Divide the canvas into cells based on the chosen scale.
   - Assign one gradient vector to each corner of the cells.

4. **Generate Noise Pattern**
   - For each pixel in the canvas:
      - Determine which cell the pixel belongs to.
      - Calculate relative position of the pixel inside the cell (0 to 1).
      - Compute how much each corner gradient affects the pixel.
      - Interpolate the corner contributions to get a single value for the pixel.

5. **Normalize Values**
   - Rescale all pixel values to a consistent range (0 to 1).

6. **Visualize and Save Grayscale Image**
   - Use Matplotlib to display the pattern as a grayscale image.
   - Save the image to the `images/` folder.

7. **Add Color (RGB Transformation)**
   - Expand the 2D grayscale array into three channels (Red, Green, Blue).
   - Map grayscale intensity to colors:
      - Dark areas → blue.
      - Mid-tones → red.
      - Bright areas → green.

8. **Display and Save Colorized Image**
   - Use Matplotlib to display the colorized image.
   - Save the image to the `images/` folder.

---

## Technical Explanation

In this assignment, I began by initializing a blank canvas using `np.zeros()`, creating a 2D array to represent the pixel grid of the image. The canvas dimensions were defined by height and width parameters, determining the resolution of the generated pattern.

To generate the Perlin noise, I divided the canvas into a grid and assigned a random gradient vector to each grid point using `np.random.randint()` combined with predefined vector direction using `np.array()`. Each pixel’s noise value was computed based on its distance from surrounding grid corners and the dot products between distance and gradient vectors. The `fade()` function $(6t^5 - 15t^4 + 10t^3)$ was applied to smooth the interpolation, and `lerp()` (linear interpolation) $(a + t * (b - a))$ was used to blend values between the corners, ensuring smooth transitions across the pattern.

The resulting noise values, which ranged between negative and positive numbers, were normalized to a 0–1 scale. This normalization step was essential to map the noise data correctly to grayscale intensity values.

To create a colorized version, I used `np.stack()` to extend the 2D array into a 3D RGB array. Each color channel was then manipulated individually, assigning different  relationships to create some variation: the red channel was based on a sine transformation done by `np.sin`, the green channel increased with brightness, and the blue channel decreased with it. This introduced a color transition, corresponding to the noise intensity.

The final image was clipped to the valid color range *(0-255)* using `np.clip()`, visualized with `plt.imshow()` and saved using `plt.savefig()`, giving both grayscale and colorized visual representations of the generated Perlin noise pattern.

---

## Results

Shown here is the result image, displaying both the grayscale version and the version where a third array has been added as an RGB channel. 

![Perlin Noise in greyscale](images/perlin_grey.png) 
*Figure 1: The normalized scalar noise field rendered in grayscale.*

![Perlin Noise with added RGB](images/perlin_rgb.png)
*Figure 2: The final output where scalar values are mapped to RGB channels using sine and linear functions.*

---

## References

- Perlin Noise Overview [Perlin noise](https://en.wikipedia.org/wiki/Perlin_noise)
- Perlin Noise Algorith Explanation [Perlin Noise: A Procedural Generation Algorithm](https://rtouti.github.io/graphics/perlin-noise-algorithm)
- Perlin Noise Mathematics [Simplex noise demystified](https://www.researchgate.net/publication/216813608_Simplex_noise_demystified)

---