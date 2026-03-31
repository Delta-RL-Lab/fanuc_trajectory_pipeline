import os
from ftplib import FTP

def ftp_upload(host, local_file, remote_dir='UD1:', username='anonymous', password=''):
    """
    Uploads a FANUC .LS file to the controller via FTP.
    
    Args:
        host (str): IP address of the FANUC controller.
        username (str): FTP username (usually 'anonymous').
        password (str): FTP password (usually empty '').
        local_file (str): Path to the local file to upload.
        remote_dir (str): Target directory on the robot (e.g., '/md/', '/fr/').
    """
    
    # 1. Basic sanity check (does the file exist?)
    if not os.path.exists(local_file):
        raise FileNotFoundError(f"Local file not found: {local_file}")

    filename = os.path.basename(local_file)
    print(f"Connecting to FANUC FTP at {host}...")

    ftp = None
    try:
        # 2. Open FTP connection
        ftp = FTP(host)
        ftp.login(user=username, passwd=password)
        
        # 3. Enable passive mode (standard for most modern networks)
        ftp.set_pasv(True)
        
        # 4. Change to target directory
        if remote_dir:
            print(f"Changing directory to {remote_dir}...")
            ftp.cwd(remote_dir)
            
        # 5. Upload the file
        # 'rb' opens the file in binary mode; 'STOR' is the FTP command to save
        print(f"Uploading {filename} to {remote_dir}...")
        with open(local_file, 'rb') as f:
            ftp.storbinary(f"STOR {filename}", f)
            
        print("Upload completed successfully.")

    except Exception as e:
        print(f"FTP upload failed: {e}")
        raise  # Re-raise the error so the calling script knows it failed

    finally:
        # 6. Close connection gracefully
        if ftp:
            try:
                ftp.quit()
                print("FTP connection closed.")
            except:
                ftp.close() # Force close if quit() fails

# Example Usage:
# ftp_upload('10.147.229.170', 'anonymous', '', 'TRAJ4MS.LS', '/md/')