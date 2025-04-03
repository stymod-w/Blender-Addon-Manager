import bpy
import traceback
from bpy.types import Operator
from bpy.props import IntProperty
from . import common

# --- 操作符：刷新类别列表 ---
class ADDONMANAGER_OT_refresh_categories(Operator):
    bl_idname = "addonmanager.refresh_categories"
    bl_label = "Refresh Addon Categories"
    bl_description = "Scan for N-Panel categories and update the list"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, "addon_manager_categories")

    def execute(self, context):
        #print("Refreshing Addon Categories and Panel Registry...")
        scene = context.scene
        manager_category_name = common.PANEL_CATEGORY
        
        favorites = {}
        favorite_cats = common.load_favorites_from_preferences()
        for cat in favorite_cats:
            favorites[cat] = True

        # --- 1. 重置当前管理的面板状态 ---
        #print("Resetting currently managed panels...")
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
                            #print(f"Error resetting panel {panel_idname}: {e}")
                            error_count += 1
                else:
                    pass

                currently_managed.discard(panel_idname)
            else:
                #print(f"Warning: Cannot find original data for panel {panel_idname} during reset. Removing from tracking.")
                currently_managed.discard(panel_idname)

        if reset_count > 0 or error_count > 0:

             print(f"Finished resetting panels: {reset_count} reset, {error_count} errors.")

        # --- 2. 清空旧数据 ---
        category_collection = scene.addon_manager_categories
        category_collection.clear()
        original_categories.clear()
        currently_managed.clear()

        #print("Cleared old categories and panel registry.")

        # --- 3. 扫描所有 Panel 子类 ---
        found_categories = set()
        # 从偏好设置中获取排除类别
        core_tabs = common.get_excluded_categories()
        #print(f"Using excluded categories from preferences: {core_tabs}")

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
        #print(f"Scanning {len(all_panel_classes)} potential panel classes...")

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

        #print(f"Scan complete: Found {len(found_categories)} valid categories.")
        #print(f"Registered {registered_panels_count} relevant panels.")
        #print(f"Skipped: {skipped_unregistered} (unregistered/mismatch), {skipped_missing_attr} (missing attrs), {skipped_core_tab} (core/empty category)")

        # --- 4. 填充类别列表 UI ---
        sorted_categories = sorted(list(found_categories))
        for cat_name in sorted_categories:
            item = category_collection.add()
            item.name = cat_name
            if cat_name in favorites:
                item.is_favorite = True

        scene.addon_manager_category_index = -1
        currently_managed.clear()

        #print("Refresh complete.")
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        return {'FINISHED'}

# --- 操作符：切换收藏状态 ---
class ADDONMANAGER_OT_toggle_favorite(Operator):
    bl_idname = "addonmanager.toggle_favorite"
    bl_label = "Toggle Category Favorite"
    bl_description = "Mark or unmark this category as a favorite"
    bl_options = {'REGISTER', 'UNDO'} # UNDO is good practice here

    item_index: IntProperty() # 接收要切换的项的索引

    @classmethod
    def poll(cls, context):
        # 确保场景和类别集合存在
        return hasattr(context.scene, "addon_manager_categories") and \
               context.scene.addon_manager_categories is not None

    def execute(self, context):
        scene = context.scene
        categories = scene.addon_manager_categories

        # 检查索引是否有效
        if 0 <= self.item_index < len(categories):
            item = categories[self.item_index]
            # 切换 is_favorite 状态
            item.is_favorite = not item.is_favorite
            #print(f"Toggled favorite for '{item.name}' to {item.is_favorite}")
            
            # 保存收藏状态到偏好设置
            common.save_favorites_to_preferences()
            # 可能需要强制刷新UI列表区域（如果图标没有立即更新）
            # 尝试找到包含这个列表的区域并标记重绘
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D': # 或者你的面板所在的其他区域类型
                       area.tag_redraw()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"Invalid item index: {self.item_index}")
            return {'CANCELLED'}

# --- 操作符：扫描可用类别 ---
class ADDONMANAGER_OT_scan_available_categories(Operator):
    bl_idname = "addonmanager.scan_available_categories"
    bl_label = "扫描可用类别"
    bl_description = "扫描所有可用的面板类别"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        from . import preferences, common
        prefs = preferences.get_preferences()
        
        # 清空现有类别
        prefs.available_categories.clear()
        
        # 获取当前排除的类别
        excluded = common.get_excluded_categories()
        
        # 扫描所有面板类别
        all_categories = set()
        
        # 收集所有面板子类
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
        
        # 提取所有类别
        for panel_cls in all_panel_classes:
            if hasattr(panel_cls, 'bl_space_type') and hasattr(panel_cls, 'bl_region_type') and hasattr(panel_cls, 'bl_category'):
                if panel_cls.bl_space_type == 'VIEW_3D' and panel_cls.bl_region_type == 'UI':
                    category = panel_cls.bl_category
                    if category and category != "":
                        all_categories.add(category)
        
        # 添加到可用类别列表
        manager_category = common.PANEL_CATEGORY
        for cat_name in sorted(all_categories):
            if cat_name == manager_category:
                continue
            item = prefs.available_categories.add()
            item.name = cat_name
            # 如果在当前排除列表中，则设置为排除
            item.exclude = cat_name in excluded
        
        #self.report({'INFO'}, f"已扫描到 {len(all_categories)} 个类别")
        return {'FINISHED'}

# --- 操作符：应用排除类别设置 ---
class ADDONMANAGER_OT_apply_excluded_categories(Operator):
    bl_idname = "addonmanager.apply_excluded_categories"
    bl_label = "应用排除设置"
    bl_description = "应用选择的排除类别设置"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        from . import preferences
        prefs = preferences.get_preferences()
        
        # 获取默认排除的类别
        default_excluded = [cat.strip() for cat in prefs.excluded_categories.split(',') if cat.strip()]
        
        # 收集所有被标记为排除的类别
        additional_excluded = []
        for item in prefs.available_categories:
            if item.exclude and item.name not in default_excluded:
                additional_excluded.append(item.name)
        
        # 合并默认排除和额外排除的类别
        all_excluded = default_excluded + additional_excluded
        
        # 更新内部使用的排除类别列表（不修改用户输入的默认排除类别）
        from . import common
        common.set_additional_excluded_categories(additional_excluded)
        
        # 刷新类别列表
        bpy.ops.addonmanager.refresh_categories()
        
        #self.report({'INFO'}, f"已应用 {len(all_excluded)} 个排除类别")
        return {'FINISHED'}

# 注册类列表
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
            #print(f"Warning: Could not register class {cls.__name__}: {e}")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass