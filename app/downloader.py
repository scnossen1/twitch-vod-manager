from pathlib import Path
import subprocess


def resolve_profile(item, idx):
  """Infers paths and enforces universal channel archiving and cleanup."""
  name = item.get("name") or f"streamer_{idx}"
  item["name"] = name

  # Auto-assign output directory template (optimized for Plex structure)
  if not item.get("output_template") and not item.get("output"):
    item["output_template"] = f"downloads/{name}/%(upload_date)s - %(title)s.%(ext)s"

  # Extract root target directory path for cleanup checks
  output_template = item.get("output_template") or item.get("output")
  parts = output_template.split("/")
  base_parts = [p for p in parts if "%" not in p]
  item["target_dir"] = "/".join(base_parts) if base_parts else "."

  # Every profile is now a channel feed: archive tracking and cleanup are mandatory
  item["archive_file"] = f"archives/{name}.txt"
  item["cleanup_enabled"] = True

  return item


def build_ytdlp_command(item):
  cmd = ["yt-dlp"]

  source = item.get("source") or item.get("url")
  if not source:
    raise ValueError("Each download entry must specify a 'source' or 'url'.")

  # Universal archive tracking prevents redownloading existing VODs
  archive_file = item.get("archive_file")
  archive_path = Path(archive_file)
  archive_path.parent.mkdir(parents=True, exist_ok=True)
  cmd.extend(["--download-archive", str(archive_path)])

  # Ensure output directory exists
  output_template = item.get("output_template") or item.get("output")
  if output_template:
    target_dir = Path(item["target_dir"])
    target_dir.mkdir(parents=True, exist_ok=True)
    cmd.extend(["-o", output_template])

  # Format selector
  fmt = item.get("format") or item.get("quality")
  if fmt:
    cmd.extend(["-f", str(fmt)])

  # Limit playlist/channel batch size per cycle to prevent rate limits
  cmd.extend(["--playlist-end", "5"])

  extra_args = item.get("extra_args")
  if extra_args and isinstance(extra_args, list):
    cmd.extend([str(arg) for arg in extra_args])

  cmd.append(source)
  return cmd


def execute_download(item):
  cmd = build_ytdlp_command(item)
  subprocess.run(cmd, check=True)