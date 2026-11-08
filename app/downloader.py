"""Download execution module for processing video downloads.

This module handles:
- Resolving download profiles with defaults
- Extracting target directories from output templates
- Executing downloads with yt-dlp
- Archive tracking to prevent duplicate downloads
"""

from pathlib import Path
import subprocess
from typing import Dict, Any, List, Optional


def resolve_profile(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Resolve a download profile with default values.
    
    Ensures output_template is set if not already provided,
    matching the auto-resolution logic used elsewhere.
    
    Args:
        item: The raw profile dictionary from config
        idx: The 1-based index of this profile (used for naming fallback)
        
    Returns:
        The resolved profile dictionary with all defaults applied
    """
    name = item.get("name") or f"streamer_{idx}"
    if not item.get("output_template") and not item.get("output"):
        item["output_template"] = f"downloads/{name}/%(upload_date)s - %(title)s.%(ext)s"
    return item


def extract_target_dir(output_template: str) -> str:
    """Extract the root target directory from an output template string.
    
    Filters out yt-dlp template specifiers (like %(title)s) to get
    only the static directory path components.
    
    Args:
        output_template: The yt-dlp output template string
        
    Returns:
        The base directory path, or "." if no static parts exist
    """
    parts = output_template.split("/")
    base_parts = [p for p in parts if "%" not in p]
    return "/".join(base_parts) if base_parts else "."


def build_ytdlp_command(item: Dict[str, Any]) -> List[str]:
    """Build the complete yt-dlp command for a download profile.
    
    Args:
        item: The resolved download profile dictionary
        
    Returns:
        List of command arguments ready for subprocess execution
    """
    output_template = item.get("output_template") or item.get("output")
    url = item.get("url")
    if not url:
        raise ValueError(f"Profile '{item.get('name', 'unknown')}' missing 'url'")
    
    cmd = ["yt-dlp", url]
    
    if output_template:
        cmd.extend(["-o", output_template])
    
    return cmd


def execute_download(item: Dict[str, Any]) -> None:
    """Execute a download for the given profile item.
    
    Sets up target directory tracking and archive file for deduplication,
    then runs the yt-dlp command.
    
    Args:
        item: The resolved download profile dictionary
    """
    name = item.get("name", "unknown")
    output_template = item.get("output_template") or item.get("output")
    
    # Extract root target directory path for cleanup checks
    item["target_dir"] = extract_target_dir(output_template)
    
    # Universal archive tracking prevents redownloading existing VODs
    archive_file = item.get("archive_file")
    if archive_file:
        archive_path = Path(archive_file)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build command
    cmd = build_ytdlp_command(item)
    if archive_file:
        cmd.extend(["--download-archive", str(archive_path)])
    
    print(f"[{name}] Starting download from: {item.get('url')}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[{name}] Download completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[{name}] Download failed with exit code {e.returncode}")
        raise