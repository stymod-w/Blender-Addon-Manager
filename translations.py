import bpy

# 翻译字典
translations_dict = {
    "zh_CN": {
        ("*", "刷新来重置视图/释放插件"): "刷新来重置视图/释放插件",
        ("*", "共找到{} 个"): "共找到{} 个",
        ("*", "显示插件: '{}'"): "显示插件: '{}'",
        ("*", "在此处查看其面板_刷新按钮释放插件."): "在此处查看其面板_刷新按钮释放插件.",
        # 偏好设置界面翻译
        ("*", "语言设置 Language Settings:"): "语言设置 Language Settings:",
        ("*", "打开新文件时自动恢复面板（建议保持默认）"): "打开新文件时自动恢复面板（建议保持默认）",
        ("*", "使用须知"): "使用须知",
        ("*", "1. 本插件会改变N面板上插件的显示顺序"): "1. 本插件会改变N面板上插件的显示顺序",
        ("*", "2. 被管理的插件在使用时会在原N面板位置会被隐藏"): "2. 被管理的插件在使用时会在原N面板位置会被隐藏",
        ("*", "介意勿用！"): "介意勿用！",
        ("*", "自动恢复设置:"): "自动恢复设置:",
        ("*", "类别排除设置:"): "类别排除设置:",
        ("*", "默认排除的类别（不建议修改）"): "默认排除的类别（不建议修改）",
        ("*", "默认排除类别 (英文逗号分隔，不建议修改)"): "默认排除类别 (英文逗号分隔，不建议修改)",
        ("*", "扫描可用类别"): "扫描可用类别",
        ("*", "初始化或插件更新后请点击"): "初始化或插件更新后请点击",
        ("*", "其他可排除类别"): "其他可排除类别",
        ("*", "其他可排除类别 (点击折叠)"): "其他可排除类别 (点击折叠)",
        ("*", "列数"): "列数",
        ("*", "点击选择要额外排除的类别:"): "点击选择要额外排除的类别:",
        ("*", "应用排除设置"): "应用排除设置",
        ("*", "请先扫描可用类别"): "请先扫描可用类别",
        ("*", "收藏设置"): "收藏设置",
        ("*", "收藏的类别"): "收藏的类别",
        ("*", "收藏类别 (英文逗号分隔)"): "收藏类别 (英文逗号分隔)",
    },
    "en_US": {
        # UI 相关翻译
        ("*", "刷新来重置视图/释放插件"): "Refresh to reset view/release addons",
        ("*", "共找到{} 个"): "Found {} items",
        ("*", "显示插件: '{}'"): "Showing addon: '{}'",
        ("*", "在此处查看其面板_刷新按钮释放插件."): "View panels here_Refresh button to release addons.",
        # 偏好设置界面翻译
        ("*", "语言设置 Language Settings:"): "Language Settings:",
        ("*", "打开新文件时自动恢复面板（建议保持默认）"): "Auto-restore panels on new file (recommended)",       
        ("*", "使用须知"): "Important Notice",
        ("*", "1. 本插件会改变N面板上插件的显示顺序"): "1. This addon will change the display order of N-panel addons",
        ("*", "2. 被管理的插件在使用时会在原N面板位置会被隐藏"): "2. Managed addons will be hidden from their original locations",
        ("*", "介意勿用！"): "Please consider before use!",
        ("*", "自动恢复设置:"): "Auto Restore Settings:",
        ("*", "类别排除设置:"): "Category Exclusion Settings:",
        ("*", "默认排除的类别（不建议修改）"): "Default Excluded Categories (Not recommended to modify)",
        ("*", "默认排除类别 (英文逗号分隔，不建议修改)"): "Default excluded categories (comma separated, not recommended to modify)",
        ("*", "扫描可用类别"): "Scan Available Categories",
        ("*", "初始化或插件更新后请点击"): "Click after initialization or addon update",
        ("*", "其他可排除类别"): "Other Excludable Categories",
        ("*", "其他可排除类别 (点击折叠)"): "Other Excludable Categories (Click to Collapse)",
        ("*", "列数"): "Columns",
        ("*", "点击选择要额外排除的类别:"): "Click to select additional categories to exclude:",
        ("*", "应用排除设置"): "Apply Exclusion Settings",
        ("*", "请先扫描可用类别"): "Please scan available categories first",
        ("*", "收藏设置"): "Favorite Settings",
        ("*", "收藏的类别"): "Favorite Categories",
        ("*", "收藏类别 (英文逗号分隔)"): "Favorite categories (comma separated)",
    }
}

_current_language = 'zh_CN'

def register_translations():
    """注册翻译"""
    # 先注册默认语言的翻译
    bpy.app.translations.register(__name__, translations_dict[_current_language])
    
    # 使用定时器延迟加载语言设置，确保偏好设置已完全初始化
    bpy.app.timers.register(load_language_from_preferences)

def unregister_translations():
    """注销翻译"""
    
    try:
        bpy.app.translations.unregister(__name__)
    except Exception as e:
        print(f"Error unregistering translations: {e}")

def switch_language(language):
    global _current_language
    if language != _current_language:
        try:
            _current_language = language
            # 重新注册翻译
            unregister_translations()
            bpy.app.translations.register(__name__, translations_dict[language])
            print(f"语言已切换到: {language}")
        except Exception as e:
            print(f"切换语言时出错: {e}")

def get_text(text):
    """获取当前语言的翻译文本"""
    try:
        # 直接从翻译字典中获取对应语言的文本
        return translations_dict[_current_language].get(("*", text), text)
    except:
        return text

def load_language_from_preferences():
    """从偏好设置中加载语言设置"""
    try:
        addon_prefs = bpy.context.preferences.addons[__package__].preferences
        if hasattr(addon_prefs, 'language') and addon_prefs.language != _current_language:
            # 如果偏好设置中的语言与当前语言不同，则切换语言
            switch_language(addon_prefs.language)
    except (AttributeError, KeyError) as e:
        print(f"加载语言设置时出错: {e}")
    
    # 不需要重复执行此定时器
    return None