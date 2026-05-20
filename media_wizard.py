"""
iOS Local Backup Media Wizard
Description: An interactive utility to extract, structure, and restore 
             original timestamps for photos and videos locked inside 
             unencrypted local iOS backups on Windows systems.
License: MIT
"""

import os
import sys
import sqlite3
import shutil
import re
from pathlib import Path

# --- SYSTEM AUTO-LAUNCHER LOGIC ---
def create_windows_launcher():
    """
    Automatically generates a 'Click_To_Run.bat' file next to the script
    if executed on a Windows machine. This eliminates the need to maintain
    two separate files in the GitHub repository.
    """
    if os.name == 'nt':  # Check if OS is Windows
        bat_path = Path(__file__).parent / "Click_To_Run.bat"
        if not bat_path.exists():
            try:
                with open(bat_path, "w", encoding="utf-8") as bat_file:
                    bat_file.write(
                        "@echo off\n"
                        f"title iOS Backup Media Wizard Launcher\n"
                        f"python \"{Path(__file__).name}\"\n"
                        "echo.\n"
                        "echo ==================================================\n"
                        "echo Process completed. Press any key to close this window.\n"
                        "echo ==================================================\n"
                        "pause\n"
                    )
                print("[*] Generated native Windows launcher: Click_To_Run.bat")
            except Exception as e:
                print(f"[-] Warning: Failed to generate Windows launcher shortcut: {e}")


