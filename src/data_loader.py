import pandas as pd
import numpy as np

def load_csv_trajectory(file_path):
    """
    Reads a semicolon-separated CSV and returns time (s) and data (m, rad).
    Format expected: timestep;x;y;z;w;p;r
    """
    try:
        # Load CSV with semicolon separator
        df = pd.read_csv(file_path, sep=';')
        
        # 1. Convert Time: ms -> seconds
        raw_time = df['timestep'].values / 1000.0
        
        # 2. Convert Position: mm -> meters
        # (Your pipeline's generate_ls_cart will convert this back to mm later)
        x_m = df['x'].values / 1000.0
        y_m = df['y'].values / 1000.0
        z_m = df['z'].values / 1000.0
        
        # 3. Convert Orientation: degrees -> radians
        # (Your pipeline's generate_ls_cart will convert this back to deg later)
        w_rad = np.radians(df['w'].values)
        p_rad = np.radians(df['p'].values)
        r_rad = np.radians(df['r'].values)
        
        # Stack into [N x 6] matrix
        raw_cart_data = np.column_stack((x_m, y_m, z_m, w_rad, p_rad, r_rad))
        
        return raw_time, raw_cart_data
        
    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        raise