# Import necessary libraries
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from siphon.catalog import TDSCatalog
from metpy.units import units
from datetime import datetime, timedelta, UTC
import xarray as xr
import os
import tempfile
import shutil

def plot_interactive_nam_forecast(plot_params):
    """
    Fetches the entire latest NAM 12km model run, generates a plot for the selected variable(s)
    for each forecast hour, and displays them in an interactive viewer with a slider.
    
    Args:
        plot_params (dict): A dictionary containing parameters for the plot.
    """
    # Create a temporary directory to store the forecast images
    img_dir = tempfile.mkdtemp()
    print(f"Image directory: {img_dir}")
    
    try:
        # --- 1. Access the Data ---
        catalog_url = 'https://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/CONUS_12km/latest.xml'
        cat = TDSCatalog(catalog_url)
        dataset = cat.datasets[0]
        print(f"Using dataset: {dataset.name}")

        ncss = dataset.subset()
        query = ncss.query()

        # --- 2. Build the Data Query for the full run ---
        query.lonlat_box(**plot_params['extent'])
        query.all_times() # Request all available forecast times
        # Add vertical level if specified (for reflectivity)
        if 'vertical_level' in plot_params:
            query.vertical_level(plot_params['vertical_level'])
        # Unpack the list of variables into individual arguments
        query.variables(*plot_params['variables']) 
        query.accept('netcdf4')

        # --- 3. Request and Parse the Data ---
        data = ncss.get_data(query)
        
        image_files = []
        with xr.open_dataset(xr.backends.NetCDF4DataStore(data)) as ds_raw:
            ds = ds_raw.metpy.parse_cf()
            
            # --- 4. Loop Through Time Steps and Generate Images ---
            for i, time in enumerate(ds.time.values):
                # Create Plot for this time step
                fig = plt.figure(figsize=(12, 10))
                map_proj = ccrs.LambertConformal(central_longitude=-92.5, central_latitude=38.5)
                ax = fig.add_subplot(1, 1, 1, projection=map_proj)
                ax.set_extent(list(plot_params['extent'].values()), crs=ccrs.PlateCarree())

                ax.add_feature(cfeature.STATES.with_scale('50m'), linestyle='-', edgecolor='black', zorder=2)
                ax.add_feature(cfeature.BORDERS.with_scale('50m'), linestyle=':', edgecolor='black', zorder=2)

                # --- Plotting Logic ---
                if plot_params['plot_type'] == 'sfc_analysis':
                    # --- Surface Analysis Plot (MSLP + Reflectivity) ---
                    mslp_var = ds[plot_params['variables'][0]].sel(time=time).squeeze()
                    reflectivity_var = ds[plot_params['variables'][1]].sel(time=time).squeeze()
                    
                    data_crs = mslp_var.metpy.cartopy_crs
                    x = mslp_var.x.values
                    y = mslp_var.y.values
                    
                    mslp_hpa = mslp_var.values / 100 # Convert Pa to hPa
                    reflectivity_data = reflectivity_var.values

                    # Plot Reflectivity (filled contour)
                    reflectivity_levels = plot_params['reflectivity_levels']
                    contour_fill = ax.contourf(x, y, reflectivity_data, levels=reflectivity_levels, cmap=plot_params['cmap'], transform=data_crs, extend='max')
                    cbar = fig.colorbar(contour_fill, orientation='vertical', pad=0.02, aspect=25)
                    cbar.set_label(plot_params['cbar_label'])

                    # Plot MSLP (contour lines)
                    mslp_levels = plot_params['mslp_levels']
                    mslp_contours = ax.contour(x, y, mslp_hpa, levels=mslp_levels, colors='black', linewidths=1.0, transform=data_crs)
                    ax.clabel(mslp_contours, inline=True, fontsize=10, fmt='%d')

                else:
                    # --- Single Variable Plot (Temp, Dew Point, or STP) ---
                    data_var = ds[plot_params['variables'][0]].sel(time=time).squeeze()
                    data_crs = data_var.metpy.cartopy_crs
                    x = data_var.x.values
                    y = data_var.y.values
                    
                    # Handle unit conversions if applicable
                    if 'units' in plot_params:
                        data_kelvin = data_var.values * units.kelvin
                        plot_data = data_kelvin.to(plot_params['units']).magnitude
                    else: # For unitless parameters like STP
                        plot_data = data_var.values

                    levels = plot_params['levels']
                    contour_fill = ax.contourf(x, y, plot_data, levels=levels, cmap=plot_params['cmap'], transform=data_crs, extend='both')
                    contour_lines = ax.contour(x, y, plot_data, levels=levels, colors='black', linewidths=0.5, transform=data_crs)
                    ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%.1f')
                    
                    cbar = fig.colorbar(contour_fill, orientation='vertical', pad=0.02, aspect=25)
                    cbar.set_label(plot_params['cbar_label'])
                
                # --- Common Plot Elements ---
                valid_time = pd.to_datetime(str(time))
                forecast_hour = (valid_time - pd.to_datetime(str(ds.time.values[0]))).total_seconds() / 3600

                ax.set_title(
                    f"NAM Forecast Hour: +{int(forecast_hour):02d} | {plot_params['plot_title']}\n"
                    f"Valid: {valid_time.strftime('%Y-%m-%d %H:%M')} UTC",
                    fontsize=14
                )
                
                filepath = os.path.join(img_dir, f'forecast_{i:02d}.png')
                plt.savefig(filepath)
                plt.close(fig)
                image_files.append(filepath)
                print(f"Saved {filepath}")

        # --- 5. Create Interactive Viewer ---
        if not image_files:
            print("No images were generated.")
            return

        fig, ax = plt.subplots()
        plt.subplots_adjust(bottom=0.25)
        
        img_data = plt.imread(image_files[0])
        im = ax.imshow(img_data)
        ax.axis('off')

        ax_slider = plt.axes([0.25, 0.1, 0.65, 0.03])
        slider = Slider(
            ax=ax_slider,
            label='Forecast Hour',
            valmin=0,
            valmax=len(image_files) - 1,
            valinit=0,
            valstep=1
        )

        def update(val):
            frame_num = int(slider.val)
            img_data = plt.imread(image_files[frame_num])
            im.set_data(img_data)
            fig.canvas.draw_idle()

        slider.on_changed(update)
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(img_dir):
            print(f"Cleaning up directory: {img_dir}")
            shutil.rmtree(img_dir)

