import bpy

# 共享常量
ADDON_NAME = "Addon Manager"
PANEL_CATEGORY = "Addon Mgr"

# 存储原始类别和当前管理的面板
original_categories = {}
currently_managed_panels = set()

# 共享函数
def update_managed_panels(self, context):
    """当类别选择变化时，更新面板的 bl_category"""
    print("Category selection changed, updating managed panels...")
    scene = context.scene
    
    # 获取目标类别（管理器面板的类别）
    target_category = PANEL_CATEGORY
    
    selected_category_name = ""
    if 0 <= scene.addon_manager_category_index < len(scene.addon_manager_categories):
        selected_category_name = scene.addon_manager_categories[scene.addon_manager_category_index].name

    panels_to_make_visible = set()
    if selected_category_name:
        # 查找所有原始类别是选中类别的面板 ID
        for pid, data in original_categories.items():
            if data['original_category'] == selected_category_name:
                panels_to_make_visible.add(pid)

    panels_to_hide = currently_managed_panels - panels_to_make_visible
    panels_to_show = panels_to_make_visible - currently_managed_panels

    # 隐藏不再需要的面板 (恢复原始类别)
    for panel_idname in panels_to_hide:
        if panel_idname in original_categories:
            panel_cls = original_categories[panel_idname]['class']
            original_cat = original_categories[panel_idname]['original_category']
            try:
                bpy.utils.unregister_class(panel_cls)
                panel_cls.bl_category = original_cat
                bpy.utils.register_class(panel_cls)
                #print(f"Moved panel {panel_idname} back to category '{original_cat}'")
            except Exception as e:
                pass
                #print(f"Error moving panel {panel_idname} back: {e}")
        else:
             print(f"Warning: Cannot find original data for panel {panel_idname} to hide.")

    # 显示新选中的面板 (设置目标类别)
    for panel_idname in panels_to_show:
         if panel_idname in original_categories:
            panel_cls = original_categories[panel_idname]['class']
            try:
                bpy.utils.unregister_class(panel_cls)
                panel_cls.bl_category = target_category
                bpy.utils.register_class(panel_cls)
                #print(f"Moved panel {panel_idname} to category '{target_category}'")
            except Exception as e:
                pass
                #print(f"Error moving panel {panel_idname} to manager: {e}")
         else:
             print(f"Warning: Cannot find original data for panel {panel_idname} to show.")

    # 更新当前管理的面板集合
    currently_managed_panels.clear()
    currently_managed_panels.update(panels_to_make_visible)

    # 请求 UI 刷新
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                break

# 添加一个函数来获取排除的类别
def get_excluded_categories():
    """从偏好设置中获取排除的类别列表"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs and hasattr(prefs, "excluded_categories"):
            # 分割字符串并去除空白
            categories = [cat.strip() for cat in prefs.excluded_categories.split(',') if cat.strip()]
            # 确保管理器自身的类别也被排除
            if PANEL_CATEGORY not in categories:
                categories.append(PANEL_CATEGORY)
            return set(categories)
    except Exception as e:
        print(f"Error getting excluded categories: {e}")
    
    # 默认排除类别
    return {"Item", "Tool", "View", "Create", "Relations", "Edit", 
            "Physics", "Grease Pencil", PANEL_CATEGORY, "Unknown"}

# 添加函数检查是否应该自动恢复
def should_auto_restore(restore_type='exit'):
    """检查是否应该自动恢复面板
    
    Args:
        restore_type: 'exit' 或 'new_file'
    
    Returns:
        bool: 是否应该自动恢复
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
        # 出错时默认恢复，更安全
        return True
    
    return True  # 默认行为是恢复

# --- 更新函数 (放在 register_properties 前面或开头) ---
def update_list_filter(self, context):
    """ Simple update function to redraw areas containing the list """
    # 强制 UI 刷新 (覆盖所有可能包含列表的窗口和区域)
    # 这是一种比较通用的方法，确保UI更新
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()

