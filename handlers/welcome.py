from telegram import Update
from telegram.ext import ContextTypes

import config


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """记录新成员加入时间（用于反垃圾），不发送欢迎消息"""
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        if "new_members" not in context.bot_data:
            context.bot_data["new_members"] = {}
        context.bot_data["new_members"][member.id] = update.message.date.timestamp()
