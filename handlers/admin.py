from datetime import timedelta

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

import config


async def _is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """检查命令调用者是否为群管理员"""
    user = update.effective_user
    chat = update.effective_chat
    member = await chat.get_member(user.id)
    return member.status in ("administrator", "creator")


def _get_target_user(update: Update):
    """从回复的消息或命令参数中获取目标用户"""
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    return None


async def _delete_command(update: Update):
    """删除管理员的命令消息"""
    try:
        await update.message.delete()
    except Exception:
        pass


async def _reply_and_delete(update: Update, text: str, delay: int = 5):
    """发送提示消息并在几秒后自动删除"""
    import asyncio
    msg = await update.effective_chat.send_message(text)
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ban — 踢出并封禁用户（需回复目标用户的消息）"""
    if not await _is_admin(update, context):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    await _delete_command(update)

    target = _get_target_user(update)
    if not target:
        await _reply_and_delete(update, "请回复要封禁的用户的消息。")
        return

    try:
        await update.effective_chat.ban_member(target.id)
        await _reply_and_delete(update, f"✅ 已封禁用户 {target.full_name}。")
    except Exception as e:
        await _reply_and_delete(update, f"❌ 操作失败：{e}")


async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/mute [分钟数] — 禁言用户（需回复目标用户的消息）"""
    if not await _is_admin(update, context):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    await _delete_command(update)

    target = _get_target_user(update)
    if not target:
        await _reply_and_delete(update, "请回复要禁言的用户的消息。")
        return

    # 解析禁言时长
    minutes = config.DEFAULT_MUTE_MINUTES
    if context.args:
        try:
            minutes = int(context.args[0])
        except ValueError:
            pass

    try:
        until = update.message.date + timedelta(minutes=minutes)
        permissions = ChatPermissions(can_send_messages=False)
        await update.effective_chat.restrict_member(target.id, permissions, until_date=until)
        await _reply_and_delete(update, f"🔇 已禁言 {target.full_name} {minutes} 分钟。")
    except Exception as e:
        await _reply_and_delete(update, f"❌ 操作失败：{e}")


async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/unmute — 解除禁言（需回复目标用户的消息）"""
    if not await _is_admin(update, context):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    await _delete_command(update)

    target = _get_target_user(update)
    if not target:
        await _reply_and_delete(update, "请回复要解除禁言的用户的消息。")
        return

    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        await update.effective_chat.restrict_member(target.id, permissions)
        await _reply_and_delete(update, f"🔊 已解除 {target.full_name} 的禁言。")
    except Exception as e:
        await _reply_and_delete(update, f"❌ 操作失败：{e}")


async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/rules — 显示群规则"""
    # 优先使用动态设置的规则
    rules = context.bot_data.get("custom_rules", config.GROUP_RULES)
    await update.message.reply_text(rules)


async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/setrules <内容> — 设置群规则（仅管理员）"""
    if not await _is_admin(update, context):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    await _delete_command(update)

    if not context.args:
        await _reply_and_delete(update, "用法：/setrules <规则内容>")
        return

    new_rules = " ".join(context.args)
    context.bot_data["custom_rules"] = new_rules
    await _reply_and_delete(update, "✅ 群规则已更新。")


async def send_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ad <内容> — 发送格式化广告消息（仅管理员）"""
    if not await _is_admin(update, context):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    if not context.args:
        await update.message.reply_text("用法：/ad <广告内容>")
        return

    ad_content = " ".join(context.args)
    ad_message = (
        "📢 <b>公告</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"{ad_content}\n"
        "━━━━━━━━━━━━━━"
    )

    try:
        # 删除管理员的命令消息
        await update.message.delete()
        # 发送格式化广告
        await update.effective_chat.send_message(ad_message, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ 发送失败：{e}")