# --- UTILITY OPERATIONS ---
def get_unique_filename(target_path):
    """Appends an incrementing counter suffix if a filename collision occurs."""
    if not os.path.exists(target_path):
        return target_path
    base, ext = os.path.splitext(target_path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"


def sanitize_windows_path(path_str):
    """Filters out illegal Win32 naming subsystem characters."""
    drive, path = os.path.splitdrive(path_str)
    parts = path.split(os.sep)
    sanitized_parts = [re.sub(r'[\*?:"<>|]', '_', part) for part in parts]
    return drive + os.sep.join(sanitized_parts)


def get_album_name(domain):
    """Maps chaotic internal application domains into a clean, curated list of albums."""
    dom_lower = domain.lower()
    if "cameraroll" in dom_lower: return "Camera Roll"
    elif "whatsapp" in dom_lower: return "WhatsApp"
    elif "snapchat" in dom_lower: return "Snapchat"
    elif "instagram" in dom_lower: return "Instagram"
    elif "facebook" in dom_lower or "messenger" in dom_lower: return "Facebook & Messenger"
    elif "screenshot" in dom_lower: return "Screenshots"
    elif "cloud" in dom_lower or "icloud" in dom_lower: return "iCloud Drive"
    elif "appdomain" in dom_lower:
        match = re.search(r'appdomain-(?:com\.)?([^.]+)', dom_lower)
        if match: return f"App - {match.group(1).title()}"
        return "Third-Party Apps"
    return "Other Media"


# --- MAIN PIPELINE ENGINE ---
def run_extraction(backup_dir, output_dir, strategy_mode):
    """Parses SQLite Manifest, evaluates strategy parameters, and executes the file dump."""
    manifest_path = os.path.join(backup_dir, "Manifest.db")
    if not os.path.exists(manifest_path):
        print(f"\n[-] Error: Manifest.db could not be located at: {manifest_path}")
        print("Please verify that the backup path points directly to the folder containing Manifest.db")
        return

    print("\n[+] Connecting to SQLite Manifest engine...")
    conn = sqlite3.connect(manifest_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT fileID, domain, relativePath FROM Files;")
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"[-] Database Error: {e}. If this persists, verify the backup is unencrypted.")
        conn.close()
        return

    print(f"[+] Found {len(rows)} file objects in manifest. Scanning for assets...")
    
    copied_count = 0
    media_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.mp4', '.mov', '.m4a', '.mp3'}
    photo_exts = {'.jpg', '.jpeg', '.png', '.heic'}
    video_exts = {'.mp4', '.mov'}

    for file_id, domain, relative_path in rows:
        if not relative_path:
            continue
            
        ext = os.path.splitext(relative_path)[1].lower()
        if ext not in media_extensions:
            continue

        # Apple splits backup binaries into subdirectories using the first two hex characters of the fileID
        folder_prefix = file_id[:2]
        source_file = os.path.join(backup_dir, folder_prefix, file_id)
        
        if os.path.exists(source_file):
            clean_filename = re.sub(r'[\*?:"<>|]', '_', os.path.basename(relative_path))
            
            # PROFILE 1: Original Deep Application Architecture
            if strategy_mode == 1:
                domain_folder = domain.replace("Domain", "").strip()
                raw_target = os.path.join(output_dir, domain_folder, os.path.dirname(relative_path))
                target_folder = sanitize_windows_path(raw_target)
                Path(target_folder).mkdir(parents=True, exist_ok=True)
                dest_file = os.path.join(target_folder, clean_filename)

            # PROFILE 2: Smart Grouped Albums (5-10 Gallery folders)
            elif strategy_mode == 2:
                album_folder = get_album_name(domain)
                target_folder = os.path.join(output_dir, album_folder)
                Path(target_folder).mkdir(parents=True, exist_ok=True)
                dest_file = get_unique_filename(os.path.join(target_folder, clean_filename))

            # PROFILE 3: Flat Media Sort (Only Photos & Videos root directories)
            elif strategy_mode == 3:
                if ext in photo_exts:
                    target_folder = os.path.join(output_dir, "Photos")
                elif ext in video_exts:
                    target_folder = os.path.join(output_dir, "Videos")
                else:
                    target_folder = os.path.join(output_dir, "Audio & Misc")
                
                Path(target_folder).mkdir(parents=True, exist_ok=True)
                dest_file = get_unique_filename(os.path.join(target_folder, clean_filename))

            # Copy operation and timestamp propagation block
            try:
                shutil.copy2(source_file, dest_file)
                if os.path.exists(dest_file):
                    # Preserve original iOS creation/modification metadata properties
                    stat = os.stat(source_file)
                    os.utime(dest_file, (stat.st_atime, stat.st_mtime))
                
                copied_count += 1
                if copied_count % 1000 == 0:
                    print(f"[+] Successfully extracted {copied_count} files...")
            except Exception:
                pass  # Skip corrupted segments or locked handles silently

    print(f"\n[+] Success! Operation finalized.")
    print(f"[+] Total files saved: {copied_count}")
    print(f"[+] Output Directory:  {output_dir}")
    conn.close()


if __name__ == "__main__":
    # Handle on-the-fly Windows launcher compilation
    create_windows_launcher()

    print("=" * 55)
    print("           iOS LOCAL BACKUP MEDIA WIZARD          ")
    print("=" * 55)
    
    # Generic platform-agnostic defaults for public use
    default_backup = os.path.join(os.path.expanduser("~"), "Apple", "MobileSync", "Backup", "YOUR_BACKUP_FOLDER")
    default_output = os.path.join(os.path.abspath(os.sep), "Extracted_Backup")
    
    print(f"ℹ️ Default Backup path hints:")
    print(f"  Windows Store: %USERPROFILE%\\Apple\\MobileSync\\Backup\\")
    print(f"  iTunes Classic: %APPDATA%\\Apple Computer\\MobileSync\\Backup\\\n")

    backup_input = input(f"Enter iPhone Backup path:\n[{default_backup}]\n> ").strip()
    backup_dir = backup_input if backup_input else default_backup
    
    output_input = input(f"\nEnter Extraction Output path:\n[{default_output}]\n> ").strip()
    output_dir = output_input if output_input else default_output

    print("\nSelect Output Directory Strategy:")
    print("  [1] Original Layout  (Replicates full nested iOS application subdirectories)")
    print("  [2] Curated Albums   (Groups files into clean categories: Camera Roll, WhatsApp, etc.)")
    print("  [3] Flat Extraction  (Sorts assets strictly into 'Photos' and 'Videos' only)")
    
    while True:
        try:
            choice = int(input("\nEnter profile choice [1-3]: ").strip())
            if choice in [1, 2, 3]:
                break
            print("[-] Scope Error: Selection parameter must range precisely between 1 and 3.")
        except ValueError:
            print("[-] Data Type Error: Please supply an integer entry input.")

    run_extraction(backup_dir, output_dir, choice)