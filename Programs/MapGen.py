import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import pandas as pd
import geopandas as gpd
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
import googlemaps
import re

# Establishing Directories
path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
input_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot SPI w Drgt Stats CSV"

# GeoLocation CSV
geoloc = pd.read_csv(r"C:\Users\thoma\Documents\GitHub\Drought-Research\output.csv")

## SPI Map Generation Components ##
# Creates Map-Ready SPI Data
def create_spi_dataframe(input_dir, spi_time, month_key):
    """
    Creates a DataFrame of SPI values for month_key from CSV files.

    Args:
        input_dir: The directory containing the CSV files.

    Returns:
        A Pandas DataFrame with columns for location, year, month, and SPI value.
    """
    spi_row = 'none'

    if spi_time == '01':
        spi_row = '1'
    elif spi_time == '03':
        spi_row = '2'
    elif spi_time == '06':
        spi_row = '3'
    elif spi_time == '12':
        spi_row = '4'

    spi_data = []
    for filename in os.listdir(input_dir):
        if filename.endswith("SPI_M_01_03_06_12.csv"):
            file_path = os.path.join(input_dir, filename)

            # Extract location from filename (adjust as needed)
            location = filename.split("_")[0]  # Assuming location is in the first part of the filename

            # Read CSV data
            df = pd.read_csv(file_path)
           
            # Filter for January 2000 data
            data = df[(df['0'] == month_key) & (df[spi_row].notnull())]

            # Extract SPI value
            spi_value = data[spi_row].iloc[0]

            # Append data to list
            spi_data.append({'location': location, 'spi': spi_value})

    # Create DataFrame
    spi_df = pd.DataFrame(spi_data)

    return spi_df

def spi_map_plot(month, spi_time, map_type, display_plot, filename):
    # Replace forward slashes with hyphens in the month
    month_formatted = re.sub('/', '-', month)
    # Load shapefile
    directory_path = rf"C:\Users\thoma\Documents\GitHub\Drought-Research\Maps\SPI Maps - V1\Categorical\\{spi_time}M"
    shapefile_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\MO_County_Boundaries.shp"
    counties = gpd.read_file(shapefile_path)
    counties_crs = counties.to_crs("EPSG:4326")
    spi_df = create_spi_dataframe(input_dir, spi_time, month)
    geoloc_call = pd.concat([spi_df, geoloc['latitude'], geoloc['longitude']], axis=1, join='outer')
    geoloc_call['county_name'] = spi_df['location'].apply(lambda x: re.sub(r' County$', '', x.split(',')[1]).strip())
    # Extract latitude and longitude from the latlon column
    geoloc_gdf = gpd.GeoDataFrame(geoloc_call, geometry=gpd.points_from_xy(geoloc_call['longitude'], geoloc_call['latitude']))

    # Create figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the map
    counties_crs.plot(ax=ax, color='lightgray', edgecolor='black')
    
    # Conditional for map type
    if map_type == "categorical":
        # Categorical Color Mapping
        ranges = [(-np.inf, -2), (-1.99, -1.6), (-1.59, -1.3), (-1.29, -0.8), (-0.79, -0.5), (-0.49, 0.49), (0.5, 0.79), (0.8, 1.29), (1.3, 1.59), (1.6, 1.99), (2, np.inf)]
        hex_codes = ['#730000', '#E60000', '#E69800', '#FED37F', '#FEFE00', '#FFFFFF', '#AAF596', '#4CE600', '#38A800', '#145A00', '#002673']
        cmap = mcolors.ListedColormap(hex_codes, N=len(ranges))
        geoloc_gdf.plot(ax=ax, column='spi', marker='o', cmap=cmap, vmin=-2, vmax=2, markersize=75, edgecolor='black', linewidth=1)
        legend_elements = [Patch(edgecolor='black', label='D4', facecolor='#730000'), 
                           Patch(edgecolor='black', label='D3', facecolor='#E60000'), 
                           Patch(edgecolor='black', label='D2', facecolor='#E69800'), 
                           Patch(edgecolor='black', label='D1', facecolor='#FED37F'), 
                           Patch(edgecolor='black', label='D0', facecolor='#FEFE00'), 
                           Patch(edgecolor='black', label='N', facecolor='#FFFFFF'), 
                           Patch(edgecolor='black', label='W0', facecolor='#AAF596'), 
                           Patch(edgecolor='black', label='W1', facecolor='#4CE600'), 
                           Patch(edgecolor='black', label='W2', facecolor='#38A800'), 
                           Patch(edgecolor='black', label='W3', facecolor='#145A00'), 
                           Patch(edgecolor='black', label='W4', facecolor='#002673')]
        ax.legend(handles=legend_elements, bbox_to_anchor=(1, 1), loc='upper left')


    elif map_type == "graduated":
        # Graduated Color Mapping
        geoloc_gdf.plot(ax=ax, column='spi', cmap='BrBG', vmin=-2, vmax=2, legend=True, markersize=75, edgecolor='black', linewidth=1)

    # Add custom legend labels
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f'SPI Values in Missouri (Month: {month}, SPI Time: {spi_time})', fontsize= 11)

    # Create the filename
    filename = os.path.join(directory_path, f"spi_map_{month_formatted}_{spi_time}.jpg")

    if display_plot == True:
        plt.show()
    elif filename != None:  # Save only if a filename is provided
        plt.savefig(filename)
        plt.close()  # Close the plot to free resources
    else: #If no filename is provided, don't save the plot
        pass

