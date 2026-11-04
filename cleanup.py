from pathlib import Path
import yaml


def load_config(config_path="config.yaml"):
  try:
    with open(config_path, "r", encoding="utf-8") as f:
      return yaml.safe_load(f)
  except Exception as e:
    print(f"Error loading config for cleanup: {e}")
    return {}


def prune_directory(target_dir, keep_count=5):
  directory = Path(target_dir)
  if not directory.exists() or not directory.is_dir():
    return

  video_extensions = {".mp4", ".mkv", ".ts", ".mov"}
  files = [
      f for f in directory.iterdir() 
      if f.is_file() and f.suffix.lower() in video_extensions
  ]

  # Sort newest first based on modification time
  files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

  if len(files) > keep_count:
    print(f"[{target_dir}] Found {len(files)} files. Pruning to keep latest {keep_count}...")
    for old_file in files[keep_count:]:
      print(f"  Deleting old VOD: {old_file.name}")
      try:
        old_file.unlink()
      except Exception as e:
        print(f"  Failed to delete {old_file.name}: {e}")


def main():
  config = load_config()
  downloads = config.get("downloads", [])

  # Track directories we've already cleaned to avoid redundant scans
  cleaned_dirs = set()

  for item in downloads:
    output_template = item.get("output_template") or item.get("output")
    if not output_template:
      continue

    # Extract the root directory path from the template (e.g., 'downloads/streamername' from 'downloads/streamername/%(title)s.%(ext)s')
    # We strip off the filename portion containing template variables
    parts = output_template.split("/")
    base_parts = [p for p in parts if "%" not in p]
    target_dir = "/".join(base_parts) if base_parts else "."

    if target_dir not in cleaned_dirs and target_dir != ".":
      prune_directory(target_dir, keep_count=5)
      cleaned_dirs.add(target_dir)


if __name__ == "__main__":
  main()