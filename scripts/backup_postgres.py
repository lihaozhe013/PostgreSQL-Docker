#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime

# ================= CONFIGURATION =================
# The name of the container as defined in docker-compose (container_name)
CONTAINER_NAME = 'system-postgres'

# The database user (as defined in environment variables)
DB_USER = 'postgres'

# The specific database name you want to backup
# Change this to your target database name
DB_NAME = 'postgres' 

# The directory where backup files will be saved
BACKUP_DIR = './backups'

# Backup file format: 'c' for custom (compressed), 'p' for plain text (SQL)
# 'c' is recommended for large databases as it supports pg_restore
FORMAT = 'c'
# =================================================

def backup_database():
    """
    Backs up a Postgres database running inside a Docker container.
    """
    
    # 1. Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        try:
            os.makedirs(BACKUP_DIR)
            print(f"[INFO] Created backup directory: {BACKUP_DIR}")
        except OSError as e:
            print(f"[ERROR] Failed to create directory: {e}")
            return

    # 2. Generate a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    extension = 'dump' if FORMAT == 'c' else 'sql'
    filename = f"{DB_NAME}_{timestamp}.{extension}"
    filepath = os.path.join(BACKUP_DIR, filename)

    print(f"[INFO] Starting backup for database: '{DB_NAME}'...")

    # 3. Construct the Docker command
    # We use 'docker exec -i' to allow piping stdout to a file.
    # We do not use '-t' (tty) to avoid carriage return issues in binary files.
    cmd = [
        'docker', 'exec', '-i', 
        CONTAINER_NAME, 
        'pg_dump', 
        '-U', DB_USER, 
        '-F', FORMAT, 
        DB_NAME
    ]

    # 4. Execute the command and write stream to file
    try:
        with open(filepath, 'wb') as f:
            # We pass environment variables if needed (e.g., PGPASSWORD)
            # Since we rely on the container's environment, standard config usually allows 'postgres' user trust.
            # If a password prompt fails, we might need to inject PGPASSWORD env var here.
            process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE)
            
            # Wait for the process to complete
            _, stderr = process.communicate()

            if process.returncode == 0:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"[SUCCESS] Backup successful!")
                print(f"[SAVED] File: {filepath}")
                print(f"[SIZE] {size_mb:.2f} MB")
            else:
                print(f"[ERROR] Backup failed with return code {process.returncode}")
                if stderr:
                    print(f"[DETAILS] {stderr.decode('utf-8')}")

    except Exception as e:
        print(f"[EXCEPTION] An error occurred: {e}")

if __name__ == "__main__":
    backup_database()