def create_gui():
    window = tk.Tk()
    window.title("MapGen")

    # Labels
    label_title = tk.Label(window, text="MapGen")
    label_disclaimer = tk.Label(window, text="This program is strictly for use with Missouri Climate Center products and research.")
    label_product = tk.Label(window, text="Select a product:")
    label_timescale = tk.Label(window, text="Select a timescale:")
    label_axis_title_font = tk.Label(window, text="Axis Title Font Size:")
    label_title_font = tk.Label(window, text="Title Font Size:")
    label_axis_tick_font = tk.Label(window, text="Axis Tick Font Size:")

    # Comboboxes
    product_options = ["Graduated SPI", "Categorical SPI", "Raw Frequency", "Cumulative Frequency",
                        "Onset Seasonality", "Relief Seasonality", "Average Duration", "Cumulative Duration",
                        "Longest Duration", "Shortest Duration"]
    product_var = tk.StringVar(window)
    product_var.set(product_options[0])
    product_dropdown = tk.OptionMenu(window, product_var, *product_options)

    timescale_options = ["01M", "03M", "06M", "12M"]
    timescale_var = tk.StringVar(window)
    timescale_var.set(timescale_options[0])
    timescale_dropdown = tk.OptionMenu(window, timescale_var, *timescale_options)

    # Entry fields
    entry_axis_title_font = tk.Entry(window)
    entry_axis_title_font.insert(0, "12")
    entry_title_font = tk.Entry(window)
    entry_title_font.insert(0, "16")
    entry_axis_tick_font = tk.Entry(window)
    entry_axis_tick_font.insert(0, "10")

    # Checkbox and custom title elements
    custom_title_var = tk.BooleanVar()
    checkbox_custom_title = tk.Checkbutton(window, text="Custom Title", variable=custom_title_var)
    label_custom_title_text = tk.Label(window, text="Custom Title:", state=tk.DISABLED)
    entry_custom_title = tk.Entry(window, state=tk.DISABLED)

    # Button
    button_ok = tk.Button(window, text="Ok", command=lambda: print(f"Selected product: {product_var.get()}, Timescale: {timescale_var.get()}, Axis Title Font: {entry_axis_title_font.get()}, Title Font: {entry_title_font.get()}, Axis Tick Font: {entry_axis_tick_font.get()}, Custom Title: {entry_custom_title.get() if custom_title_var.get() else None}, Show Plot: {show_plot_var.get()}"))    
    button_cancel = tk.Button(window, text="Cancel", command=window.quit)

    # Checkbox for showing or saving plot
    show_plot_var = tk.BooleanVar()
    show_plot_checkbox = tk.Checkbutton(window, text="Show Plot", variable=show_plot_var)
    label_show_plot_text = tk.Label(window, text="SPI Key:", state=tk.DISABLED)
    entry_spi_key = tk.Entry(window, state=tk.DISABLED)

    # Grid layout
    label_title.grid(row=0, columnspan=2)
    label_disclaimer.grid(row=1, columnspan=2)
    label_product.grid(row=2, column=0)
    product_dropdown.grid(row=2, column=1)
    label_timescale.grid(row=3, column=0)
    timescale_dropdown.grid(row=3, column=1)
    label_axis_title_font.grid(row=4, column=0)
    entry_axis_title_font.grid(row=4, column=1)
    label_title_font.grid(row=5, column=0)
    entry_title_font.grid(row=5, column=1)
    label_axis_tick_font.grid(row=6, column=0)
    entry_axis_tick_font.grid(row=6, column=1)
    checkbox_custom_title.grid(row=7, columnspan=2)
    label_custom_title_text.grid(row=8, column=0)
    entry_custom_title.grid(row=8, column=1)
    checkbox_custom_title.grid(row=7, columnspan=2)
    show_plot_checkbox.grid(row=9, columnspan=2)
    label_show_plot_text.grid(row=10, column=0)
    entry_spi_key.grid(row=10, column=1)
    button_ok.grid(row=11, column=0)
    button_cancel.grid(row=11, column=1)

    def toggle_custom_title():
        label_custom_title_text.config(state=tk.NORMAL if custom_title_var.get() else tk.DISABLED)
        entry_custom_title.config(state=tk.NORMAL if custom_title_var.get() else tk.DISABLED)

    checkbox_custom_title.config(command=toggle_custom_title)


    def toggle_show_plot():
        label_show_plot_text.config(state=tk.NORMAL if show_plot_var.get() else tk.DISABLED)
        entry_spi_key.config(state=tk.NORMAL if show_plot_var.get() else tk.DISABLED)

    show_plot_checkbox.config(command=toggle_show_plot)


    window.mainloop()

#create_gui()


