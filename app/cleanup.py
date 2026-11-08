"""Module for cleaning up downloaded video files.

Provides functionality to prune old video files from download
directories based on modification time and retention count.
"""

from pathlib import Path
from typing import Set, Optional


# Constants
VIDEO_EXTENSIONS: Set[str] = {".mp4", ".mkv", ".ts", ".mov"}


def prune_directory(
    target_dir: str,
    keep_count: int = 5,
    extensions: Optional[Set[str]] = None
) -> None:
    """Prune old video files from a directory, keeping only the newest ones.
    
    Scans the target directory for video files, sorts them by modification
    time (newest first), and removes any files beyond the keep_count limit.
    
    Args:
        target_dir: Path to the directory to clean up
        keep_count: Number of most recent files to retain (default: 5)
        extensions: Optional set of video file extensions to consider
    """
    if extensions is None:
        extensions = VIDEO_EXTENSIONS
        
    directory = Path(target_dir)
    if not directory.exists() or not directory.is_dir():
        print(f"[{target_dir}] Directory does not exist yet. Skipping cleanup.")
        return

    # Filter for video files
    files = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ]

    # Sort newest first based on modification time
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"[{target_dir}] Found {len(files)} VOD file(s). Target limit: {keep_count}.")

    if len(files) > keep_count:
        print(f"Pruning excess files... keeping the latest {keep_count}.")
        files_to_remove = files[keep_count:]
        for old_file in files_to_remove:
            print(f"  Deleting old VOD: {old_file.name}")
            try:
                old_file.unlink()
            except PermissionError as e:
                print(f"  Permission denied for {old_file.name}: {e}")
            except OSError as e:
                print(f"  OS error deleting {old_file.name}: {e}")
    else:
        print(f"File count is within the limit. No pruning needed.")