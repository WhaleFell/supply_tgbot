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
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from app.database.model import User, Config, Pay, Msg
from app.database.curd import UserCurd, ConfigCurd, MsgCURD, PayCurd

from app.database.connect import AsyncSessionMaker
from app.database.string_template import CustomParam
from app.database import init_table

from app.req_epusdt import EpusdtSDK
from app.config import settings

epsdk = EpusdtSDK(
    base_url=settings.EPUSDT_BACKEND,
    callback_url=settings.EPUSDT_CALLBACK_URL,
    sign_key=settings.EPUSDT_KEY,
)

# ====== sqlalchemy end =====

# ====== pyrogram =======
import pyromod
from pyromod.helpers import ikb, array_chunk  # inlinekeyboard
from pykeyboard import InlineButton, InlineKeyboard
from pyrogram import Client, idle, filters  # type:ignore
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
)
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

# ====== Schemas ======


# ====== Schemas end =====

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
NAME = os.environ.get("NAME") or "WFTest8964Bot"
# SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
# 异步 mysql+aiomysql://user:password@host:port/dbname
API_ID = 21341224
API_HASH = "2d910cf3998019516d6d4bbb53713f20"
SESSION_PATH: Path = Path(ROOTPATH, "sessions", f"{NAME}.txt")
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
            logger.error("回答超时！")
            if isinstance(message, Message):
                await message.reply(f"回答超时,请重来！")
        except SQLAlchemyError as err:
            logger.error(f"SQL Error:{err}")
            if isinstance(message, CallbackQuery):
                await message.message.reply(
                    f"机器人按钮回调数据库 Panic 了请重试:\n<code>{err}</code>"
                )
            else:
                await message.reply(f"机器人数据库 Panic 了请重试:\n<code>{err}</code>")
            raise err
        except Exception as err:
            logger.error(f"TGBot Error:{err}")
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

    def addCode(self, code: Any):
        return f"<code>{code}</code>"

    def USER_INFO(self, user: "User") -> str:
        return f"""
👧用户信息👧
系统 ID: {self.addCode(user.id)}
用户 ID:{self.addCode(user.user_id)}
注册时间:{self.addCode(user.create_at)}
账号余额:{self.addCode(user.amount)} Cion
发布次数:{self.addCode(user.count)}
"""

    def PAY_INFO(self, pay: Pay, actual_amount: str, token: str):
        return f"""
支付已经创建,请在 10 分钟内向:
<code>{token}</code>
转账 **{actual_amount}** USDT

订单号: <code>{pay.trade_id}</code>
实际到账金额: <code>{pay.amount}</code>
创建时间: <code>{pay.pay_at}</code>
订单状态: <code>{pay.status}</code> (1:等待支付 2:支付成功 3:已过期)
订单数据库 ID: <code>{pay.id}</code>
支付用户 ID: <code>{pay.user_id}</code>

**注意:转账一分都不能少,小数点也要精准支付,不然无法支付成功,遇到支付异常的情况请联系频道主**
"""

    async def start(self) -> str:
        """bot description"""
        async with AsyncSessionMaker() as session:
            config: Config = await ConfigCurd.getConfig(session)
            config = config.replaceConfig(custom=CustomParam())  # type: ignore
            return config.description

    async def PROVIDE(self) -> str:
        """供应方"""
        async with AsyncSessionMaker() as session:
            config: Config = await ConfigCurd.getConfig(session)
            return config.provide_desc

    async def REQUIRE(self) -> str:
        """需求方"""
        async with AsyncSessionMaker() as session:
            config: Config = await ConfigCurd.getConfig(session)
            return config.require_desc

    async def onceCost(self) -> int:
        async with AsyncSessionMaker() as session:
            config: Config = await ConfigCurd.getConfig(session)
            return config.once_cost

    def confirmButton(self) -> InlineKeyboardMarkup:
        """确定/取消按钮"""
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="✅确定", callback_data=CallBackData.YES),
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
) -> Optional[Message]:
    try:
        ans: Message = await message.chat.ask(queston, timeout=timeout)  # type: ignore
        return ans
    except pyromod.listen.ListenerTimeout:
        await message.reply(f"超时 {timeout}s,请重新 /start 开始")
    except Exception as exc:
        await message.reply(f"发送错误:\n <code>{exc}</code>")

    return None


def try_int(string: str) -> Union[str, int]:
    try:
        return int(string)
    except:
        return string


def remove_first_line(text: str) -> str:
    lines = text.split("\n")
    return "\n".join(lines[1:])


# ====== helper function end ====


# ===== Handle ======


