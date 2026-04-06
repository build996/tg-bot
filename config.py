# Telegram Bot Token（从 @BotFather 获取）
import os

TOKEN = os.environ.get("BOT_TOKEN", "1883001169:AAFEPCzmwW4kdvWa54sYuGAfxXmE7Mt2B1M")

# 欢迎消息模板（{name} 会被替换为新成员的名字）
WELCOME_MESSAGE = "欢迎 {name} 加入本群！请先阅读群规则（输入 /rules 查看）。"

# 关键词自动回复（关键词 -> 回复内容）
KEYWORD_REPLIES = {
    "你好": "你好！有什么可以帮你的吗？",
    "管理员": "如需联系管理员，请 @管理员用户名",
}

# 群规则
GROUP_RULES = """📋 群规则：
1. 禁止发送垃圾信息和广告
2. 禁止人身攻击和辱骂
3. 禁止发送不良内容
4. 遵守相关法律法规
5. 违规者将被禁言或踢出群组
"""

# 反垃圾设置
ANTISPAM = {
    "max_links_per_message": 2,          # 单条消息最大链接数
    "new_member_link_cooldown": 300,      # 新成员加入后多少秒内禁止发链接
    "banned_words": ["色情", "赌博", "代开"],  # 敏感词列表
}

# 默认禁言时长（分钟）
DEFAULT_MUTE_MINUTES = 10
