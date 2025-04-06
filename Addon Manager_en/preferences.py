import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty, EnumProperty, CollectionProperty,IntProperty


# Add category item type
class ADDONMANAGER_CategoryExcludeItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Category Name")
    exclude: BoolProperty(
        name="Exclude",
        description="Exclude this category from the addon manager",
        default=False
    )
# Addon preferences
class ADDONMANAGER_preferences(AddonPreferences):
    bl_idname = __package__  # Use package name as ID


    favorite_categories: StringProperty(
        name="Favorite Categories",
        description="List of favorite categories, separated by commas",
        default=""
    )
    
    auto_restore_on_exit: BoolProperty(
        name="Auto-restore panels on exit",
        description="Automatically restore panels to their original categories when closing Blender or opening a new file",
        default=True
    )

    auto_restore_on_new_file: BoolProperty(
        name="Auto-restore panels on new file (recommended)",
        description="Automatically restore panels to their original categories when opening a new file",
        default=True
    )
    
    excluded_categories: StringProperty(
        name="Default excluded categories (not recommended to modify)",
        description="Base categories that are always excluded, separated by commas",
        default="Item,Tool,View,Create,Relations,Edit,Physics,Grease Pencil"
    )
    additional_excluded_categories: StringProperty(
        name="Additional excluded categories",
        description="Additional categories excluded through UI selection",
        default=""
    )
    # Add properties for UI display control
    show_category_list: BoolProperty(
        name="Show Category List",
        description="Expand/collapse category list",
        default=False
    )
    
    columns_count: IntProperty(
        name="Columns",
        description="Number of columns to display in the category list",
        default=3,
        min=1,
        max=5
    )
    available_categories: CollectionProperty(type=ADDONMANAGER_CategoryExcludeItem)


    def draw(self, context):
        layout = self.layout
        
        # Notice section
        box = layout.box()
        box.label(text="Important Notice", icon='ERROR')
        box.label(text="1. This addon will change the display order of plugins in the N-panel")
        box.label(text="2. Managed plugins will be hidden from their original N-panel location")
        box.label(text="Please be aware of these behaviors!", icon='INFO')
        
        layout.separator()

        # Add auto-restore options
        box = layout.box()
        box.label(text="Auto-restore Settings:", icon='RECOVER_LAST')
        box.prop(self, "auto_restore_on_new_file")
        layout.separator()
        
        # Category exclusion settings
        box = layout.box()
        box.label(text="Category Exclusion Settings:", icon='FILTER')
        
        # Default excluded categories (text input)
        box.prop(self, "excluded_categories")
        box.label(text="Default excluded categories (comma-separated, not recommended to modify)", icon='INFO')
        

        # Scan button
        row = box.row()
        row.operator("addonmanager.scan_available_categories", 
                    text="Scan Available Categories", icon='FILE_REFRESH')
        row.label(text="Click after initialization or plugin updates", icon='ERROR')
        # Collapse/expand button
        row = box.row()
        row.prop(self, "show_category_list", 
                 icon='TRIA_DOWN' if self.show_category_list else 'TRIA_RIGHT',
                 text="Other Excludable Categories" if not self.show_category_list else "Other Excludable Categories (Click to collapse)")
        
        # Column settings
        if self.show_category_list:
            row.prop(self, "columns_count", text="Columns")
        

        
        # Display selectable category list (only when expanded)
        if self.show_category_list and len(self.available_categories) > 0:
            # Calculate items per column
            total_items = len(self.available_categories)
            items_per_column = max(1, total_items // self.columns_count + (1 if total_items % self.columns_count else 0))
            
            # Create multi-column layout
            box.label(text="Click to select additional categories to exclude:")
            row = box.row()
            
            # Get default excluded categories list
            default_excluded = [cat.strip() for cat in self.excluded_categories.split(',') if cat.strip()]
            
            # Create a column layout for each column
            for col_idx in range(self.columns_count):
                if col_idx * items_per_column >= total_items:
                    break
                    
                col = row.column()
                for i in range(items_per_column):
                    item_idx = col_idx * items_per_column + i
                    if item_idx < total_items:
                        item = self.available_categories[item_idx]
                        # Don't display if category is in default excluded list
                        if item.name not in default_excluded:
                            item_row = col.row()
                            item_row.prop(item, "exclude", text=item.name)
            
            # Apply button
            row = box.row()
            row.operator("addonmanager.apply_excluded_categories", 
                         text="Apply Exclusion Settings", icon='CHECKMARK')
        elif self.show_category_list:
            box.label(text="Please scan available categories first", icon='INFO')

        # Add favorite categories settings
        box = layout.box()
        box.label(text="Favorite Settings", icon='SOLO_ON')
        box.prop(self, "favorite_categories")
        box.label(text="Favorite categories (comma-separated)", icon='INFO')

# Helper function to get addon preferences
def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences

# Register class list
classes = (
    ADDONMANAGER_CategoryExcludeItem,
    ADDONMANAGER_preferences,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            print(f"Warning: Could not register class {cls.__name__}: {e}")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass