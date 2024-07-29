import geopandas as gpd
import matplotlib.pyplot as plt

def plot_missouri_map(shapefile_path):
  """Plots a map of Missouri from the specified shapefile."""

  # Load the US states shapefile
  us_states = gpd.read_file(shapefile_path)

  # Filter for Missouri (assuming 'STUSPS' is the state abbreviation column)
  missouri = us_states[us_states['FIPS'] == 'MO']

  # Plot the Missouri map with white fill and black outline
  missouri.plot(color='white', edgecolor='black', figsize=(8, 6))
  plt.title('Map of Missouri')
  plt.show()

if __name__ == "__main__":
  shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\tl_2023_us_state.shp"
  plot_missouri_map(shapefile_path)
