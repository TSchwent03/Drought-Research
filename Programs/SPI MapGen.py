import numpy as np 
import matplotlib.pyplot as plt 
import pandas as pd 
import contextily as ctx 
import geopandas as gpd 
import os 
from mpl_toolkits.axes_grid1 import make_axes_locatable

path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\tl_2023_us_state.shp"

# Load the shapefile with the specified CRS (if known)
df = gpd.read_file(path, crs="EPSG:4326")  # Replace with the correct CRS

# If CRS is not defined in the shapefile, set it manually
if df.crs is None:
    df = df.set_crs("EPSG:4326")

# Check the CRS
print(df.crs)
print(df.columns)

# Plot the entire shapefile
df.plot(color='white', edgecolor='black')
plt.title('Map of the United States')
plt.show()