# iOS Local Backup Media Wizard

An interactive python utility to automatically extract, structure, and rebuild media assets locked inside unencrypted local iOS backups on Windows machines.

## Features
* **Timestamp Preservation:** Explicitly reconstructs the file system metadata (`creation_time` and `modification_time`) onto the target machine, aligning assets chronologically for easy viewing.
* **Three Flexible Sorting Profiles:** 
	1. Recreate the full deep application directory pathing (Orignal IOS).
	2. Map file targets to a curated 5-10 folder gallery scheme (Camera Roll, WhatsApp, Instagram, etc.).
	3. Sort purely down into a flat architecture consisting only of root `Photos` and `Videos` folders.
* **Automatic File De-confliction:** Handles filename collisions transparently by checking system targets dynamically before extraction.

## Requirements
* Python 3.x

## How To Run
	1. Download `media_wizard.py` to your desired working directory.
	2. If running on Windows, execute the script once or double-click it. It will automatically generate a localized `Click_To_Run.bat` executable inside the same folder.
	3. Launch the script, follow the on-screen configuration prompts, and select your structural sorting strategy.
		1. Add backup path
		2. Add extraction path
		3. Choose Extraction type

## Note
	1. Usually backup location Of Apple Devices/ Itunes is "C:\Users\%USERPROFILE%\Apple\MobileSync\Backup\(your backup id)"
	2. In case to terminate process press (CTRL+C)
	
