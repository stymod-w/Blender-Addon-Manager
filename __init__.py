bl_info = {
    "name": "Addon Manager",
    "author": "stymod",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Addon Mgr",
    "description": "管理和组织N面板插件",
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
# 注册函数
def register():
    for func in func_list:
        func.register()
    
    # 从偏好设置中加载额外排除的类别
    from . import common
    common.load_additional_excluded_from_preferences()
    # 延迟刷新
    def deferred_refresh():
        try:
            # 先扫描可用类别
            bpy.ops.addonmanager.scan_available_categories()
            bpy.ops.addonmanager.apply_excluded_categories()

            bpy.ops.addonmanager.refresh_categories()
        except Exception as e:
            print(f"Error during initial category refresh: {e}")
        return None
    
    bpy.app.timers.register(deferred_refresh, first_interval=0.1)

# 注销函数
def unregister():
    # 先恢复面板
    ui.restore_panels(force=True)
    
    # 然后注销各模块
    for func in reversed(func_list):
        func.unregister()

# 仅用于测试
if __name__ == "__main__":
    register()
