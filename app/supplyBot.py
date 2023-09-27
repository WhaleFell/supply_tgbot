# ===== Sqlalchemy =====
from sqlalchemy import select, insert, String, func, update, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncAttrs,
    async_sessionmaker,
    AsyncSession,
)
from datetime import datetime

# ====== sqlalchemy end =====

# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pykeyboard import InlineButton, InlineKeyboard
from pyrogram import Client, idle, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
)
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode

# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional
from typing_extensions import Annotated
from pathlib import Path
import asyncio
from loguru import logger
import sys
import re
from functools import wraps
import os
import sys
import glob
from asyncio import Queue

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
NAME = os.environ.get("NAME") or "WFTest8964Bot"
# SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
# 异步 mysql+aiomysql://user:password@host:port/dbname
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
# 需要发布的 Channle ID
# ====== Config End ======

# ===== logger ====
from .utils.custom_log import logger

# ===== logger end =====

# ===== error handle =====


def capture_err(func):
    """handle error and notice user"""

    @wraps(func)
    async def capture(
        client: Client, message: Union[Message, CallbackQuery], *args, **kwargs
    ):
        try:
            return await func(client, message, *args, **kwargs)
        except asyncio.exceptions.TimeoutError:
            if isinstance(message, Message):
                await message.reply(f"回答超时,请重来！")
            logger.error("回答超时！")
        except Exception as err:
            if isinstance(message, CallbackQuery):
                await message.message.reply(
                    f"机器人按钮回调 Panic 了:\n<code>{err}</code>"
                )
            else:
                await message.reply(f"机器人 Panic 了:\n<code>{err}</code>")
            raise err

    return capture


# ====== error handle end =========

# ====== Client maker =======


def makeClient(path: Path) -> Client:
    session_string = path.read_text(encoding="utf8")
    return Client(
        name=path.stem,
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
    )


app = makeClient(SESSION_PATH)

# ====== Client maker end =======

# ====== callback Queue ========


class CallbackDataQueue(object):
    def __init__(self) -> None:
        self.queue = Queue()

    async def addCallback(self, callbackQuery: CallbackQuery):
        logger.info(f"new callbackQuery data:{callbackQuery.data}")
        await self.queue.put(callbackQuery)

    async def moniterCallback(
        self, message: Message, timeout: int = 10
    ) -> CallbackQuery:
        while True:
            cb: CallbackQuery = await asyncio.wait_for(
                self.queue.get(), timeout=timeout
            )
            if cb.message.id == message.id:
                return cb
            else:
                await self.queue.put(cb)


cd = CallbackDataQueue()

# ====== callback Queue end ========


# ====== Content enum =======


class CallBackData:
    YES = "YES"
    NO = "NO"
    RETURN = "return"


class Content(object):
    ZZFB = "💫自助发布"
    WYCZ = "✨我要充值"
    GRZX = "👩‍🦱个人中心"

    def KEYBOARD(self) -> ReplyKeyboardMarkup:
        keyboard = ReplyKeyboardMarkup(
            [[self.ZZFB, self.WYCZ], [self.GRZX]], resize_keyboard=True
        )
        return keyboard

    def addCode(self, code: str):
        return f"<code>{code}</code>"

    def USER_INFO(self, user: "User") -> str:
        return f"""
👧用户信息👧
系统 ID: {self.addCode(user.id)}
用户 ID:{self.addCode(user.user_id)}
注册时间:{self.addCode(user.reg_at)}
账号余额:{self.addCode(user.cion)} Cion
发布次数:{self.addCode(user.count)}
"""

    def PROVIDE(self) -> str:
        """供应方"""
        return """
项目名称：
项目介绍：
价格：
联系人：
频道：【选填/没频道可以不填】
"""

    def REQUIRE(self) -> str:
        """需求方"""
        return """
需求：
预算：
联系人：
频道：【选填/没频道可以不填】
"""

    def confirmButton(self) -> InlineKeyboardMarkup:
        """确定/取消按钮"""
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="☑确定", callback_data=CallBackData.YES),
            InlineButton(text="❌取消", callback_data=CallBackData.RETURN),
        )
        return keyboard

    def channelButton(self) -> InlineKeyboardMarkup:
        """添加到频道的按钮"""
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="供给自助发布", url="https://t.me/WFTest8964Bot"),
        )
        return keyboard


content = Content()

# ====== Content enum End =======

