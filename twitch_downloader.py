import argparse
import subprocess
import sys
import yaml


def load_config(config_path):
  try:
    with open(config_path, "r", encoding="utf-8") as f:
      return yaml.safe_load(f)
  except Exception as e:
    print(f"Error loading config file '{config_path}': {e}")
    sys.exit(1)


def resolve_profile(item, idx):
  """Dynamically assigns name, output_template, and archive_file if omitted."""
  name = item.get("name") or f"streamer_{idx}"
  item["name"] = name

  if not item.get("output_template") and not item.get("output"):
    item["output_template"] = f"downloads/{name}/%(upload_date)s - %(title)s.%(ext)s"

  if not item.get("archive_file"):
    item["archive_file"] = f"archives/{name}.txt"

  return item


def build_ytdlp_command(item):
  cmd = ["yt-dlp"]

  source = item.get("source") or item.get("url")
  if not source:
    raise ValueError("Each download entry must specify a 'source' or 'url'.")

  # Use exact format selector directly (default to 'best' if not specified)
  fmt = item.get("format") or item.get("quality")
  if fmt:
    cmd.extend(["-f", str(fmt)])

  output_template = item.get("output_template") or item.get("output")
  cmd.extend(["-o", output_template])

  # Enforce grabbing only the latest 5 VODs from the channel playlist
  cmd.extend(["--playlist-end", "5"])

  archive_file = item.get("archive_file")
  cmd.extend(["--download-archive", archive_file])

  extra_args = item.get("extra_args")
  if extra_args and isinstance(extra_args, list):
    cmd.extend([str(arg) for arg in extra_args])

  cmd.append(source)
  return cmd


def main():
  parser = argparse.ArgumentParser(description="Twitch VOD Downloader.")
  parser.add_argument(
      "-c", "--config", default="config.yaml", help="Path to config file"
  )
  args = parser.parse_args()

  config = load_config(args.config)
  downloads = config.get("downloads", [])

  if not downloads:
    print("No download profiles found in configuration.")
    sys.exit(0)

  print(f"Found {len(downloads)} download profile(s). Starting tasks...\n")

  for idx, raw_item in enumerate(downloads, 1):
    item = resolve_profile(raw_item, idx)
    profile_name = item["name"]
    
    print(f"=== Processing Profile [{profile_name}] ({idx}/{len(downloads)}) ===")
    try:
      cmd = build_ytdlp_command(item)
      subprocess.run(cmd, check=True)
      print(f"Profile '{profile_name}' finished successfully.\n")
    except subprocess.CalledProcessError as e:
      print(f"Error: yt-dlp exited with status {e.returncode} on profile '{profile_name}'.\n")
    except Exception as e:
      print(f"Unexpected error on profile '{profile_name}': {e}\n")


if __name__ == "__main__":
  main()