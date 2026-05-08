import json
import os
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

import config

WHITELIST_FILE = Path(__file__).resolve().parent.parent / "whitelist.json"


def _load_from_disk() -> set:
    if not WHITELIST_FILE.exists():
        return set()
    try:
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("items", []))
    except Exception:
        return set()


def _save_to_disk(items: set) -> None:
    tmp = WHITELIST_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"items": sorted(items, key=lambda x: (isinstance(x, str), str(x)))}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, WHITELIST_FILE)


def init_whitelist(bot_data: dict) -> None:
    """启动时调用，把磁盘上的运行时白名单加载到 bot_data。"""
    bot_data["ad_whitelist"] = _load_from_disk()


def get_runtime_whitelist(context: ContextTypes.DEFAULT_TYPE) -> set:
    return context.bot_data.setdefault("ad_whitelist", set())


def is_whitelisted(user, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """命中 config.AD_WHITELIST 或运行时白名单任一项即放行。"""
    runtime = get_runtime_whitelist(context)
    for source in (config.AD_WHITELIST, runtime):
        if user.id in source:
            return True
        if user.username and user.username in source:
            return True
        if user.full_name and user.full_name in source:
            return True
    return False


async def _is_admin(update: Update) -> bool:
    user = update.effective_user
    if user.id == 1087968824:
        return True
    member = await update.effective_chat.get_member(user.id)
    return member.status in ("administrator", "creator")


async def _delete_command(update: Update):
    try:
        await update.message.delete()
    except Exception:
        pass


async def _reply_and_delete(update: Update, text: str, delay: int = 5):
    import asyncio
    msg = await update.effective_chat.send_message(text)
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def add_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/whitelist — 把回复的目标用户加入广告白名单（按 user_id，最稳）。
    也支持 /whitelist <user_id|@username|昵称> 直接加。
    """
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    await _delete_command(update)
    runtime = get_runtime_whitelist(context)

    target_repr = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        runtime.add(target.id)
        target_repr = f"{target.full_name} (id={target.id})"
    elif context.args:
        raw = " ".join(context.args).strip()
        if raw.startswith("@"):
            raw = raw[1:]
        if raw.isdigit():
            runtime.add(int(raw))
            target_repr = f"user_id={raw}"
        else:
            runtime.add(raw)
            target_repr = f"'{raw}'"
    else:
        await _reply_and_delete(update, "用法：回复某人消息后发 /whitelist，或 /whitelist <user_id|@username|昵称>")
        return

    _save_to_disk(runtime)
    await _reply_and_delete(update, f"✅ 已加入广告白名单：{target_repr}")


async def remove_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/unwhitelist — 把回复的目标用户移出广告白名单，或 /unwhitelist <user_id|@username|昵称>。"""
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    await _delete_command(update)
    runtime = get_runtime_whitelist(context)

    candidates = []
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        candidates = [target.id, target.username, target.full_name]
    elif context.args:
        raw = " ".join(context.args).strip()
        if raw.startswith("@"):
            raw = raw[1:]
        candidates = [int(raw)] if raw.isdigit() else [raw]
    else:
        await _reply_and_delete(update, "用法：回复某人消息后发 /unwhitelist，或 /unwhitelist <user_id|@username|昵称>")
        return

    removed = [c for c in candidates if c and c in runtime]
    for c in removed:
        runtime.discard(c)

    if removed:
        _save_to_disk(runtime)
        await _reply_and_delete(update, f"✅ 已移出广告白名单：{removed}")
    else:
        await _reply_and_delete(update, "ℹ️ 该用户不在运行时白名单中（注意 config.AD_WHITELIST 是静态配置，需要改代码）。")


async def list_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/whitelisted — 列出当前广告白名单（静态 + 运行时）。"""
    if not await _is_admin(update):
        await update.message.reply_text("⚠️ 仅管理员可使用此命令。")
        return

    await _delete_command(update)
    runtime = get_runtime_whitelist(context)

    static_items = sorted(config.AD_WHITELIST, key=lambda x: (isinstance(x, str), str(x)))
    runtime_items = sorted(runtime, key=lambda x: (isinstance(x, str), str(x)))

    lines = ["📋 <b>广告白名单</b>"]
    lines.append(f"\n<b>静态（config.py，需改代码）</b>: {static_items or '空'}")
    lines.append(f"<b>运行时（/whitelist 添加）</b>: {runtime_items or '空'}")
    await update.effective_chat.send_message("\n".join(lines), parse_mode="HTML")
