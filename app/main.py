from app.cleanup import prune_directory
from app.downloader import build_ytdlp_command, resolve_profile
import argparse
import subprocess
import sys
import time
import yaml


def load_yaml(filepath):
  try:
    with open(filepath, "r", encoding="utf-8") as f:
      return yaml.safe_load(f) or {}
  except Exception as e:
    print(f"Error loading '{filepath}': {e}")
    return {}


def run_pipeline(config_path):
  config = load_yaml(config_path)
  downloads = config.get("downloads", [])

  if not downloads:
    print("No download profiles found in configuration.")
    return

  print(f"\n[Cycle Start] Found {len(downloads)} download profile(s). Starting execution...")

  for idx, raw_item in enumerate(downloads, 1):
    item = resolve_profile(raw_item, idx)
    profile_name = item["name"]
    
    print(f"=== Processing Profile [{profile_name}] ({idx}/{len(downloads)}) ===")
    try:
      cmd = build_ytdlp_command(item)
      subprocess.run(cmd, check=True)
      print(f"Profile '{profile_name}' download finished successfully.")

      if item["cleanup_enabled"]:
        keep_count = item.get("max_keep", 5)
        prune_directory(item["target_dir"], keep_count=keep_count)
      else:
        print(f"Skipping cleanup for '{profile_name}' (Single VOD mode).")

      print("-" * 40)
      
    except subprocess.CalledProcessError as e:
      print(f"\n[ERROR] yt-dlp failed on profile '{profile_name}' with exit code {e.returncode}\n")
    except Exception as e:
      print(f"Unexpected error on profile '{profile_name}': {e}\n")


def main():
  parser = argparse.ArgumentParser(description="Twitch VOD Downloader Daemon.")
  parser.add_argument(
      "-c", "--config", default="config.yaml", help="Path to config file"
  )
  parser.add_argument(
      "-s", "--settings", default="settings.yaml", help="Path to settings file"
  )
  args = parser.parse_args()

  print("Starting Twitch Downloader Daemon with isolated settings...")

  while True:
    # 1. Run the ingestion cycle using download config
    run_pipeline(args.config)

    # 2. Re-read settings fresh on each cycle to pick up on-the-fly edits
    settings = load_yaml(args.settings)
    refresh_hours = settings.get("refresh_interval_hours", 4)
    sleep_seconds = int(refresh_hours * 3600)

    print(f"\n[Cycle Complete] Sleeping for {refresh_hours} hour(s) ({sleep_seconds} seconds)...")
    try:
      time.sleep(sleep_seconds)
    except KeyboardInterrupt:
      print("\nDaemon stopped by user.")
      sys.exit(0)


if __name__ == "__main__":
  main()