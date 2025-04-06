import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, CollectionProperty,BoolProperty
from . import common

# --- 列表项数据结构 ---
class ADDONMANAGER_CategoryItem(PropertyGroup):
    name: StringProperty(name="Category Name")
    is_favorite: BoolProperty(
        name="Is Favorite",
        description="Mark this category as a favorite",
        default=False
    )

# --- 属性注册/注销 ---
def register_properties():
    bpy.types.Scene.addon_manager_search_term = StringProperty(
        name="Search",
        description="Filter addon categories by name",
        default="",
        
        update=common.update_list_filter # 也让搜索框触发更新
    )
    bpy.types.Scene.addon_manager_categories = CollectionProperty(type=ADDONMANAGER_CategoryItem)
    bpy.types.Scene.addon_manager_category_index = IntProperty(
        name="Selected Category Index",
        default=-1,
        update=common.update_managed_panels
    )
    bpy.types.Scene.addon_manager_show_favorites_only = BoolProperty(
        name="Show Favorites Only",
        description="Filter the list to show only favorite categories",
        default=False,
        update=common.update_list_filter # 使用相同的更新函数
    )

def unregister_properties():
    props_to_delete = [
        "addon_manager_search_term",
        "addon_manager_categories",
        "addon_manager_category_index",
        "addon_manager_show_favorites_only", 
    ]
    for prop in props_to_delete:
        try:
            if hasattr(bpy.types.Scene, prop):
                delattr(bpy.types.Scene, prop)
        except Exception as e:
            print(f"Error unregistering property {prop}: {e}")

# 注册类列表
classes = (
    ADDONMANAGER_CategoryItem,
)

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            print(f"Warning: Could not register class {cls.__name__}: {e}")
    
    register_properties()

def unregister():
    unregister_properties()
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass