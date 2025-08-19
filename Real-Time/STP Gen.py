# Import necessary libraries
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from siphon.catalog import TDSCatalog
from metpy.units import units
import metpy.calc as mpcalc
from datetime import datetime, timedelta, UTC
import xarray as xr
import os
import tempfile
import shutil

def plot_interactive_forecast(plot_params):
    """
    Fetches the latest NAM 12km model data, calculates a chosen parameter (STP or VTP)
    for each forecast hour, and displays the plots in an interactive viewer with a slider.
    
    Args:
        plot_params (dict): A dictionary containing parameters for the plot.
    """
    # Create a temporary directory to store the forecast images
    img_dir = tempfile.mkdtemp()
    print(f"Image directory: {img_dir}")
    ds_lr_raw = None # Initialize to ensure it exists for the finally block
    
    try:
        # --- 1. Access the Data ---
        catalog_url = 'https://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/CONUS_12km/latest.xml'
        cat = TDSCatalog(catalog_url)
        dataset = cat.datasets[0]
        print(f"Using dataset: {dataset.name}")

        ncss = dataset.subset()

        # --- 2. Build and Execute Separate Data Queries for Each Vertical Level ---
        print("Requesting data from server... This may take multiple requests.")

        # Query 1: Surface and layer variables
        query_sfc = ncss.query()
        query_sfc.lonlat_box(**plot_params['extent'])
        query_sfc.all_times()
        query_sfc.variables(*plot_params['variables']['surface'])
        query_sfc.accept('netcdf4')
        data_sfc = ncss.get_data(query_sfc)

        # Query 2: 10m Above Ground Level variables
        query_10m = ncss.query()
        query_10m.lonlat_box(**plot_params['extent'])
        query_10m.all_times()
        query_10m.variables(*plot_params['variables']['agl_10m'])
        query_10m.vertical_level(10)
        query_10m.accept('netcdf4')
        data_10m = ncss.get_data(query_10m)

        # Query 3: 500mb Isobaric variables for shear
        query_500mb = ncss.query()
        query_500mb.lonlat_box(**plot_params['extent'])
        query_500mb.all_times()
        query_500mb.variables(*plot_params['variables']['isobaric_500mb'])
        query_500mb.vertical_level(50000) # 500 hPa in Pa
        query_500mb.accept('netcdf4')
        data_500mb = ncss.get_data(query_500mb)
        
        # Query 4 (only for VTP): Isobaric levels for lapse rate calculation
        if plot_params['plot_type'] == 'vtp':
            query_lr = ncss.query()
            query_lr.lonlat_box(**plot_params['extent'])
            query_lr.all_times()
            query_lr.variables(*plot_params['variables']['isobaric_lapse_rate'])
            query_lr.vertical_level(97500) # 975 hPa
            query_lr.vertical_level(70000) # 700 hPa
            query_lr.accept('netcdf4')
            data_lr = ncss.get_data(query_lr)

        print("All data received. Processing forecast hours...")
        
        image_files = []
        # --- 3. Open and Process Datasets Separately ---
        with xr.open_dataset(xr.backends.NetCDF4DataStore(data_sfc)) as ds_sfc_raw, \
             xr.open_dataset(xr.backends.NetCDF4DataStore(data_10m)) as ds_10m_raw, \
             xr.open_dataset(xr.backends.NetCDF4DataStore(data_500mb)) as ds_500mb_raw:
            
            # Parse each dataset with MetPy
            ds_sfc = ds_sfc_raw.metpy.parse_cf()
            ds_10m = ds_10m_raw.metpy.parse_cf()
            ds_500mb = ds_500mb_raw.metpy.parse_cf()
            
            # Open the lapse rate dataset if it exists
            ds_lr = None
            if plot_params['plot_type'] == 'vtp':
                ds_lr_raw = xr.open_dataset(xr.backends.NetCDF4DataStore(data_lr))
                ds_lr = ds_lr_raw.metpy.parse_cf()

            # --- 4. Loop Through Time Steps, Calculate Parameter, and Generate Images ---
            for i, time in enumerate(ds_sfc.time.values):
                # --- Extract necessary variables from their respective datasets ---
                sbcape = ds_sfc['Convective_available_potential_energy_surface'].sel(time=time).squeeze()
                srh = ds_sfc['Storm_relative_helicity_height_above_ground_layer'].sel(time=time).squeeze()
                sbcin = ds_sfc['Convective_inhibition_surface'].sel(time=time).squeeze()
                temp_sfc = ds_sfc['Temperature_height_above_ground'].sel(time=time).squeeze() * units.kelvin
                dewp_sfc = ds_sfc['Dewpoint_temperature_height_above_ground'].sel(time=time).squeeze() * units.kelvin
                pres_sfc = ds_sfc['Pressure_surface'].sel(time=time).squeeze() * units.pascal
                u_sfc = ds_10m['u-component_of_wind_height_above_ground'].sel(time=time).squeeze() * units('m/s')
                v_sfc = ds_10m['v-component_of_wind_height_above_ground'].sel(time=time).squeeze() * units('m/s')
                u_500 = ds_500mb['u-component_of_wind_isobaric'].sel(time=time).squeeze() * units('m/s')
                v_500 = ds_500mb['v-component_of_wind_isobaric'].sel(time=time).squeeze() * units('m/s')

                # Get coordinates and CRS
                data_crs = sbcape.metpy.cartopy_crs
                x = sbcape.x.values
                y = sbcape.y.values

                # --- Calculate Derived Parameters ---
                lcl_pressure, _ = mpcalc.lcl(pres_sfc, temp_sfc, dewp_sfc)
                lcl_hght = mpcalc.pressure_to_height_std(lcl_pressure)
                u_shear = u_500 - u_sfc
                v_shear = v_500 - v_sfc
                bwd = mpcalc.wind_speed(u_shear, v_shear)

                # --- Calculate STP ---
                sbcape_val = sbcape.values
                lcl_hght_val = lcl_hght.magnitude
                srh_val = srh.values
                bwd_val = bwd.values
                sbcin_val = sbcin.values

                cape_term = sbcape_val / 1500.0
                lcl_term = (2000.0 - lcl_hght_val) / 1000.0
                lcl_term[lcl_term < 0] = 0
                srh_term = srh_val / 150.0
                bwd_term = bwd_val / 20.0
                bwd_term[bwd_val < 12.5] = 0
                cin_term = (200.0 + sbcin_val) / 150.0
                cin_term[cin_term < 0] = 0
                stp_values = cape_term * lcl_term * srh_term * bwd_term * cin_term
                
                # --- Main Plotting Logic ---
                if plot_params['plot_type'] == 'vtp':
                    # --- Calculate VTP using proxies ---
                    low_level_cape = ds_sfc['Convective_available_potential_energy_pressure_difference_layer'].sel(time=time).squeeze()
                    
                    # Manually calculate lapse rate
                    temp_975 = ds_lr['Temperature_isobaric'].sel(time=time, isobaric=97500, method='nearest').squeeze()
                    hght_975 = ds_lr['Geopotential_height_isobaric'].sel(time=time, isobaric=97500, method='nearest').squeeze()
                    temp_700 = ds_lr['Temperature_isobaric'].sel(time=time, isobaric=70000, method='nearest').squeeze()
                    hght_700 = ds_lr['Geopotential_height_isobaric'].sel(time=time, isobaric=70000, method='nearest').squeeze()
                    
                    # Use the .metpy.unit_array attribute to perform the calculation with units
                    lapse_rate = (-(temp_700.metpy.unit_array - temp_975.metpy.unit_array) / 
                                  (hght_700.metpy.unit_array - hght_975.metpy.unit_array)).to('delta_degC / km')

                    low_level_cape_val = low_level_cape.values
                    low_level_lr_val = lapse_rate.magnitude
                    
                    low_level_cape_term = low_level_cape_val / 150.0
                    low_level_lr_term = low_level_lr_val / 7.0
                    
                    plot_values = stp_values * low_level_cape_term * low_level_lr_term
                else: # Default to STP
                    plot_values = stp_values

                plot_values[plot_values < 0] = 0

                # --- Create Plot ---
                fig = plt.figure(figsize=(12, 10))
                map_proj = ccrs.LambertConformal(central_longitude=-92.5, central_latitude=38.5)
                ax = fig.add_subplot(1, 1, 1, projection=map_proj)
                ax.set_extent(list(plot_params['extent'].values()), crs=ccrs.PlateCarree())

                ax.add_feature(cfeature.STATES.with_scale('50m'), linestyle='-', edgecolor='black', zorder=2)
                ax.add_feature(cfeature.BORDERS.with_scale('50m'), linestyle=':', edgecolor='black', zorder=2)

                levels = plot_params['levels']
                contour_fill = ax.contourf(x, y, plot_values, levels=levels, cmap=plot_params['cmap'], transform=data_crs, extend='max')
                
                cbar = fig.colorbar(contour_fill, orientation='vertical', pad=0.02, aspect=25)
                cbar.set_label(plot_params['cbar_label'])
                
                valid_time = pd.to_datetime(str(time))
                forecast_hour = (valid_time - pd.to_datetime(str(ds_sfc.time.values[0]))).total_seconds() / 3600

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
        if ds_lr_raw:
            ds_lr_raw.close()
        if os.path.exists(img_dir):
            print(f"Cleaning up directory: {img_dir}")
            shutil.rmtree(img_dir)