if __name__ == '__main__':
    try:
        import pandas as pd
    except ImportError:
        print("Pandas is not installed. Please install it using: pip install pandas")
        exit()
        
    # --- User Selection ---
    # Define parameters for each plot type
    TEMP_PARAMS = {
        'plot_type': 'single_var',
        'variables': ['Temperature_height_above_ground'],
        'plot_title': '2m Temperature (°F)',
        'cbar_label': 'Temperature (°F)',
        'levels': np.arange(32, 101, 2),
        'cmap': 'jet',
        'extent': {'west': -96, 'east': -89, 'south': 36, 'north': 41},
        'units': 'degF'
    }
    
    DEW_PARAMS = {
        'plot_type': 'single_var',
        'variables': ['Dewpoint_temperature_height_above_ground'],
        'plot_title': '2m Dew Point (°F)',
        'cbar_label': 'Dew Point (°F)',
        'levels': np.arange(0, 81, 2),
        'cmap': 'BrBG',
        'extent': {'west': -96, 'east': -89, 'south': 36, 'north': 41},
        'units': 'degF'
    }

    SFC_PARAMS = {
        'plot_type': 'sfc_analysis',
        'variables': ['MSLP_Eta_model_reduction_msl', 'Reflectivity_height_above_ground'],
        'plot_title': 'Midwest Surface Analysis (MSLP & 1km Reflectivity)',
        'cbar_label': 'Reflectivity (dBZ)',
        'reflectivity_levels': np.arange(5, 80, 5),
        'mslp_levels': np.arange(960, 1051, 4),
        'cmap': 'gist_ncar',
        'extent': {'west': -100, 'east': -82, 'south': 36, 'north': 48},
        'vertical_level': 1000
    }

    STP_PARAMS = {
        'plot_type': 'single_var',
        'variables': ['Significant_Tornado_parameter_surface'],
        'plot_title': 'Significant Tornado Parameter (STP)',
        'cbar_label': 'STP (unitless)',
        'levels': [0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        'cmap': 'plasma',
        'extent': {'west': -96, 'east': -89, 'south': 36, 'north': 41}
    }
    
    choice = ''
    while choice not in ['temp', 'dew', 'sfc', 'stp']:
        choice = input("Select plot type: 'temp', 'dew', 'sfc', or 'stp': ").lower()

    if choice == 'temp':
        plot_interactive_nam_forecast(TEMP_PARAMS)
    elif choice == 'dew':
        plot_interactive_nam_forecast(DEW_PARAMS)
    elif choice == 'sfc':
        plot_interactive_nam_forecast(SFC_PARAMS)
    else:
        plot_interactive_nam_forecast(STP_PARAMS)