# ====== helper function  ====


async def askQuestion(
    queston: str, client: Client, message: Message, timeout: int = 200
) -> Union[Message, bool]:
    try:
        ans: Message = await message.chat.ask(queston, timeout=timeout)
        return ans
    except pyromod.listen.ListenerTimeout:
        await message.reply(f"超时 {timeout}s,请重新 /start 开始")
    except Exception as exc:
        await message.reply(f"发送错误:\n <code>{exc}</code>")
    return False


def try_int(string: str) -> Union[str, int]:
    try:
        return int(string)
    except:
        return string


def remove_first_line(text: str) -> str:
    lines = text.split("\n")
    return "\n".join(lines[1:])


# ====== helper function end ====

# ====== DB model =====

engine = create_async_engine(DB_URL, pool_pre_ping=True, pool_recycle=600)

# 会话构造器
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False
)


# ======= DB model End =====

# ===== Handle ======


@app.on_callback_query()
@capture_err
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    await cd.addCallback(callback_query)

    # 返回
    if callback_query.data == CallBackData.RETURN:
        await callback_query.message.reply_text(
            __desc__, reply_markup=content.KEYBOARD()
        )


@app.on_message(
    filters=filters.command("start") & filters.private & ~filters.me
)
@capture_err
async def start(client: Client, message: Message):
    await message.reply_text(__desc__, reply_markup=content.KEYBOARD())


@app.on_message(
    filters=filters.regex(content.ZZFB) & filters.private & ~filters.me
)
@capture_err
async def sendSupply(client: Client, message: Message):
    await message.reply(
        text="请选择需求还是供应",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(  # Generates a callback query when pressed
                        "供给模板",
                        switch_inline_query_current_chat=content.PROVIDE(),
                    ),
                    InlineKeyboardButton(  # Generates a callback query when pressed
                        "需求模板",
                        switch_inline_query_current_chat=content.REQUIRE(),
                    ),
                ],
            ]
        ),
    )


@app.on_message(filters=filters.regex(r"^@.*") & filters.private & ~filters.me)
@capture_err
async def atMessage(client: Client, message: Message):
    raw_text = remove_first_line(message.text)
    msg: Message = await message.reply(
        text=f"您的供给需求信息,是否确定发送,发送成功后将扣除 {amount} Cion:\n<code>{raw_text}</code>",
        reply_markup=content.confirmButton(),
    )
    cq: CallbackQuery = await cd.moniterCallback(msg, timeout=20)

    if cq.data == CallBackData.YES:
        user = await manager.register(user_id=message.from_user.id)
        count = await manager.getOrSetCount(user=user)
        text = f"""
{raw_text}

**该用户累计发布 {count+1} 次广告**
"""

        await client.send_message(
            chat_id=CHANNEL_ID, text=text, reply_markup=content.channelButton()
        )

        user_end = await manager.pay(user=user, amount=-amount)
        await msg.edit_text(
            text=f"供需发送频道成功,您的信息:\n{content.USER_INFO(user_end)}"
        )


@app.on_message(
    filters=filters.regex(content.WYCZ) & filters.private & ~filters.me
)
@capture_err
async def addCion(client: Client, message: Message):
    await message.reply_text("请联系管理员充值")


@app.on_message(
    filters=filters.regex(content.GRZX) & filters.private & ~filters.me
)
@capture_err
async def accountCenter(client: Client, message: Message):
    user = await manager.searchUser(user_id=message.from_user.id)
    if not user:
        await message.reply_text("用户未注册!正在注册!")

    user = await manager.register(user_id=message.from_user.id)

    await message.reply_text(f"{content.USER_INFO(user)}")


@app.on_message(filters=filters.command("getID") & ~filters.me)
@capture_err
async def get_ID(client: Client, message: Message):
    await message.reply(f"当前会话的ID:<code>{message.chat.id}</code>")


# ==== Handle end =====


async def main():
    global app
    await app.start()
    user = await app.get_me()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ===== Test Code =======
    # chat_id = await app.get_chat("@w2ww2w2w")
    # print(chat_id)

    # ======== Test Code end ==========

    logger.success(
        f"""
-------login success--------
username: {user.first_name}
type: {"Bot" if user.is_bot else "User"}
@{user.username}
----------------------------
"""
    )

    await app.set_bot_commands(
        [
            BotCommand("start", "开始"),
        ]
    )

    await idle()
    await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
