import numpy as np
from datetime import datetime

def ascii_convert(filename, q_deg):
    """
    Converts a trajectory matrix into a FANUC LS ASCII file.
    
    Args:
        filename (str): Output path (e.g., 'TRAJTEST.LS')
        q_deg (np.ndarray): N x 6 array of joint angles in degrees
    """
    prog_name = 'TRAJTEST'
    group_num = 1
    n_points = q_deg.shape[0]
    speed_percent = 100
    
    # Ensure q_deg is a numpy array
    q_deg = np.array(q_deg)
    
    # Line count logic from original MATLAB code: N + 2 lines total
    # Note: The original code logic skips P[2] and P[3] in the motion section.
    line_count = n_points + 2

    try:
        with open(filename, 'w') as f:
            # -------- HEADER --------
            f.write(f"/PROG  {prog_name}\n")
            f.write("/ATTR\n")
            f.write("OWNER        = MNEDITOR;\n")
            f.write("COMMENT      = \"Generated from Python\";\n")
            f.write("PROG_SIZE    = 0;\n")
            f.write("CREATE       = DATE 00-00-00  TIME 00:00:00;\n")
            f.write("MODIFIED     = DATE 00-00-00  TIME 00:00:00;\n")
            f.write(f"FILE_NAME    = {prog_name};\n")
            f.write("VERSION      = 0;\n")
            f.write(f"LINE_COUNT   = {line_count};\n")
            f.write("MEMORY_SIZE  = 0;\n")
            f.write("PROTECT      = READ_WRITE;\n")
            f.write("TCD:  STACK_SIZE    = 0,\n")
            f.write("      TASK_PRIORITY = 50,\n")
            f.write("      TIME_SLICE    = 0,\n")
            f.write("      BUSY_LAMP_OFF = 0,\n")
            f.write("      ABORT_REQUEST = 0,\n")
            f.write("      PAUSE_REQUEST = 0;\n")
            f.write(f"DEFAULT_GROUP   = {group_num},*,*,*,*;\n")
            f.write("CONTROL_CODE    = 00000000 00000000;\n")
            f.write("/APPL\n")
            f.write("/MN\n")
            
            # --------- TIMER -------------
            f.write("   1:  TIMER[1]=RESET;\n")
            f.write("   2:  TIMER[1]=START;\n")
            
            # -------- MOTION LINES --------
            # Line 3: Move to first point
            f.write(f"   3:  J P[1] {speed_percent}% FINE ;\n")
            
            # Following the MATLAB logic: starts loop at line 4 through N
            for i in range(4, n_points + 1):
                f.write(f"   {i}:  J P[{i}] {speed_percent}% FINE ;\n")
            
            f.write(f"   {n_points + 1}:  TIMER[1]=STOP;\n")
            f.write(f"   {n_points + 2}:  END ;\n")
            
            # -------- POSITIONS --------
            f.write("/POS\n")
            for i in range(n_points):
                joints = q_deg[i, :]
                point_id = i + 1  # 1-based indexing for the robot
                f.write(f"P[{point_id}]{{\n")
                f.write("   GP1:\n")
                f.write("    UF : 0, UT : 1,\n")
                f.write(f"    J1 = {joints[0]:8.3f} deg, J2 = {joints[1]:8.3f} deg, J3 = {joints[2]:8.3f} deg,\n")
                f.write(f"    J4 = {joints[3]:8.3f} deg, J5 = {joints[4]:8.3f} deg, J6 = {joints[5]:8.3f} deg \n")
                f.write("};\n")
                
            f.write("/END\n")
            
    except IOError as e:
        print(f"Could not open file {filename}: {e}")

# Example Usage:
# data = np.random.uniform(-90, 90, (10, 6))
# ascii_convert('TEST.LS', data)