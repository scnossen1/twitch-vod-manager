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


def build_ytdlp_command(item):
  cmd = ["yt-dlp"]

  source = item.get("source") or item.get("url")
  if not source:
    raise ValueError("Each download entry must specify a 'source' or 'url'.")

  quality = item.get("quality", "best")
  if quality == "best":
    cmd.extend(["-f", "bestvideo+bestaudio/best"])
  elif quality == "worst":
    cmd.extend(["-f", "worst"])
  else:
    cmd.extend(["-f", quality])

  output_template = item.get("output_template") or item.get("output")
  if output_template:
    cmd.extend(["-o", output_template])

  # Enforce grabbing only the latest 5 VODs from the channel playlist
  cmd.extend(["--playlist-end", "5"])

  archive_file = item.get("archive_file", "download_archive.txt")
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

  for idx, item in enumerate(downloads, 1):
    print(f"=== Processing Task {idx} ===")
    try:
      cmd = build_ytdlp_command(item)
      subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
      print(f"yt-dlp exited with error code {e.returncode}")
    except Exception as e:
      print(f"An error occurred: {e}")


if __name__ == "__main__":
  main()