def save_favorites_to_preferences():
    """将当前收藏状态保存到插件偏好设置中"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        scene = bpy.context.scene
        
        if prefs and hasattr(scene, "addon_manager_categories"):
            # 收集所有收藏的类别
            favorite_cats = []
            for item in scene.addon_manager_categories:
                if item.is_favorite:
                    favorite_cats.append(item.name)
            
            # 保存到偏好设置
            prefs.favorite_categories = ",".join(favorite_cats)
            #print(f"已保存 {len(favorite_cats)} 个收藏类别到偏好设置")
    except Exception as e:
        print(f"保存收藏类别时出错: {e}")

def load_favorites_from_preferences():
    """从插件偏好设置中加载收藏状态"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        scene = bpy.context.scene
        
        if prefs and hasattr(prefs, "favorite_categories") and hasattr(scene, "addon_manager_categories"):
            # 解析收藏类别列表
            favorite_cats = [cat.strip() for cat in prefs.favorite_categories.split(',') if cat.strip()]
            
            # 应用到当前类别列表
            updated_count = 0
            for item in scene.addon_manager_categories:
                if item.name in favorite_cats:
                    item.is_favorite = True
                    updated_count += 1
            
            #print(f"从偏好设置中加载了 {updated_count} 个收藏类别")
            return favorite_cats
    except Exception as e:
        print(f"加载收藏类别时出错: {e}")
    
    return []

# 存储额外排除的类别
_additional_excluded_categories = []

def set_additional_excluded_categories(categories):
    """设置额外排除的类别列表"""
    global _additional_excluded_categories
    # 确保不会移除 PANEL_CATEGORY（Addon Mgr 自身的类别）
    _additional_excluded_categories = [cat for cat in categories if cat != PANEL_CATEGORY]
    # 确保 PANEL_CATEGORY 始终在排除列表中
    if PANEL_CATEGORY not in _additional_excluded_categories:
        _additional_excluded_categories.append(PANEL_CATEGORY)
    
    # 保存到偏好设置中
    save_additional_excluded_to_preferences()

def get_additional_excluded_categories():
    """获取额外排除的类别列表"""
    global _additional_excluded_categories
    return _additional_excluded_categories

def save_additional_excluded_to_preferences():
    """将额外排除的类别保存到偏好设置中"""
    try:
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs:
            # 将额外排除的类别列表转换为逗号分隔的字符串
            prefs.additional_excluded_categories = ",".join(_additional_excluded_categories)
    except Exception as e:
        print(f"Error saving additional excluded categories: {e}")

def load_additional_excluded_from_preferences():
    """从偏好设置中加载额外排除的类别"""
    global _additional_excluded_categories
    try:
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs and hasattr(prefs, "additional_excluded_categories"):
            # 分割字符串并去除空白
            _additional_excluded_categories = [cat.strip() for cat in prefs.additional_excluded_categories.split(',') if cat.strip()]
            # 确保 PANEL_CATEGORY 始终在排除列表中
            if PANEL_CATEGORY not in _additional_excluded_categories:
                _additional_excluded_categories.append(PANEL_CATEGORY)
    except Exception as e:
        print(f"Error loading additional excluded categories: {e}")

def get_excluded_categories():
    """从偏好设置中获取排除的类别列表"""
    try:
        import bpy
        from . import preferences
        prefs = preferences.get_preferences()
        if prefs and hasattr(prefs, "excluded_categories"):
            # 分割字符串并去除空白
            categories = [cat.strip() for cat in prefs.excluded_categories.split(',') if cat.strip()]
            # 添加额外排除的类别
            categories.extend([cat for cat in get_additional_excluded_categories() if cat not in categories])
            # 确保管理器自身的类别也被排除
            if PANEL_CATEGORY not in categories:
                categories.append(PANEL_CATEGORY)
            return set(categories)
    except Exception as e:
        print(f"Error getting excluded categories: {e}")
    
    # 默认排除类别
    return {"Item", "Tool", "View", "Create", "Relations", "Edit", 
            "Physics", "Grease Pencil", PANEL_CATEGORY, "Unknown"}