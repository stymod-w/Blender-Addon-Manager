import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty, EnumProperty, CollectionProperty,IntProperty
from . import translations

# 添加类别项类型
class ADDONMANAGER_CategoryExcludeItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Category Name")
    exclude: BoolProperty(
        name="Exclude",
        description="Exclude this category from the addon manager",
        default=False
    )

def update_language(self, context):
    """语言更新回调函数"""
    bpy.ops.addonmanager.change_language()
    # 不返回任何值
# 插件偏好设置
class ADDONMANAGER_preferences(AddonPreferences):
    bl_idname = __package__  # 使用包名作为ID
    language: EnumProperty(
        name="插件语言 Language",
        description="选择插件界面语言",
        items=[
            ('zh_CN', "中文", "使用中文界面"),
            ('en_US', "English", "Use English interface"),
        ],
        default='zh_CN',
        update=lambda self, context: update_language(self, context)
        
    )

    favorite_categories: StringProperty(
        name="收藏的类别",
        description="收藏的类别列表，用逗号分隔",
        default=""
    )
    #在ADDONMANAGER_preferences类中添加新属性
    auto_restore_on_exit: BoolProperty(
        name="退出时自动恢复面板",
        description="关闭Blender或打开新文件时自动将面板恢复到原始类别",
        default=True
    )

    auto_restore_on_new_file: BoolProperty(
        name="打开新文件时自动恢复面板（建议保持默认）",
        description="打开新文件时自动将面板恢复到原始类别",
        default=True
    )
    
    excluded_categories: StringProperty(
        name="默认排除的类别（不建议修改）",
        description="始终排除的基础类别，用逗号分隔",
        default="Item,Tool,View,Create,Relations,Edit,Physics,Grease Pencil"
    )
    additional_excluded_categories: StringProperty(
        name="额外排除的类别",
        description="通过UI选择排除的额外类别",
        default=""
    )
    # 添加用于控制UI显示的属性
    show_category_list: BoolProperty(
        name="显示类别列表",
        description="展开/折叠类别列表",
        default=False
    )
    
    columns_count: IntProperty(
        name="列数",
        description="类别列表显示的列数",
        default=3,
        min=1,
        max=5
    )
    available_categories: CollectionProperty(type=ADDONMANAGER_CategoryExcludeItem)


    def draw(self, context):
        layout = self.layout
        

        # 语言设置
        lang_box = layout.box()
        lang_box.label(text="语言设置 Language Settings:", icon='WORLD')
        lang_box.prop(self, "language")
        layout.separator()

        # 提醒部分 
        box = layout.box()
        box.label(text=translations.get_text("使用须知"), icon='ERROR')
        box.label(text=translations.get_text("1. 本插件会改变N面板上插件的显示顺序"))
        box.label(text=translations.get_text("2. 被管理的插件在使用时会在原N面板位置会被隐藏"))
        box.label(text=translations.get_text("介意勿用！"), icon='INFO')
        
        layout.separator()

        # 添加自动恢复选项
        box = layout.box()
        box.label(text=translations.get_text("自动恢复设置:"), icon='RECOVER_LAST')
        box.prop(self, "auto_restore_on_new_file",text=translations.get_text("打开新文件时自动恢复面板（建议保持默认）"))
        layout.separator()
        
        # 类别排除设置
        box = layout.box()
        box.label(text=translations.get_text("类别排除设置:"), icon='FILTER')
        
        # 默认排除类别（文本输入）
        box.prop(self, "excluded_categories", text=translations.get_text("默认排除的类别（不建议修改）"))
        box.label(text=translations.get_text("默认排除类别 (英文逗号分隔，不建议修改)"), icon='INFO')
        

        # 扫描按钮
        row = box.row()
        row.operator("addonmanager.scan_available_categories", 
                    text=translations.get_text("扫描可用类别"), icon='FILE_REFRESH')
        row.label(text=translations.get_text("初始化或插件更新后请点击"), icon='ERROR')
        # 折叠/展开按钮
        row = box.row()
        row.prop(self, "show_category_list", 
                 icon='TRIA_DOWN' if self.show_category_list else 'TRIA_RIGHT',
                 text=translations.get_text("其他可排除类别") if not self.show_category_list else translations.get_text("其他可排除类别 (点击折叠)"))
        
        # 列数设置
        if self.show_category_list:
            row.prop(self, "columns_count", text=translations.get_text("列数"))
        

        
        # 显示可选择的类别列表（仅当展开时）
        if self.show_category_list and len(self.available_categories) > 0:
            # 计算每列显示的项目数
            total_items = len(self.available_categories)
            items_per_column = max(1, total_items // self.columns_count + (1 if total_items % self.columns_count else 0))
            
            # 创建多列布局
            box.label(text=translations.get_text("点击选择要额外排除的类别:"))
            row = box.row()
            
            # 获取默认排除的类别列表
            default_excluded = [cat.strip() for cat in self.excluded_categories.split(',') if cat.strip()]
            
            # 为每列创建一个列布局
            for col_idx in range(self.columns_count):
                if col_idx * items_per_column >= total_items:
                    break
                    
                col = row.column()
                for i in range(items_per_column):
                    item_idx = col_idx * items_per_column + i
                    if item_idx < total_items:
                        item = self.available_categories[item_idx]
                        # 如果类别已在默认排除列表中，则不显示
                        if item.name not in default_excluded:
                            item_row = col.row()
                            item_row.prop(item, "exclude", text=item.name)
            
            # 应用按钮
            row = box.row()
            row.operator("addonmanager.apply_excluded_categories", 
                         text=translations.get_text("应用排除设置"), icon='CHECKMARK')
        elif self.show_category_list:
            box.label(text=translations.get_text("请先扫描可用类别"), icon='INFO')

        # 添加收藏类别设置
        box = layout.box()
        box.label(text=translations.get_text("收藏设置"), icon='SOLO_ON')
        box.prop(self, "favorite_categories", text=translations.get_text("收藏的类别"))
        box.label(text=translations.get_text("收藏类别 (英文逗号分隔)"), icon='INFO')

# 获取插件偏好设置的辅助函数
def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences

# 注册类列表
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