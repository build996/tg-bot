import re
import time

from telegram import Update
from telegram.ext import ContextTypes

import config

URL_PATTERN = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)


async def antispam_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """反垃圾消息过滤"""
    if not update.message or not update.message.text:
        return

    message = update.message
    user = message.from_user
    text = message.text

    # 管理员不受限制
    member = await message.chat.get_member(user.id)
    if member.status in ("administrator", "creator"):
        return

    # 检查敏感词
    for word in config.ANTISPAM["banned_words"]:
        if word in text:
            try:
                await message.delete()
                await message.chat.send_message(
                    f"⚠️ {user.full_name} 的消息因包含违规内容已被删除。"
                )
            except Exception:
                pass
            return

    # 检查链接数量
    links = URL_PATTERN.findall(text)
    max_links = config.ANTISPAM["max_links_per_message"]
    if len(links) > max_links:
        try:
            await message.delete()
            await message.chat.send_message(
                f"⚠️ {user.full_name} 的消息因包含过多链接已被删除（最多 {max_links} 个）。"
            )
        except Exception:
            pass
        return

    # 新成员链接限制
    new_members = context.bot_data.get("new_members", {})
    join_time = new_members.get(user.id)
    if join_time and links:
        cooldown = config.ANTISPAM["new_member_link_cooldown"]
        if time.time() - join_time < cooldown:
            try:
                await message.delete()
                remaining = int(cooldown - (time.time() - join_time))
                await message.chat.send_message(
                    f"⚠️ {user.full_name}，新成员在加入 {cooldown // 60} 分钟内不能发送链接。"
                    f"请 {remaining} 秒后再试。"
                )
            except Exception:
                pass
