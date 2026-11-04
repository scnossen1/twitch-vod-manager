from pathlib import Path
import yaml


def load_config(config_path="config.yaml"):
  try:
    with open(config_path, "r", encoding="utf-8") as f:
      return yaml.safe_load(f)
  except Exception as e:
    print(f"Error loading config for cleanup: {e}")
    return {}


def resolve_profile(item, idx):
  """Ensures output_template matches the downloader's auto-resolution logic."""
  name = item.get("name") or f"streamer_{idx}"
  if not item.get("output_template") and not item.get("output"):
    item["output_template"] = f"downloads/{name}/%(upload_date)s - %(title)s.%(ext)s"
  return item


def prune_directory(target_dir, keep_count=5):
  directory = Path(target_dir)
  if not directory.exists() or not directory.is_dir():
    print(f"[{target_dir}] Directory does not exist yet. Skipping cleanup.")
    return

  video_extensions = {".mp4", ".mkv", ".ts", ".mov"}
  files = [
      f for f in directory.iterdir()
      if f.is_file() and f.suffix.lower() in video_extensions
  ]

  # Sort newest first based on modification time
  files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

  print(f"[{target_dir}] Found {len(files)} VOD file(s). Target limit: {keep_count}.")

  if len(files) > keep_count:
    print(f"Pruning excess files... keeping the latest {keep_count}.")
    for old_file in files[keep_count:]:
      print(f"  Deleting old VOD: {old_file.name}")
      try:
        old_file.unlink()
      except Exception as e:
        print(f"  Failed to delete {old_file.name}: {e}")
  else:
    print(f"File count is within the limit. No pruning needed.")


def main():
  config = load_config()
  downloads = config.get("downloads", [])

  if not downloads:
    print("No download profiles found in config.")
    return

  print("=== Starting Cleanup Routine ===")
  for idx, raw_item in enumerate(downloads, 1):
    item = resolve_profile(raw_item, idx)
    profile_name = item.get("name")

    # Skip profiles where archiving or cleanup is explicitly disabled (e.g., single VOD tests)
    is_archived = item.get("archive", True)
    cleanup_enabled = item.get("cleanup", is_archived)
    
    if not cleanup_enabled:
      print(f"\nSkipping cleanup for profile: '{profile_name}' (Cleanup/Archiving disabled)")
      continue

    output_template = item.get("output_template") or item.get("output")

    # Extract the root directory path from the template
    parts = output_template.split("/")
    base_parts = [p for p in parts if "%" not in p]
    target_dir = "/".join(base_parts) if base_parts else "."

    # Allow custom retention limit per profile if specified, otherwise default to 5
    keep_count = item.get("max_keep", 5)

    print(f"\nProcessing profile: '{profile_name}' (Dir: {target_dir})")
    prune_directory(target_dir, keep_count=keep_count)

  print("\n=== Cleanup Complete ===")


if __name__ == "__main__":
  main()