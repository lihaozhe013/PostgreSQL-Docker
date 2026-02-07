#!/usr/bin/env python3
import subprocess
import os
import sys

# ================= CONFIGURATION =================
# The name of the container as defined in docker-compose
CONTAINER_NAME = 'system-postgres'

# The database user
DB_USER = 'postgres'

# The target database to restore into
TARGET_DB_NAME = 'postgres'

# The path to the dump file you want to restore
BACKUP_FILE_PATH = './backups/your_backup_file.dump'
# =================================================

def run_docker_sql(sql_command, db='postgres'):
    """
    Executes an SQL command inside the Docker container using psql.
    Returns a tuple: (success: bool, error_message: str)
    """
    cmd = [
        'docker', 'exec', 
        CONTAINER_NAME, 
        'psql', '-U', DB_USER, '-d', db, '-c', sql_command
    ]
    
    # Capture both stdout and stderr to handle errors gracefully
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, ""

def restore_database_safe():
    # 1. Validate backup file existence on host
    if not os.path.exists(BACKUP_FILE_PATH):
        print(f"[ERROR] Backup file not found: {BACKUP_FILE_PATH}")
        sys.exit(1)

    print(f"[INFO] Prepare to restore file: {BACKUP_FILE_PATH}")
    print(f"[INFO] Target Database: '{TARGET_DB_NAME}'")

    # 2. Attempt to Drop the existing database (Safe Mode)
    # We use double quotes \" around the DB name to handle hyphens (e.g., "my-db-1")
    # correctly. Without quotes, SQL interprets '-' as a subtraction operator.
    print(f"[STEP 1/3] Attempting to DROP database '{TARGET_DB_NAME}'...")
    
    drop_sql = f'DROP DATABASE IF EXISTS "{TARGET_DB_NAME}";'
    success, error_msg = run_docker_sql(drop_sql)

    if not success:
        print("\n" + "="*50)
        print(f"[ERROR] Failed to drop database.")
        print(f"[DETAILS] Postgres returned error: \n{error_msg}")
        print("="*50)
        
        # Check if the error is due to active connections
        if "accessed by other users" in error_msg:
            print("[SUGGESTION] There are active connections (e.g., Backend API, Navicat).")
            print("[SUGGESTION] Please stop your services or close connections manually.")
        else:
            print("[SUGGESTION] Check if the database name is valid.")
            
        print("[RESULT] Restore aborted. No data was changed.")
        sys.exit(1)

    # 3. Create a fresh database
    # Again, using double quotes to handle special characters safely.
    print(f"[STEP 2/3] Creating fresh database '{TARGET_DB_NAME}'...")
    create_sql = f'CREATE DATABASE "{TARGET_DB_NAME}";'
    success, error_msg = run_docker_sql(create_sql)
    
    if not success:
        print(f"[ERROR] Failed to create database: {error_msg}")
        sys.exit(1)

    # 4. Restore data from the dump file
    # We pipe the local file content directly to pg_restore inside the container.
    print(f"[STEP 3/3] Restoring data from dump file...")
    
    restore_cmd = [
        'docker', 'exec', '-i', 
        CONTAINER_NAME, 
        'pg_restore', 
        '-U', DB_USER, 
        '-d', TARGET_DB_NAME, 
        '-v',           # Verbose output
        '--no-owner',   # Skip restoring object ownership
        '--no-acl'      # Skip restoring access privileges
    ]

    try:
        with open(BACKUP_FILE_PATH, 'rb') as f:
            # Popen allows us to pipe the file (stdin) to the process
            process = subprocess.Popen(restore_cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = process.communicate()
            
            if process.returncode == 0:
                print(f"[SUCCESS] Database restore completed successfully!")
            else:
                # pg_restore often returns non-zero for minor warnings, which is okay.
                print(f"[INFO] Restore finished (exit code {process.returncode}).")
                if stderr:
                    err_text = stderr.decode('utf-8')
                    # Print the last few lines of the log for context
                    print(f"[LOG] Last 5 lines of output:\n{'\n'.join(err_text.splitlines()[-5:])}")

    except Exception as e:
        print(f"[EXCEPTION] Critical error during restore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    restore_database_safe()