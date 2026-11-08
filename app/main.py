"""Main entry point for the Streamlined Twitch Downloader Daemon.

This module orchestrates the download pipeline by:
1. Loading configuration from YAML files
2. Iterating through download profiles
3. Executing downloads via the downloader module
4. Pruning old files via the cleanup module
5. Repeating on a configurable interval
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from cleanup import prune_directory
from downloader import execute_download, resolve_profile


def load_yaml(filepath: str) -> Union[List[Any], Dict[str, Any]]:
    """Load and parse a YAML configuration file.
    
    Args:
        filepath: Path to the YAML file to load
        
    Returns:
        Parsed YAML content as a list or dict, or empty list on error
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Warning: Config file '{filepath}' not found.")
        return []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else []
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in '{filepath}': {e}")
        return []
    except PermissionError:
        print(f"Permission denied reading '{filepath}'.")
        return []
    except Exception as e:
        print(f"Error loading '{filepath}': {e}")
        return []


def run_pipeline(config_path: str, settings_path: str) -> None:
    """Execute one full cycle of the download pipeline.
    
    Processes each download profile in sequence:
    1. Resolves the profile with defaults
    2. Executes the download
    3. Prunes old downloads if configured
    
    Args:
        config_path: Path to the download profiles config file
        settings_path: Path to the daemon settings file
    """
    # Expect config.yaml to be a direct list of download profiles
    downloads = load_yaml(config_path)
    
    if not isinstance(downloads, list) or not downloads:
        print("No download profiles found or invalid config format (expected a list).")
        return
    
    print(f"\n[Cycle Start] Found {len(downloads)} download profile(s). Starting execution...")
    
    for idx, raw_item in enumerate(downloads, 1):
        item = resolve_profile(raw_item, idx)
        profile_name = item.get("name", f"profile_{idx}")
        
        print(f"\n{'='*40}")
        print(f"=== Processing Profile [{profile_name}] ({idx}/{len(downloads)}) ===")
        print('='*40)
        
        try:
            # Step 1: Execute download via downloader.py
            execute_download(item)
            print(f"Profile '{profile_name}' download finished successfully.")
            
            # Step 2: Universal rolling retention pruning for channel profiles
            keep_count = item.get("max_keep", 5)
            target_dir = item.get("target_dir", "downloads")
            prune_directory(target_dir, keep_count=keep_count)
            
        except Exception as e:
            print(f"Error processing profile '{profile_name}': {e}")
        
        print("-" * 40)


def load_settings(filepath: str) -> Dict[str, Any]:
    """Load daemon settings from YAML file.
    
    Args:
        filepath: Path to the settings file
        
    Returns:
        Settings dictionary with defaults applied
    """
    settings = load_yaml(filepath)
    
    # Fallback to default dict if settings is loaded as something else
    if not isinstance(settings, dict):
        settings = {}
    
    # Apply defaults
    settings.setdefault("refresh_interval_hours", 4)
    return settings


def main() -> None:
    """Main entry point for the daemon.
    
    Parses command-line arguments, then runs the download pipeline
    in an infinite loop with configurable intervals.
    """
    parser = argparse.ArgumentParser(
        description="Streamlined Twitch Downloader Daemon."
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )
    parser.add_argument(
        "-s", "--settings",
        default="settings.yaml",
        help="Path to settings file (default: settings.yaml)"
    )
    args = parser.parse_args()
    
    print("=" * 50)
    print("Starting Streamlined Twitch Downloader Daemon...")
    print("=" * 50)
    
    try:
        while True:
            run_pipeline(args.config, args.settings)
            
            # Load settings for interval
            settings = load_settings(args.settings)
            refresh_hours = settings.get("refresh_interval_hours", 4)
            sleep_seconds = int(refresh_hours * 3600)
            
            print(f"\n[Cycle Complete] Sleeping for {refresh_hours} hour(s)...")
            
            try:
                time.sleep(sleep_seconds)
            except KeyboardInterrupt:
                print("\nDaemon stopped by user.")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\nDaemon stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()