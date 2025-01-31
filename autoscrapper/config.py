# config.py at the project source code root
import os
import glob

PROJECT_SOURCE_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_LOG_FOLDER = os.path.join(PROJECT_SOURCE_ROOT, 'log_files')

# Find the next task number
existing_tasks = glob.glob(os.path.join(BASE_LOG_FOLDER, 'task_*'))
next_task_num = 1 if not existing_tasks else max([int(os.path.basename(t).split('_')[1]) for t in existing_tasks]) + 1
SOURCE_LOG_FOLDER_PATH = os.path.join(BASE_LOG_FOLDER, f'task_{next_task_num}')

PROJECT_ROOT = os.path.dirname(PROJECT_SOURCE_ROOT)

PROJECT_TEMP_PATH = os.path.join(PROJECT_ROOT, 'temp')

# Check if the log folder exists, and if not, create it
if not os.path.exists(SOURCE_LOG_FOLDER_PATH):
    os.makedirs(SOURCE_LOG_FOLDER_PATH)
    print(f"Created log folder at: {SOURCE_LOG_FOLDER_PATH}")

if not os.path.exists(PROJECT_TEMP_PATH):
    os.makedirs(PROJECT_TEMP_PATH)
    print(f"Created temp folder at: {PROJECT_TEMP_PATH}")
