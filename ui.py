import bpy
from bpy.types import Panel, UIList
from bpy.app.handlers import persistent
from . import common, preferences, operators, translations

# --- UIList 实现 ---
class ADDONMANAGER_UL_category_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.9) # 尝试 0.9 或 0.95
            split.label(text=item.name, icon='PLUGIN')

            # 先确定图标
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
        # 初始化 filtered 列表，长度与 items 相同
        # 默认标记为 0 (或表示“不显示”的任何适当值)
        # 只有匹配的项才会被标记为 self.bitflag_filter_item
        filtered = [0] * len(items)
        ordered = [] # 排序列表将在后面填充
        # Filtering
        if search_term or show_only_favs:
            for i, item in enumerate(items):
                # 检查收藏状态
                is_fav = item.is_favorite

                # 如果没有搜索词 (search_term 为空)，则 name_match 为 True
                item_name = getattr(item, "name", "").lower()
                name_match = (not search_term or search_term in item_name)

                # --- 决定是否显示该项 ---
                show_item = False
                if show_only_favs:
                    # 如果只显示收藏：必须是收藏项 AND 匹配搜索词
                    if is_fav and name_match:
                        show_item = True
                else:
                    # 如果不只显示收藏：只需要匹配搜索词
                    if name_match:
                        show_item = True
                # -------------------------

                # 如果决定显示，则设置标志位
                if show_item:
                    filtered[i] = self.bitflag_filter_item
        else:
            filtered = [self.bitflag_filter_item] * len(items)

        # Ordering (by name)
        ordered = helper_funcs.sort_items_by_name(items, "name")

        return filtered, ordered

# --- 主管理面板 ---
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


        
        # --- 1. 搜索和刷新 ---
        row = layout.row(align=True)
        row.prop(scene, "addon_manager_search_term", text="", icon='VIEWZOOM')
        row.operator("addonmanager.refresh_categories", text="", icon='FILE_REFRESH')
        # 添加提示
        if scene.addon_manager_category_index != -1:
            # 放在按钮同行右侧
            row.label(text="", icon='INFO') # 图标带默认 tooltip
            # 或者在下一行显示文字
            layout.label(text=translations.get_text("刷新来重置视图/释放插件"), icon='INFO')
        # 添加设置按钮，跳转到偏好设置
        show_favs_icon = 'SOLO_ON' if scene.addon_manager_show_favorites_only else 'SOLO_OFF'
        row.prop(
            scene,
            "addon_manager_show_favorites_only",
            text="", # 只显示图标
            toggle=True, # 让它看起来像个切换按钮
            icon= show_favs_icon  # 使用 'SOLO_ON' 图标，和收藏图标一致
        )
        props = row.operator("preferences.addon_show", text="", icon='PREFERENCES')
        props.module = __package__
        
        # --- 2. 插件类别列表 (UIList) ---
        list_box = layout.box()
        # 显示插件总数
        total_panels = len(scene.addon_manager_categories)
        
        # 获取排除的类别数量
        excluded_categories = common.get_excluded_categories()
        excluded_count = len(excluded_categories)
        
        # 计算原始类别总数（包括排除的）
        original_total = total_panels + excluded_count - 1  # 减1是因为管理器自身的类别也被排除了
        
        # 显示面板数量和排除信息
        row = list_box.row()
        row.label(text=translations.get_text("共找到{} 个").format(total_panels), icon='PLUGIN')
        

        list_box.template_list(
            "ADDONMANAGER_UL_category_list",
            "",
            scene,
            "addon_manager_categories",
            scene,
            "addon_manager_category_index",
            rows=4,
        )

        # --- 3. 信息区域 ---
        layout.separator()
        info_box = layout.box()
        selected_category_name = ""
        if 0 <= scene.addon_manager_category_index < len(scene.addon_manager_categories):
             selected_category_name = scene.addon_manager_categories[scene.addon_manager_category_index].name

        if selected_category_name:
            info_box.label(text=translations.get_text("显示插件: '{}'").format(selected_category_name), icon='INFO')
            #info_box.label(text=f"({len(common.currently_managed_panels)} panels managed)")
        else:
            info_box.label(text=translations.get_text("在此处查看其面板_刷新按钮释放插件."), icon='INFO')

# 恢复面板函数 - 在注销插件前调用
def restore_panels(force=False):

    if not force and not common.should_auto_restore('exit'):
        #print("Auto restore disabled in preferences, skipping...")
        return
    #print("Restoring managed panels to their original categories...")
    
    panels_to_restore = list(common.currently_managed_panels)
    restored_count = 0
    error_count = 0
    for panel_idname in panels_to_restore:
        try:
            if panel_idname in common.original_categories:
                panel_cls = common.original_categories[panel_idname]['class']
                original_cat = common.original_categories[panel_idname]['original_category']
                
                # 检查它是否真的在管理类别下
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
                #print(f"Warning: Cannot find original data for panel {panel_idname}")
        except Exception as e:
            print(f"Unexpected error processing panel {panel_idname}: {e}")
            error_count += 1
    common.currently_managed_panels.clear()
    
    print(f"Panel restoration complete: {restored_count} restored, {error_count} errors")


# 添加处理器函数
@persistent
def load_handler(dummy):
    """新文件加载时的处理器"""
    # 检查是否应该在新文件时自动恢复
    if common.should_auto_restore('new_file'):
        #print("New file detected, auto-restoring panels...")
        restore_panels(force=True)
    else:
        pass

@persistent
def save_handler(dummy):
    """文件保存时的处理器 - 可以用于保存状态"""
    # 这里可以添加保存状态的代码
    pass

@persistent
def exit_handler(dummy=None):
    """Blender退出时的处理器
    
    Args:
        dummy: 可选参数，当从 bpy.app.handlers 调用时会传入
    """
    #print("Blender is closing, running cleanup...")
    restore_panels(force=True)  # 强制恢复，确保清理


# 注册类列表
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
    # 注册处理器
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.save_pre.append(save_handler)

    
    # 注册退出处理器
    try:
        import atexit
        atexit.register(exit_handler)
    except ImportError:
        print("Could not register exit handler")

def unregister():
    # 先恢复面板
    restore_panels(force=True)
    
    # 移除处理器
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    if save_handler in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(save_handler)
    
    # 注销类
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    
    # 尝试移除退出处理器
    try:
        import atexit
        atexit.unregister(exit_handler)
    except (ImportError, AttributeError):
        pass