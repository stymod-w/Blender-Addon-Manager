import bpy
import traceback
from bpy.types import Operator
from bpy.props import IntProperty
from . import common

# --- Operator: Refresh Category List ---
class ADDONMANAGER_OT_refresh_categories(Operator):
    bl_idname = "addonmanager.refresh_categories"
    bl_label = "Refresh Addon Categories"
    bl_description = "Scan for N-Panel categories and update the list"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, "addon_manager_categories")

    def execute(self, context):
        scene = context.scene
        manager_category_name = common.PANEL_CATEGORY
        
        favorites = {}
        favorite_cats = common.load_favorites_from_preferences()
        for cat in favorite_cats:
            favorites[cat] = True

        # --- 1. Reset currently managed panel state ---
        original_categories = common.original_categories
        currently_managed = common.currently_managed_panels

        panels_to_reset = list(currently_managed)
        reset_count = 0
        error_count = 0

        for panel_idname in panels_to_reset:
            if panel_idname in original_categories:
                panel_data = original_categories[panel_idname]
                panel_cls = panel_data['class']
                original_cat = panel_data['original_category']

                if hasattr(bpy.types, panel_idname):
                    registered_cls = getattr(bpy.types, panel_idname)
                    if registered_cls == panel_cls and hasattr(panel_cls, 'bl_category') and panel_cls.bl_category == manager_category_name:
                        try:
                            bpy.utils.unregister_class(panel_cls)
                            panel_cls.bl_category = original_cat
                            bpy.utils.register_class(panel_cls)
                            reset_count += 1
                        except Exception as e:
                            error_count += 1
                else:
                    pass

                currently_managed.discard(panel_idname)
            else:
                currently_managed.discard(panel_idname)

        if reset_count > 0 or error_count > 0:
             print(f"Finished resetting panels: {reset_count} reset, {error_count} errors.")

        # --- 2. Clear old data ---
        category_collection = scene.addon_manager_categories
        category_collection.clear()
        original_categories.clear()
        currently_managed.clear()

        # --- 3. Scan all Panel subclasses ---
        found_categories = set()
        # Get excluded categories from preferences
        core_tabs = common.get_excluded_categories()

        all_panel_classes = []
        def collect_subclasses(cls, collected):
            if isinstance(cls, type):
                if cls is not bpy.types.Panel:
                     if issubclass(cls, bpy.types.Panel):
                         collected.append(cls)
                try:
                    subclasses = cls.__subclasses__()
                    for subcls in subclasses:
                         if isinstance(subcls, type):
                            collect_subclasses(subcls, collected)
                except TypeError:
                     pass

        collect_subclasses(bpy.types.Panel, all_panel_classes)

        registered_panels_count = 0
        skipped_unregistered = 0
        skipped_missing_attr = 0
        skipped_core_tab = 0

        for panel_cls in all_panel_classes:
            required_attrs = ['bl_space_type', 'bl_region_type', 'bl_category','draw']
            if not all(hasattr(panel_cls, attr) for attr in required_attrs):
                skipped_missing_attr += 1
                continue

            if panel_cls.bl_space_type == 'VIEW_3D' and panel_cls.bl_region_type == 'UI':
                category = panel_cls.bl_category
                panel_idname = getattr(panel_cls, 'bl_idname', panel_cls.__name__)
                
                if not category or category in core_tabs:
                    skipped_core_tab += 1
                    continue

                is_registered = True
                if hasattr(panel_cls, 'bl_idname'):
                    if hasattr(bpy.types, panel_cls.bl_idname):
                        registered_cls = getattr(bpy.types, panel_cls.bl_idname)
                        is_registered = (registered_cls == panel_cls)
                    else:
                        is_registered = False
                
                if is_registered:
                    if panel_idname not in original_categories:
                        original_categories[panel_idname] = {
                            'class': panel_cls,
                            'original_category': category
                        }
                        found_categories.add(category)
                        registered_panels_count += 1
                else:
                    skipped_unregistered += 1

        # --- 4. Fill category list UI ---
        sorted_categories = sorted(list(found_categories))
        for cat_name in sorted_categories:
            item = category_collection.add()
            item.name = cat_name
            if cat_name in favorites:
                item.is_favorite = True

        scene.addon_manager_category_index = -1
        currently_managed.clear()

        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        return {'FINISHED'}

