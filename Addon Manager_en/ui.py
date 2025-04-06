import bpy
from bpy.types import Panel, UIList
from bpy.app.handlers import persistent
from . import common, preferences, operators

# --- UIList Implementation ---
class ADDONMANAGER_UL_category_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.9) # Try 0.9 or 0.95
            split.label(text=item.name, icon='PLUGIN')

            # Determine icon
            icon_name = 'SOLO_ON' if item.is_favorite else 'SOLO_OFF'

            col_right = split.column(align=True) 
            op = col_right.operator(  
                "addonmanager.toggle_favorite",
                text="",
                icon=icon_name,
                emboss=False
            )
            op.item_index = index

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='PLUGIN')
    
    def filter_items(self, context, data, propname):
        """ Filter and order items in the list """
        items = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        search_term = context.scene.addon_manager_search_term.lower()
        show_only_favs = context.scene.addon_manager_show_favorites_only
        # Initialize filtered list with length matching items
        # Default mark as 0 (or any appropriate value meaning "don't show")
        # Only matching items will be marked with self.bitflag_filter_item
        filtered = [0] * len(items)
        ordered = [] # Sort list will be filled later
        # Filtering
        if search_term or show_only_favs:
            for i, item in enumerate(items):
                # Check favorite status
                is_fav = item.is_favorite

                # If no search term (search_term is empty), name_match is True
                item_name = getattr(item, "name", "").lower()
                name_match = (not search_term or search_term in item_name)

                # --- Decide whether to show this item ---
                show_item = False
                if show_only_favs:
                    # If showing only favorites: must be favorite AND match search term
                    if is_fav and name_match:
                        show_item = True
                else:
                    # If not showing only favorites: just need to match search term
                    if name_match:
                        show_item = True
                # -------------------------

                # If decided to show, set the flag
                if show_item:
                    filtered[i] = self.bitflag_filter_item
        else:
            filtered = [self.bitflag_filter_item] * len(items)

        # Ordering (by name)
        ordered = helper_funcs.sort_items_by_name(items, "name")

        return filtered, ordered

# --- Main Management Panel ---
class ADDONMANAGER_PT_main(Panel):
    bl_label = "Addon Manager"
    bl_idname = "OBJECT_PT_addon_manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = common.PANEL_CATEGORY


    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'VIEW_3D'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # --- 1. Search and Refresh ---
        row = layout.row(align=True)
        row.prop(scene, "addon_manager_search_term", text="", icon='VIEWZOOM')
        row.operator("addonmanager.refresh_categories", text="", icon='FILE_REFRESH')
        # Add hint
        if scene.addon_manager_category_index != -1:
            # Place on same row on the right
            row.label(text="", icon='INFO') # Icon with default tooltip
            # Or show text on next line
            layout.label(text="Refresh to reset view/release addons", icon='INFO')
        # Add settings button, jump to preferences
        show_favs_icon = 'SOLO_ON' if scene.addon_manager_show_favorites_only else 'SOLO_OFF'
        row.prop(
            scene,
            "addon_manager_show_favorites_only",
            text="", # Show icon only
            toggle=True, # Make it look like a toggle button
            icon= show_favs_icon  # Use 'SOLO_ON' icon to match favorite icon
        )
        props = row.operator("preferences.addon_show", text="", icon='PREFERENCES')
        props.module = __package__
        
        # --- 2. Plugin Category List (UIList) ---
        list_box = layout.box()
        # Show total number of plugins
        total_panels = len(scene.addon_manager_categories)
        
        # Get number of excluded categories
        excluded_categories = common.get_excluded_categories()
        excluded_count = len(excluded_categories)
        
        # Calculate total original categories (including excluded)
        original_total = total_panels + excluded_count - 1  # Subtract 1 because manager's own category is also excluded
        
        # Show panel count and exclusion info
        row = list_box.row()
        row.label(text=f"Found {total_panels} categories", icon='PLUGIN')
        

        list_box.template_list(
            "ADDONMANAGER_UL_category_list",
            "",
            scene,
            "addon_manager_categories",
            scene,
            "addon_manager_category_index",
            rows=4,
        )

        # --- 3. Information Area ---
        layout.separator()
        info_box = layout.box()
        selected_category_name = ""
        if 0 <= scene.addon_manager_category_index < len(scene.addon_manager_categories):
             selected_category_name = scene.addon_manager_categories[scene.addon_manager_category_index].name

        if selected_category_name:
            info_box.label(text=f"Showing addons from: '{selected_category_name}'", icon='INFO')
        else:
            info_box.label(text="View panels here - Refresh button to release addons.", icon='INFO')

# Restore panels function - called before unregistering addon
def restore_panels(force=False):

    if not force and not common.should_auto_restore('exit'):
        return
    
    panels_to_restore = list(common.currently_managed_panels)
    restored_count = 0
    error_count = 0
    for panel_idname in panels_to_restore:
        try:
            if panel_idname in common.original_categories:
                panel_cls = common.original_categories[panel_idname]['class']
                original_cat = common.original_categories[panel_idname]['original_category']
                
                # Check if it's actually under manager category
                if hasattr(panel_cls, 'bl_category') and panel_cls.bl_category == common.PANEL_CATEGORY:
                    try:
                        bpy.utils.unregister_class(panel_cls)
                        panel_cls.bl_category = original_cat
                        bpy.utils.register_class(panel_cls)
                        restored_count += 1
                    except Exception as e:
                        print(f"Error restoring panel {panel_idname}: {e}")
                        error_count += 1
                else:
                    pass
            else:
                pass
        except Exception as e:
            print(f"Unexpected error processing panel {panel_idname}: {e}")
            error_count += 1
    common.currently_managed_panels.clear()
    
    print(f"Panel restoration complete: {restored_count} restored, {error_count} errors")


# Add handler functions
@persistent
def load_handler(dummy):
    """Handler for new file load"""
    # Check if auto-restore should be performed on new file
    if common.should_auto_restore('new_file'):
        restore_panels(force=True)
    else:
        pass

@persistent
def save_handler(dummy):
    """Handler for file save - can be used to save state"""
    # Add code to save state here
    pass

@persistent
def exit_handler(dummy=None):
    """Handler for Blender exit
    
    Args:
        dummy: Optional parameter passed when called from bpy.app.handlers
    """
    restore_panels(force=True)  # Force restore to ensure cleanup


# Register class list
classes = (
    ADDONMANAGER_UL_category_list,
    ADDONMANAGER_PT_main,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            print(f"Warning: Could not register class {cls.__name__}: {e}")
    # Register handlers
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.save_pre.append(save_handler)

    
    # Register exit handler
    try:
        import atexit
        atexit.register(exit_handler)
    except ImportError:
        print("Could not register exit handler")

def unregister():
    # Restore panels first
    restore_panels(force=True)
    
    # Remove handlers
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    if save_handler in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(save_handler)
    
    # Unregister classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    
    # Try to remove exit handler
    try:
        import atexit
        atexit.unregister(exit_handler)
    except (ImportError, AttributeError):
        pass