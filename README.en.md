[简体中文](./README.md) | English
# Blender Addon Manager
> This project was developed with AI assistance, with human oversight and refinements.

## Introduction
A tool for managing and organizing Blender N-panel addons.

Pain point: When there are too many N-panel addons in Blender, they become difficult to manage and find. The vertical layout causes neck strain, and there's no quick navigation function.

## Features

1. **Centralized Panel Management**
   - Consolidate addon panels scattered across N-panel categories into a unified interface

   - Quickly switch between different addon panels by selecting categories

   - Reduce N-panel clutter and improve workspace organization

2. **Category Filtering and Exclusion**
   - Search for categories

   - Set excluded categories to hide rarely used panels

   - Flexibly select additional categories to exclude through the Preferences

3. **Favorites Function**
   - Mark commonly used categories as favorites

   - Quick filter to show only favorite categories


4. **Auto-restore Function**
   - Automatically restore panels to their original positions when opening new files

   - Automatically clean up and restore all panels when closing Blender

   - Customize auto-restore behavior in preferences

## Important Notes!!!

- **Using this addon will affect the display order of addons in the N-panel**

- **Managed addons will be hidden from their original N-panel location when in use**

## Installation

1. Download the ZIP file
2. In Blender, go to Edit > Preferences > Add-ons > Install
3. Select the downloaded ZIP file
4. Enable the addon

## Usage Instructions

### Basic Usage

1. The addon is located in the "Addon Mgr" tab in the 3D View sidebar (N-panel)

2. Enter keywords in the search box to filter categories

3. Click on a category name to load all its panels under Addon Mgr

4. Click the refresh button to rescan and reload categories

5. Click the star icon to add categories to favorites

6. Click the "Show Favorites Only" button to filter and show only favorite categories

    ![n-panel](https://github.com/user-attachments/assets/9a275dbe-5d4d-490d-a17a-3d9af6334aaf)

### Preferences

The following options can be configured in the addon preferences:

1. **Auto-restore Settings**
   - Control whether panels automatically restore when opening new files

2. **Category Exclusion Settings**
   - Set default excluded categories

   - Scan and select additional categories to exclude

3. **Favorites Settings**
   - Manage the list of favorite categories

    ![preferences](https://github.com/user-attachments/assets/07907e3a-5ee9-4dd1-87b9-6004bdabdc04)

## Version History

- v0.1.0: Initial Release
  - Implemented basic panel management functionality
  - Added category filtering and favorites features
  - Implemented auto-restore mechanism