import bpy

# Shared constants
ADDON_NAME = "Addon Manager"
PANEL_CATEGORY = "Addon Mgr"

# Store original categories and currently managed panels
original_categories = {}
currently_managed_panels = set()

# Shared functions
def update_managed_panels(self, context):
    """Update panel bl_category when category selection changes"""
    print("Category selection changed, updating managed panels...")
    scene = context.scene
    
    # Get target category (manager panel category)
    target_category = PANEL_CATEGORY
    
    selected_category_name = ""
    if 0 <= scene.addon_manager_category_index < len(scene.addon_manager_categories):
        selected_category_name = scene.addon_manager_categories[scene.addon_manager_category_index].name

    panels_to_make_visible = set()
    if selected_category_name:
        # Find all panel IDs whose original category matches the selected category
        for pid, data in original_categories.items():
            if data['original_category'] == selected_category_name:
                panels_to_make_visible.add(pid)

    panels_to_hide = currently_managed_panels - panels_to_make_visible
    panels_to_show = panels_to_make_visible - currently_managed_panels

    # Hide panels that are no longer needed (restore original category)
    for panel_idname in panels_to_hide:
        if panel_idname in original_categories:
            panel_cls = original_categories[panel_idname]['class']
            original_cat = original_categories[panel_idname]['original_category']
            try:
                bpy.utils.unregister_class(panel_cls)
                panel_cls.bl_category = original_cat
                bpy.utils.register_class(panel_cls)
            except Exception as e:
                pass
        else:
             print(f"Warning: Cannot find original data for panel {panel_idname} to hide.")

    # Show newly selected panels (set target category)
    for panel_idname in panels_to_show:
         if panel_idname in original_categories:
            panel_cls = original_categories[panel_idname]['class']
            try:
                bpy.utils.unregister_class(panel_cls)
                panel_cls.bl_category = target_category
                bpy.utils.register_class(panel_cls)
            except Exception as e:
                pass
         else:
             print(f"Warning: Cannot find original data for panel {panel_idname} to show.")

    # Update currently managed panels set
    currently_managed_panels.clear()
    currently_managed_panels.update(panels_to_make_visible)

    # Request UI refresh
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                break

# Function to get excluded categories
def get_excluded_categories():
    """Get list of excluded categories from preferences"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs and hasattr(prefs, "excluded_categories"):
            # Split string and remove whitespace
            categories = [cat.strip() for cat in prefs.excluded_categories.split(',') if cat.strip()]
            # Ensure manager's own category is also excluded
            if PANEL_CATEGORY not in categories:
                categories.append(PANEL_CATEGORY)
            return set(categories)
    except Exception as e:
        print(f"Error getting excluded categories: {e}")
    
    # Default excluded categories
    return {"Item", "Tool", "View", "Create", "Relations", "Edit", 
            "Physics", "Grease Pencil", PANEL_CATEGORY, "Unknown"}

# Function to check if auto-restore should be performed
def should_auto_restore(restore_type='exit'):
    """Check if panels should be auto-restored
    
    Args:
        restore_type: 'exit' or 'new_file'
    
    Returns:
        bool: Whether auto-restore should be performed
    """
    try:
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs:
            if restore_type == 'exit':
                return prefs.auto_restore_on_exit
            elif restore_type == 'new_file':
                return prefs.auto_restore_on_new_file
    except Exception as e:
        print(f"Error checking auto restore setting: {e}")
        # Default to restore on error, safer
        return True
    
    return True  # Default behavior is to restore

# --- Update functions (placed before register_properties) ---
def update_list_filter(self, context):
    """ Simple update function to redraw areas containing the list """
    # Force UI refresh (cover all windows and areas that might contain the list)
    # This is a general approach to ensure UI updates
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()

def save_favorites_to_preferences():
    """Save current favorite status to addon preferences"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        scene = bpy.context.scene
        
        if prefs and hasattr(scene, "addon_manager_categories"):
            # Collect all favorite categories
            favorite_cats = []
            for item in scene.addon_manager_categories:
                if item.is_favorite:
                    favorite_cats.append(item.name)
            
            # Save to preferences
            prefs.favorite_categories = ",".join(favorite_cats)
    except Exception as e:
        print(f"Error saving favorite categories: {e}")

def load_favorites_from_preferences():
    """Load favorite status from addon preferences"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        scene = bpy.context.scene
        
        if prefs and hasattr(prefs, "favorite_categories") and hasattr(scene, "addon_manager_categories"):
            # Parse favorite categories list
            favorite_cats = [cat.strip() for cat in prefs.favorite_categories.split(',') if cat.strip()]
            
            # Apply to current category list
            updated_count = 0
            for item in scene.addon_manager_categories:
                if item.name in favorite_cats:
                    item.is_favorite = True
                    updated_count += 1
            
            return favorite_cats
    except Exception as e:
        print(f"Error loading favorite categories: {e}")
    
    return []

# Store additional excluded categories
_additional_excluded_categories = []

def set_additional_excluded_categories(categories):
    """Set list of additional excluded categories"""
    global _additional_excluded_categories
    # Ensure PANEL_CATEGORY (Addon Mgr's own category) won't be removed
    _additional_excluded_categories = [cat for cat in categories if cat != PANEL_CATEGORY]
    # Ensure PANEL_CATEGORY is always in the excluded list
    if PANEL_CATEGORY not in _additional_excluded_categories:
        _additional_excluded_categories.append(PANEL_CATEGORY)
    
    # Save to preferences
    save_additional_excluded_to_preferences()

def get_additional_excluded_categories():
    """Get list of additional excluded categories"""
    global _additional_excluded_categories
    return _additional_excluded_categories

def save_additional_excluded_to_preferences():
    """Save additional excluded categories to preferences"""
    try:
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs:
            # Convert additional excluded categories list to comma-separated string
            prefs.additional_excluded_categories = ",".join(_additional_excluded_categories)
    except Exception as e:
        print(f"Error saving additional excluded categories: {e}")

def load_additional_excluded_from_preferences():
    """Load additional excluded categories from preferences"""
    global _additional_excluded_categories
    try:
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs and hasattr(prefs, "additional_excluded_categories"):
            # Split string and remove whitespace
            _additional_excluded_categories = [cat.strip() for cat in prefs.additional_excluded_categories.split(',') if cat.strip()]
            # Ensure PANEL_CATEGORY is always in the excluded list
            if PANEL_CATEGORY not in _additional_excluded_categories:
                _additional_excluded_categories.append(PANEL_CATEGORY)
    except Exception as e:
        print(f"Error loading additional excluded categories: {e}")

def get_excluded_categories():
    """Get list of excluded categories from preferences"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs and hasattr(prefs, "excluded_categories"):
            # Split string and remove whitespace
            categories = [cat.strip() for cat in prefs.excluded_categories.split(',') if cat.strip()]
            # Add additional excluded categories
            categories.extend([cat for cat in get_additional_excluded_categories() if cat not in categories])
            # Ensure manager's own category is also excluded
            if PANEL_CATEGORY not in categories:
                categories.append(PANEL_CATEGORY)
            return set(categories)
    except Exception as e:
        print(f"Error getting excluded categories: {e}")
    
    # Default excluded categories
    return {"Item", "Tool", "View", "Create", "Relations", "Edit", 
            "Physics", "Grease Pencil", PANEL_CATEGORY, "Unknown"}