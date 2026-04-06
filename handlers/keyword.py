from telegram import Update
from telegram.ext import ContextTypes

import config


async def keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """检查消息是否包含关键词并自动回复"""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    for keyword, reply in config.KEYWORD_REPLIES.items():
        if keyword in text:
            await update.message.reply_text(reply)
            break
