from pathlib import Path

# Get the root directory of the project
# __file__ -> current script path
# .resolve() -> absolute path
# .parents[1] -> go up two levels in the folder hierarchy
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Define main data directory
DATA_DIR = PROJECT_ROOT / "data"

# Define subdirectories for raw and processed data
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Create the processed directory if it does not exist
# parents = True -> create parent folders if needed
# exist_ok = True -> avoid error if folder already exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)