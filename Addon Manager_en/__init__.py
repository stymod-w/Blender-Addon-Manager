bl_info = {
    "name": "Addon Manager",
    "author": "stymod",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Addon Mgr",
    "description": "Manage and organize N-panel addons",
    "category": "Interface",
}

import bpy
from . import common, properties, operators, ui, preferences


func_list = [
    properties, 
    operators, 
    ui, 
    preferences,
    ]

def register():
    for func in func_list:
        func.register()
    
    # Load additional excluded categories from preferences
    from . import common
    common.load_additional_excluded_from_preferences()
    # Deferred refresh
    def deferred_refresh():
        try:
            # First scan available categories
            bpy.ops.addonmanager.scan_available_categories()
            bpy.ops.addonmanager.apply_excluded_categories()

            bpy.ops.addonmanager.refresh_categories()
        except Exception as e:
            print(f"Error during initial category refresh: {e}")
        return None
    
    bpy.app.timers.register(deferred_refresh, first_interval=0.1)

def unregister():
    # Restore panels first
    ui.restore_panels(force=True)
    
    # Then unregister modules
    for func in reversed(func_list):
        func.unregister()

# For testing only
if __name__ == "__main__":
    register()