@app.on_callback_query()
@capture_err
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    await cd.addCallback(callback_query)

    # 返回
    if callback_query.data == CallBackData.RETURN:
        await callback_query.message.reply_text(
            text=await content.start(), reply_markup=content.KEYBOARD()
        )


@app.on_message(
    filters=filters.command("start") & filters.private & ~filters.me
)
@capture_err
async def start(client: Client, message: Message):
    await message.reply_text(
        text=await content.start(), reply_markup=content.KEYBOARD()
    )


@app.on_message(
    filters=filters.regex(content.ZZFB) & filters.private & ~filters.me
)
@capture_err
async def choose_privide_or_require(client: Client, message: Message):
    await message.reply(
        text="请选择需求还是供应",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(  # Generates a callback query when pressed
                        "供给模板",
                        switch_inline_query_current_chat=await content.PROVIDE(),
                    ),
                    InlineKeyboardButton(  # Generates a callback query when pressed
                        "需求模板",
                        switch_inline_query_current_chat=await content.REQUIRE(),
                    ),
                ],
            ]
        ),
    )


@app.on_message(filters=filters.regex(r"^@.*") & filters.private & ~filters.me)
@capture_err
async def send_channel_message(client: Client, message: Message):
    raw_text = remove_first_line(message.text)
    # ban word check
    async with AsyncSessionMaker() as session:
        config: Config = await ConfigCurd.getConfig(session)
        matches = [
            ban_word for ban_word in config.banWordList if ban_word in raw_text
        ]
        if matches:
            return await message.reply(text=f"您发布的需求中含有违禁词！{matches} 请检查后重新发送！")

    msg: Message = await message.reply(
        text=f"您的供给需求信息,是否确定发送,发送成功后将扣除 {await content.onceCost()} Cion:\n<code>{raw_text}</code>",
        reply_markup=content.confirmButton(),
    )
    cq: CallbackQuery = await cd.moniterCallback(msg, timeout=30)

    if cq.data == CallBackData.YES:
        async with AsyncSessionMaker() as session:
            user = await UserCurd.registerUser(
                session, user=User.generateUser(message)
            )

            if user.amount <= 0:
                await message.reply("💔💔💔对不起,你的没钱了,赶紧充值！！！")
                return

            config: Config = await ConfigCurd.getConfig(session)
            config = config.replaceConfig(
                custom=CustomParam(sendCountent=raw_text, count=user.count + 1)
            )

            await client.send_message(
                chat_id=try_int(config.channel_id),
                text=config.send_content,
                reply_markup=content.channelButton(),
            )

            # 发送成功后付费
            user_end = await UserCurd.pay(session, user)
            # 并记录用户发送的信息
            send_msg: Msg = await MsgCURD.addMsg(
                session, msg=Msg(user_id=user_end.user_id, content=raw_text)
            )

            await session.commit()
            await msg.edit_text(
                text=f"供需发送频道成功,您的信息:\n{content.USER_INFO(user_end)}\n发送时间:{send_msg.send_at}"
            )


def str_to_float(s: str) -> Optional[float]:
    try:
        f = float(s)
        return f
    except ValueError:
        return None


@app.on_message(
    filters=filters.regex(content.WYCZ) & filters.private & ~filters.me
)
@capture_err
async def pay_usdt(client: Client, message: Message):
    # TODO: support amount button
    msg: Optional[Message] = await askQuestion(
        queston="请输入你要充值的金额,必须是一个小数或者整数!",
        client=client,
        message=message,
        timeout=200,
    )
    if not msg:
        return

    amount = str_to_float(msg.text)
    if amount == None:
        await message.reply(f"输入的参数有错误!{msg.text}")
        return

    trade_id, actual_amount, token = await epsdk.createPay(amount=amount)
    async with AsyncSessionMaker() as session:
        pay = Pay(
            user_id=message.from_user.id,
            trade_id=trade_id,
            amount=amount,
        )
        rePay = await PayCurd.createNewPay(session, pay=pay)

    await message.reply(
        text=content.PAY_INFO(
            pay=rePay, actual_amount=actual_amount, token=token
        )
    )


@app.on_message(
    filters=filters.regex(content.GRZX) & filters.private & ~filters.me
)
@capture_err
async def account_info(client: Client, message: Message):
    async with AsyncSessionMaker() as session:
        user = await UserCurd.getUserByID(session, user_id=message.from_user.id)
        if not user:
            await message.reply_text("用户未注册!正在注册!")

        user = await UserCurd.registerUser(
            session, user=User.generateUser(message)
        )

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
    logger.info("初始化数据库..")

    await init_table(is_drop=False)

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
