from app.cleanup import prune_directory
from app.downloader import execute_download, resolve_profile
import argparse
from pathlib import Path
import subprocess
import sys
import time
import yaml


def load_yaml(filepath):
  path = Path(filepath)
  if not path.exists():
    return []
  try:
    with open(path, "r", encoding="utf-8") as f:
      return yaml.safe_load(f) or []
  except Exception as e:
    print(f"Error loading '{filepath}': {e}")
    return []


def run_pipeline(config_path):
  # Expect config.yaml to be a direct list of download profiles
  downloads = load_yaml(config_path)

  if not isinstance(downloads, list) or not downloads:
    print("No download profiles found or invalid config format (expected a list).")
    return

  print(f"\n[Cycle Start] Found {len(downloads)} download profile(s). Starting execution...")

  for idx, raw_item in enumerate(downloads, 1):
    item = resolve_profile(raw_item, idx)
    profile_name = item["name"]
    
    print(f"=== Processing Profile [{profile_name}] ({idx}/{len(downloads)}) ===")
    try:
      # Step 1: Execute download via downloader.py
      execute_download(item)
      print(f"Profile '{profile_name}' download finished successfully.")

      # Step 2: Universal rolling retention pruning for channel profiles
      keep_count = item.get("max_keep", 5)
      prune_directory(item["target_dir"], keep_count=keep_count)

      print("-" * 40)
      
    except subprocess.CalledProcessError as e:
      print(f"\n[ERROR] yt-dlp failed on profile '{profile_name}' with exit code {e.returncode}\n")
    except Exception as e:
      print(f"Unexpected error on profile '{profile_name}': {e}\n")


def main():
  parser = argparse.ArgumentParser(description="Twitch VOD Downloader Daemon.")
  parser.add_argument("-c", "--config", default="config.yaml", help="Path to config file")
  parser.add_argument("-s", "--settings", default="settings.yaml", help="Path to settings file")
  args = parser.parse_args()

  print("Starting Streamlined Twitch Downloader Daemon...")

  while True:
    run_pipeline(args.config)

    settings = load_yaml(args.settings)
    # Fallback to default dict if settings is loaded as something else
    if not isinstance(settings, dict):
      settings = {}
      
    refresh_hours = settings.get("refresh_interval_hours", 4)
    sleep_seconds = int(refresh_hours * 3600)

    print(f"\n[Cycle Complete] Sleeping for {refresh_hours} hour(s)...")
    try:
      time.sleep(sleep_seconds)
    except KeyboardInterrupt:
      print("\nDaemon stopped by user.")
      sys.exit(0)


if __name__ == "__main__":
  main()