# --- Operator: Toggle Favorite Status ---
class ADDONMANAGER_OT_toggle_favorite(Operator):
    bl_idname = "addonmanager.toggle_favorite"
    bl_label = "Toggle Category Favorite"
    bl_description = "Mark or unmark this category as a favorite"
    bl_options = {'REGISTER', 'UNDO'} # UNDO is good practice here

    item_index: IntProperty() # Index of the item to toggle

    @classmethod
    def poll(cls, context):
        # Ensure scene and category collection exist
        return hasattr(context.scene, "addon_manager_categories") and \
               context.scene.addon_manager_categories is not None

    def execute(self, context):
        scene = context.scene
        categories = scene.addon_manager_categories

        # Check if index is valid
        if 0 <= self.item_index < len(categories):
            item = categories[self.item_index]
            # Toggle is_favorite status
            item.is_favorite = not item.is_favorite
            
            # Save favorite status to preferences
            common.save_favorites_to_preferences()
            # Force refresh UI list area if icons don't update immediately
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D': # Or other area type where your panel is
                       area.tag_redraw()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"Invalid item index: {self.item_index}")
            return {'CANCELLED'}

# --- Operator: Scan Available Categories ---
class ADDONMANAGER_OT_scan_available_categories(Operator):
    bl_idname = "addonmanager.scan_available_categories"
    bl_label = "Scan Available Categories"
    bl_description = "Scan all available panel categories"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        from . import preferences, common
        prefs = preferences.get_preferences()
        
        # Clear existing categories
        prefs.available_categories.clear()
        
        # Get current excluded categories
        excluded = common.get_excluded_categories()
        
        # Scan all panel categories
        all_categories = set()
        
        # Collect all panel subclasses
        all_panel_classes = []
        def collect_subclasses(cls, collected):
            if isinstance(cls, type):
                if cls is not bpy.types.Panel:
                    if issubclass(cls, bpy.types.Panel):
                        collected.append(cls)
                try:
                    subclasses = cls.__subclasses__()
                    for subcls in subclasses:
                        if isinstance(subcls, type):
                            collect_subclasses(subcls, collected)
                except TypeError:
                    pass
        
        collect_subclasses(bpy.types.Panel, all_panel_classes)
        
        # Extract all categories
        for panel_cls in all_panel_classes:
            if hasattr(panel_cls, 'bl_space_type') and hasattr(panel_cls, 'bl_region_type') and hasattr(panel_cls, 'bl_category'):
                if panel_cls.bl_space_type == 'VIEW_3D' and panel_cls.bl_region_type == 'UI':
                    category = panel_cls.bl_category
                    if category and category != "":
                        all_categories.add(category)
        
        # Add to available categories list
        manager_category = common.PANEL_CATEGORY
        for cat_name in sorted(all_categories):
            if cat_name == manager_category:
                continue
            item = prefs.available_categories.add()
            item.name = cat_name
            # Set as excluded if in current exclude list
            item.exclude = cat_name in excluded
        
        return {'FINISHED'}

# --- Operator: Apply Excluded Categories Settings ---
class ADDONMANAGER_OT_apply_excluded_categories(Operator):
    bl_idname = "addonmanager.apply_excluded_categories"
    bl_label = "Apply Exclusion Settings"
    bl_description = "Apply selected category exclusion settings"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        from . import preferences
        prefs = preferences.get_preferences()
        
        # Get default excluded categories
        default_excluded = [cat.strip() for cat in prefs.excluded_categories.split(',') if cat.strip()]
        
        # Collect all categories marked for exclusion
        additional_excluded = []
        for item in prefs.available_categories:
            if item.exclude and item.name not in default_excluded:
                additional_excluded.append(item.name)
        
        # Combine default and additional excluded categories
        all_excluded = default_excluded + additional_excluded
        
        # Update internal excluded categories list (without modifying user's default excluded categories)
        from . import common
        common.set_additional_excluded_categories(additional_excluded)
        
        # Refresh category list
        bpy.ops.addonmanager.refresh_categories()
        
        return {'FINISHED'}

# Register class list
classes = (
    ADDONMANAGER_OT_toggle_favorite,
    ADDONMANAGER_OT_refresh_categories,
    ADDONMANAGER_OT_scan_available_categories,
    ADDONMANAGER_OT_apply_excluded_categories,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            pass

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass