import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
from handlers.welcome import welcome_new_member
from handlers.keyword import keyword_reply
from handlers.admin import ban_user, mute_user, unmute_user, show_rules, set_rules, send_ad
from handlers.antispam import antispam_filter, antispam_photo_filter

# 日志配置
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    app = ApplicationBuilder().token(config.TOKEN).build()

    # 新成员欢迎
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # 管理命令
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("rules", show_rules))
    app.add_handler(CommandHandler("setrules", set_rules))
    app.add_handler(CommandHandler("ad", send_ad))

    # 反垃圾过滤（优先级高，group=0）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antispam_filter), group=0)
    # 图片/文件广告过滤（group=0）
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, antispam_photo_filter), group=0)

    # 关键词自动回复（优先级低，group=1，在反垃圾之后）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_reply), group=1)

    logger.info("Bot 启动成功！")
    app.run_polling()


if __name__ == "__main__":
    main()
