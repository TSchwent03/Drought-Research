import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import contextily as ctx  # Optional for basemap
import geopandas as gpd
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable

path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"

# Load the shapefile with the specified CRS (if known)
df = gpd.read_file(path, crs="EPSG:4326")  # Replace with the correct CRS

# If CRS is not defined in the shapefile, set it manually
if df.crs is None:
    df = df.set_crs("EPSG:4326")

# Plot the Missouri counties with hidden axes
fig, ax = plt.subplots(figsize=(8, 6))  # Adjust figure size as needed
df.plot(ax=ax, color='white', edgecolor='black', linewidth=1)
plt.title('Map of Missouri Counties')

# Hide x and y axes
ax.axis('off')  # This hides both x and y axes

plt.show()