import re
import time
from datetime import timedelta

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

import config

URL_PATTERN = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)


async def _is_admin_user(message, user) -> bool:
    """检查用户是否为管理员"""
    if user.id == 1087968824:
        return True
    member = await message.chat.get_member(user.id)
    return member.status in ("administrator", "creator")


async def _delete_and_mute(message, user, reason: str, minutes: int):
    """删除消息并禁言"""
    try:
        await message.delete()
        until = message.date + timedelta(minutes=minutes)
        permissions = ChatPermissions(can_send_messages=False)
        await message.chat.restrict_member(user.id, permissions, until_date=until)
        await message.chat.send_message(
            f"🚫 {user.full_name} {reason}，已被禁言 {minutes} 分钟。"
        )
    except Exception:
        pass


async def antispam_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """反垃圾消息过滤（文本消息）"""
    if not update.message or not update.message.text:
        return

    message = update.message
    user = message.from_user
    text = message.text

    # 管理员不受限制
    if await _is_admin_user(message, user):
        return

    # 检查链接（普通成员禁止发任何链接）
    links = URL_PATTERN.findall(text)
    if links:
        await _delete_and_mute(message, user, "因发送链接", config.AD_MUTE_MINUTES)
        return

    # 检查广告关键词
    for keyword in config.AD_KEYWORDS:
        if keyword in text:
            await _delete_and_mute(message, user, "因发送广告", config.AD_MUTE_MINUTES)
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


async def antispam_photo_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """过滤二维码图片（含图片/贴纸的消息）"""
    if not update.message:
        return

    message = update.message
    user = message.from_user

    # 管理员不受限制
    if await _is_admin_user(message, user):
        return

    # 检查消息中的图片说明文字是否包含广告关键词
    caption = message.caption or ""
    for keyword in config.AD_KEYWORDS:
        if keyword in caption:
            await _delete_and_mute(message, user, "因发送广告", config.AD_MUTE_MINUTES)
            return

    # 检查图片说明中的链接
    links = URL_PATTERN.findall(caption)
    if links:
        await _delete_and_mute(message, user, "因发送链接", config.AD_MUTE_MINUTES)
        return
