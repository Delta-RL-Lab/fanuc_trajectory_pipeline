import numpy as np
from scipy.interpolate import PchipInterpolator

def resample_to_4ms(time, data):
    """
    Resamples trajectory data to a constant 4ms (0.004s) sample rate.
    
    Args:
        time (np.ndarray): Original time vector [N] or [N, 1] in seconds.
        data (np.ndarray): Original joint data [N, nJoints].
        
    Returns:
        t4 (np.ndarray): New time vector with 4ms spacing.
        q4 (np.ndarray): Resampled joint matrix.
    """
    # Ensure time is a 1D array (equivalent to t(:) in MATLAB)
    t = np.array(time).flatten()
    q = np.array(data)
    
    # Define the new time grid (4ms steps)
    dt = 0.004
    # np.arange excludes the stop value, so we add a tiny epsilon 
    # or use np.linspace to match MATLAB's t(1):dt:t(end) behavior
    t4 = np.arange(t[0], t[-1] + dt/2, dt)
    
    # Initialize the PCHIP interpolator
    # axis=0 ensures interpolation happens along the time dimension
    interp_func = PchipInterpolator(t, q, axis=0)
    
    # Generate the resampled data
    q4 = interp_func(t4)
    
    return t4, q4

# --- Example of how to use it with a 'timeseries-like' object ---
# class JointTS:
#     def __init__(self, time, data):
#         self.Time = time
#         self.Data = data
#
# joint_ts = JointTS(np.array([0, 0.1, 0.5]), np.random.rand(3, 6))
# t_new, q_new = resample_to_4ms(joint_ts.Time, joint_ts.Data)