if __name__ == '__main__':
    try:
        import pandas as pd
    except ImportError:
        print("Pandas is not installed. Please install it using: pip install pandas")
        exit()
        
    # --- Define parameters for the plot types ---
    STP_PARAMS = {
        'plot_type': 'stp',
        'variables': {
            'surface': [
                'Convective_available_potential_energy_surface',
                'Storm_relative_helicity_height_above_ground_layer',
                'Convective_inhibition_surface',
                'Temperature_height_above_ground',
                'Dewpoint_temperature_height_above_ground',
                'Pressure_surface'
            ],
            'agl_10m': ['u-component_of_wind_height_above_ground', 'v-component_of_wind_height_above_ground'],
            'isobaric_500mb': ['u-component_of_wind_isobaric', 'v-component_of_wind_isobaric']
        },
        'plot_title': 'Significant Tornado Parameter (STP)',
        'cbar_label': 'STP (unitless)',
        'levels': [0.5, 1, 2, 3, 4, 5, 6, 8, 10, 12],
        'cmap': 'plasma',
        'extent': {'west': -96, 'east': -89, 'south': 36, 'north': 41}
    }

    VTP_PARAMS = {
        'plot_type': 'vtp',
        'variables': {
            'surface': [
                'Convective_available_potential_energy_surface',
                'Storm_relative_helicity_height_above_ground_layer',
                'Convective_inhibition_surface',
                'Temperature_height_above_ground',
                'Dewpoint_temperature_height_above_ground',
                'Pressure_surface',
                'Convective_available_potential_energy_pressure_difference_layer'
            ],
            'agl_10m': ['u-component_of_wind_height_above_ground', 'v-component_of_wind_height_above_ground'],
            'isobaric_500mb': ['u-component_of_wind_isobaric', 'v-component_of_wind_isobaric'],
            'isobaric_lapse_rate': ['Temperature_isobaric', 'Geopotential_height_isobaric']
        },
        'plot_title': 'Violent Tornado Parameter (VTP)',
        'cbar_label': 'VTP (unitless)',
        'levels': [1, 2, 3, 4, 5, 7, 9, 11, 13, 15],
        'cmap': 'magma',
        'extent': {'west': -96, 'east': -89, 'south': 36, 'north': 41}
    }
    
    # --- User Selection ---
    choice = ''
    while choice not in ['stp', 'vtp']:
        choice = input("Select plot type: 'stp' or 'vtp': ").lower()

    if choice == 'stp':
        plot_interactive_forecast(STP_PARAMS)
    else:
        plot_interactive_forecast(VTP_PARAMS)
