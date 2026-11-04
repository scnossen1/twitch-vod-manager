import argparse
from pathlib import Path
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
  """Dynamically assigns name, output paths, and archive logic."""
  name = item.get("name") or f"streamer_{idx}"
  item["name"] = name

  if not item.get("output_template") and not item.get("output"):
    item["output_template"] = f"downloads/{name}/%(upload_date)s - %(title)s.%(ext)s"

  is_archived = item.get("archive", True)
  if is_archived and not item.get("archive_file"):
    item["archive_file"] = f"archives/{name}.txt"
  elif not is_archived:
    item["archive_file"] = None

  return item


def build_ytdlp_command(item):
  cmd = ["yt-dlp"]

  source = item.get("source") or item.get("url")
  if not source:
    raise ValueError("Each download entry must specify a 'source' or 'url'.")

  archive_file = item.get("archive_file")
  if archive_file:
    archive_path = Path(archive_file)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    cmd.extend(["--download-archive", str(archive_path)])

  output_template = item.get("output_template") or item.get("output")
  if output_template:
    parts = output_template.split("/")
    base_parts = [p for p in parts if "%" not in p]
    if base_parts:
      target_dir = Path("/".join(base_parts))
      target_dir.mkdir(parents=True, exist_ok=True)
    cmd.extend(["-o", output_template])

  fmt = item.get("format") or item.get("quality")
  if fmt:
    cmd.extend(["-f", str(fmt)])

  cmd.extend(["--playlist-end", "5"])

  extra_args = item.get("extra_args")
  if extra_args and isinstance(extra_args, list):
    cmd.extend([str(arg) for arg in extra_args])

  cmd.append(source)
  return cmd
  