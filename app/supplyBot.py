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
    ForceReply,
)
from pyrogram.enums import ParseMode, MessageMediaType
from pyrogram.errors import exceptions as pyroExc
from pyrogram import types

# ====== pyrogram end =====

from contextlib import closing, suppress
from typing import List, Union, Any, Optional, BinaryIO
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
from datetime import datetime, timedelta

# ====== Schemas ======


# ====== Schemas end =====

# ====== Config ========
ROOTPATH: Path = Path(__file__).parent.absolute()
DEBUG = True
NAME = os.environ.get("NAME") or "session"
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
                await message.reply(
                    f"回答超时,请重来！", reply_markup=content.KEYBOARD()
                )
        except SQLAlchemyError as err:
            logger.error(f"SQL Error:{err}")
            if isinstance(message, CallbackQuery):
                await message.message.reply(
                    f"机器人按钮回调数据库 Panic 了请重试:\n<code>{err}</code>",
                    reply_markup=content.KEYBOARD(),
                )
            else:
                await message.reply(
                    f"机器人数据库 Panic 了请重试:\n<code>{err}</code>",
                    reply_markup=content.KEYBOARD(),
                )
            raise err
        except pyroExc.bad_request_400.MessageNotModified as exc:
            logger.error(
                f"Pyrogram MessageNotModified Error 编辑了相同信息 {exc.MESSAGE}"
            )
        except Exception as err:
            logger.error(f"TGBot Globe Error:{err}")
            if isinstance(message, CallbackQuery):
                await message.message.reply(
                    f"机器人按钮回调 Panic 了:\n<code>{err}</code>",
                    reply_markup=content.KEYBOARD(),
                )
            else:
                await message.reply(
                    f"机器人 Panic 了:\n<code>{err}</code>",
                    reply_markup=content.KEYBOARD(),
                )
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

    PAY: str = "pay"

    PROVIDE: str = "provide"
    REQUIRE: str = "require"

    MEDIAPROREQ: str = "mediaProReq"


class Content(object):
    ZZFB = "💫自助发布"
    WYCZ = "✨我要充值"
    GRZX = "👩‍🦱个人中心"
    FBJL = "🔰发布记录"

    def KEYBOARD(self) -> ReplyKeyboardMarkup:
        keyboard = ReplyKeyboardMarkup(
            [[self.ZZFB, self.WYCZ], [self.GRZX, self.FBJL]],
            resize_keyboard=True,
            is_persistent=True,
        )
        return keyboard

    def addCode(self, code: Any):
        return f"<code>{code}</code>"

    def USER_INFO(self, user: "User") -> str:
        # 用户 ID:{self.addCode(user.user_id)}
        return f"""
👧用户信息👧
注册时间:{self.addCode(user.create_at)}
账号余额:{self.addCode(user.amount)} USDT
发布次数:{self.addCode(user.count)}
"""

    def PAY_INFO(
        self, pay: Pay, actual_amount: str, token: str, config: Config
    ):
        return f"""
支付已经创建,请在 10 分钟内向:
<code>{token}</code>
转账 **{actual_amount}** USDT

当前系统充值倍率:<code>{config.multiple}</code>
订单号: <code>{pay.trade_id}</code>
实际到账金额: <code>{pay.amount*config.multiple}</code>
创建时间: <code>{pay.pay_at}</code>
订单状态: <code>{pay.status}</code> (1:等待支付 2:支付成功 3:已过期)
订单数据库 ID: <code>{pay.id}</code>
支付用户 ID: <code>{pay.user_id}</code>

⚠⚠⚠注意:
**1. 转账一分也不能少，小数点也要准确支付才能到账，否则后果自负。**
**2. 订单在 10 分钟内超时，过期不候！**
**3. 遇到支付问题请带着用户ID及时联系供需频道主！**
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

    async def MEDIAPROREQ(self) -> str:
        """图文供需"""
        string = f"""
发布图文供需也要严格按照供需格式来哦,点击可以复制.
供应格式:
<code>{await self.PROVIDE()}</code>

需求格式:
<code>{await self.REQUIRE()}</code>
"""
        return string

    async def onceCost(self) -> float:
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

    def choosePayAmountButton(self) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="0.1", callback_data=f"{CallBackData.PAY}/0.1"),
            InlineButton(text="5", callback_data=f"{CallBackData.PAY}/5"),
            InlineButton(text="10", callback_data=f"{CallBackData.PAY}/10"),
            InlineButton(text="20", callback_data=f"{CallBackData.PAY}/20"),
        )
        keyboard.row(
            InlineButton(text="50", callback_data=f"{CallBackData.PAY}/50"),
            InlineButton(text="100", callback_data=f"{CallBackData.PAY}/100"),
            InlineButton(text="200", callback_data=f"{CallBackData.PAY}/200"),
            InlineButton(text="500", callback_data=f"{CallBackData.PAY}/500"),
        )
        return keyboard

    def chooseProvideOrRequireButton(self) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="⭕供给", callback_data=f"{CallBackData.PROVIDE}"),
            InlineButton(text="✔需求", callback_data=f"{CallBackData.REQUIRE}"),
        )
        keyboard.row(
            InlineButton(
                text="💯图文供需", callback_data=f"{CallBackData.MEDIAPROREQ}"
            )
        )

        return keyboard

    async def channelButton(self, client: Client) -> InlineKeyboardMarkup:
        """添加到频道的按钮"""
        me = await client.get_me()
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineButton(text="供给自助发布", url=f"https://t.me/{me.username}"),
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


def try_float(s: str) -> Optional[float]:
    try:
        f = float(s)
        return f
    except ValueError:
        return None


def remove_first_line(text: str) -> str:
    lines = text.split("\n")
    return "\n".join(lines[1:])


# ====== helper function end ====


async def send_media_msg(
    client: Client,
    media_msg: Message,
    chat_id: int,
    caption: str,
    reply_markup=None,
):
    if media_msg.media == MessageMediaType.STICKER:
        file_id = media_msg.sticker.file_id
        file_byte: Union[BinaryIO, str, None] = await client.download_media(
            message=file_id, in_memory=True, file_name="test.jpg"
        )
        if file_byte:
            return await client.send_photo(
                chat_id=chat_id,
                photo=file_byte,
                caption=caption,
                reply_markup=reply_markup,  # type:ignore
            )

    elif media_msg.media == MessageMediaType.PHOTO:
        file_id = media_msg.photo.file_id
        return await client.send_photo(
            chat_id=chat_id,
            photo=file_id,
            caption=caption,
            reply_markup=reply_markup,  # type:ignore
        )
    elif media_msg.media == MessageMediaType.VIDEO:
        file_id = media_msg.video.file_id
        return await client.send_video(
            chat_id=chat_id,
            video=file_id,
            caption=caption,
            reply_markup=reply_markup,  # type:ignore
        )

    return None


async def send_media_proreq(
    client: Client, message: Message, from_user: types.User
):
    """发布图文供需"""

    await message.reply(
        text=await content.MEDIAPROREQ(), reply_markup=content.KEYBOARD()
    )
    content_msg: Optional[Message] = await askQuestion(
        queston="第一步:发送按格式供需文本（限时120s）",
        client=client,
        message=message,
        timeout=120,
    )
    if not content_msg:
        return
    if not content_msg.text:
        return await message.reply("无法识别出文字???")

    async with AsyncSessionMaker() as session:
        config: Config = await ConfigCurd.getConfig(session)
        matches = [
            ban_word
            for ban_word in config.banWordList
            if ban_word in content_msg.text
        ]
        if matches:
            return await content_msg.reply(
                text=f"您发布的内容中含有违禁词！{matches} 请检查后重新发送！",
                reply_markup=content.KEYBOARD(),
            )

    media_msg: Optional[Message] = await askQuestion(
        queston=f"第一步已经完成,您的信息:\n<code>\n{content_msg.text}\n</code>\n\n 第二步就要发送你的图片/视频/贴纸（限时120s）",
        client=client,
        message=message,
        timeout=120,
    )

    if not media_msg:
        return

    msg: Optional[Message] = await send_media_msg(
        client=client,
        media_msg=media_msg,
        chat_id=message.chat.id,
        caption=content_msg.text
        + f"\n**以上是你发送到频道的信息,发送图文供需需要消耗:{config.pic_once_cost} USDT,请再三确认**\n",
        reply_markup=content.confirmButton(),
    )
    if not msg:
        return await message.reply("请发送图片/视频/贴纸!")
    cq: CallbackQuery = await cd.moniterCallback(msg, timeout=30)

    if cq.data == CallBackData.YES:
        async with AsyncSessionMaker() as session:
            user = await UserCurd.registerUser(
                session,
                user=User(username=from_user.username, user_id=from_user.id),
            )

            if user.amount <= 0:
                await message.reply(
                    "💔💔💔对不起,你的没钱了,赶紧充值！！！",
                    reply_markup=content.KEYBOARD(),
                )
                return

            config: Config = await ConfigCurd.getConfig(session)
            config = config.replaceConfig(
                custom=CustomParam(
                    sendCountent=content_msg.text, count=user.count + 1
                )
            )

            # add send author
            send_content_review = f"{config.send_content}\n{user.getUserLink()}"

            # support multi channel
            send_msg_links = []
            for channel_id in config.sendChannelIDs:
                send_msg: Optional[Message] = await send_media_msg(
                    client=client,
                    media_msg=media_msg,
                    chat_id=channel_id,
                    caption=send_content_review,
                    reply_markup=await content.channelButton(client),
                )
                if send_msg:
                    send_msg_links.append(send_msg.link)

            send_msg_links = ",".join(send_msg_links)

            # 发送成功后付费
            user_end = await UserCurd.payPic(session, user)
            # 并记录用户发送的信息
            store_send_msg: Msg = await MsgCURD.addMsg(
                session,
                msg=Msg(
                    user_id=user_end.user_id,
                    content=content_msg.text,
                    amount=config.pic_once_cost,
                    url=str(send_msg_links),
                ),
            )

            await session.commit()
            await msg.delete()
            await message.reply(
                text=f"供需发送频道成功,您的信息:\n{content.USER_INFO(user_end)} \n发送时间:{store_send_msg.send_at}\n扣除余额:{store_send_msg.amount}\n频道链接:{store_send_msg.url}",
                reply_markup=content.KEYBOARD(),
            )


# ===== Handle ======


@app.on_callback_query()
@capture_err
async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    """处理按钮回调数据"""
    await cd.addCallback(callback_query)

    # 返回
    if callback_query.data == CallBackData.RETURN:
        await callback_query.message.edit(
            text=await content.start(),
        )

    # 选择需求
    if callback_query.data == CallBackData.REQUIRE:
        await callback_query.message.delete(revoke=True)

        await callback_query.message.reply(
            text=f"需求模板如下,点击可以复制,回复此信息发送:\n<code>{await content.REQUIRE()}</code>",
            reply_markup=ForceReply(
                selective=False, placeholder=f"请按照格式回复需求内容"
            ),
        )

    # 发送普通供需
    if callback_query.data == CallBackData.PROVIDE:
        await callback_query.message.delete(revoke=True)

        await callback_query.message.reply(
            text=f"供给模板如下,点击可以复制,回复此信息发送:\n<code>{await content.PROVIDE()}</code>",
            reply_markup=ForceReply(
                selective=False, placeholder=f"请按照格式回复供给内容"
            ),
        )

    # 充值
    elif callback_query.data.startswith(CallBackData.PAY):  # type: ignore
        async with AsyncSessionMaker() as session:
            config = await ConfigCurd.getConfig(session)
            # 新建一个用户对象防止用户没有注册
            user = await UserCurd.registerUser(
                session,
                user=User(
                    username=callback_query.from_user.username,
                    user_id=callback_query.from_user.id,
                ),
            )

            amount: str = callback_query.data.split("/")[-1]  # type: ignore

            trade_id, actual_amount, token = await epsdk.createPay(
                amount=amount
            )
            pay = Pay(
                user_id=user.user_id,
                trade_id=trade_id,
                amount=amount,
            )
            rePay = await PayCurd.createNewPay(session, pay=pay)

            await callback_query.message.edit(
                text=content.PAY_INFO(
                    pay=rePay,
                    actual_amount=actual_amount,
                    token=token,
                    config=config,
                )
            )

    # 发送图文供需
    elif callback_query.data == CallBackData.MEDIAPROREQ:
        await send_media_proreq(
            client=client,
            message=callback_query.message,
            from_user=callback_query.from_user,
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
        text="请选择需求还是供应,新增图文供需功能！！",
        reply_markup=content.chooseProvideOrRequireButton(),
    )


def contains_all_keywords(string, keywords: List[str]) -> bool:
    for keyword in keywords:
        if keyword not in string:
            return False
    return True


async def send_common_msg_to_channel(
    session: AsyncSession, message: Message, client: Client, delMsg: Message
):
    """发送普通信息到供需频道"""
    user = await UserCurd.registerUser(session, user=User.generateUser(message))

    if user.amount <= 0:
        await message.reply(
            "💔💔💔对不起,你的没钱了,赶紧充值！！！", reply_markup=content.KEYBOARD()
        )
        return

    config: Config = await ConfigCurd.getConfig(session)
    config = config.replaceConfig(
        custom=CustomParam(sendCountent=message.text, count=user.count + 1)
    )

    # add send author
    send_content_review = f"{config.send_content}\n{user.getUserLink()}"

    # support multi channel
    send_msg_links = []
    for channel_id in config.sendChannelIDs:
        send_msg = await client.send_message(
            chat_id=channel_id,
            text=send_content_review,
            reply_markup=await content.channelButton(client),
            disable_web_page_preview=True,
        )
        send_msg_links.append(send_msg.link)

    send_msg_links = ",".join(send_msg_links)

    # 发送成功后付费
    user_end = await UserCurd.payCommon(session, user)
    # 并记录用户发送的信息
    store_send_msg: Msg = await MsgCURD.addMsg(
        session,
        msg=Msg(
            user_id=user_end.user_id,
            content=message.text,
            amount=config.once_cost,
            url=str(send_msg_links),
        ),
    )

    await session.commit()
    await delMsg.delete()
    await message.reply(
        text=f"供需发送频道成功,您的信息:\n{content.USER_INFO(user_end)} \n发送时间:{store_send_msg.send_at}\n扣除余额:{store_send_msg.amount}\n频道链接:{store_send_msg.url}",
        reply_markup=content.KEYBOARD(),
    )


@app.on_message(filters=filters.reply & filters.private & ~filters.me)
@capture_err
async def handle_reply_message(client: Client, message: Message):
    """处理回复的供需信息,并进行发布"""
    # # first check
    # privideKws = ["名称", "介绍", "联系人", "价格"]
    # requireKws = ["需求", "联系人", "预算"]
    # if not (
    #     contains_all_keywords(message.text, privideKws)
    #     or contains_all_keywords(message.text, requireKws)
    # ):
    #     return await message.reply(
    #         f"请严格按照格式发布!\n供给包含:{privideKws}\n需求包含:{requireKws}"
    #     )

    # ban word check
    async with AsyncSessionMaker() as session:
        config: Config = await ConfigCurd.getConfig(session)
        matches = [
            ban_word
            for ban_word in config.banWordList
            if ban_word in message.text
        ]
        if matches:
            return await message.reply(
                text=f"您发布的需求中含有违禁词！{matches} 请检查后重新发送！",
                reply_markup=content.KEYBOARD(),
            )

    msg: Message = await message.reply(
        text=f"您的普通供给需求信息,是否确定发送,发送成功后将扣除 {config.once_cost} 余额:\n<code>{message.text}</code>",
        reply_markup=content.confirmButton(),
    )
    cq: CallbackQuery = await cd.moniterCallback(msg, timeout=30)

    if cq.data == CallBackData.YES:
        async with AsyncSessionMaker() as session:
            await send_common_msg_to_channel(
                session, message=message, client=client, delMsg=msg
            )


@app.on_message(
    filters=filters.regex(content.WYCZ) & filters.private & ~filters.me
)
@capture_err
async def pay_usdt(client: Client, message: Message):
    # support amount button

    await message.reply(
        text="请选择你要充值的USDT:**(0.1为测试平台所用)**",
        reply_markup=content.choosePayAmountButton(),
    )


@app.on_message(
    filters=filters.regex(content.GRZX) & filters.private & ~filters.me
)
@capture_err
async def account_info(client: Client, message: Message):
    async with AsyncSessionMaker() as session:
        user = await UserCurd.getUserByID(session, user_id=message.from_user.id)
        if not user:
            await message.reply_text(
                "用户未注册!正在注册!", reply_markup=content.KEYBOARD()
            )
            user = await UserCurd.registerUser(
                session, user=User.generateUser(message)
            )

        # 调出用户的充值记录
        pay_string_list = user.getUserPays()
        string = "\n".join(pay_string_list)

        await message.reply_text(
            f"{content.USER_INFO(user)}\n支付记录:\n{string}",
            reply_markup=content.KEYBOARD(),
        )


@app.on_message(
    filters=filters.regex(content.FBJL) & filters.private & ~filters.me
)
@capture_err
async def send_msg_info(client: Client, message: Message):
    """发布记录"""
    async with AsyncSessionMaker() as session:
        user = await UserCurd.getUserByID(session, user_id=message.from_user.id)
        if not user:
            await message.reply_text(
                "用户未注册!正在注册!", reply_markup=content.KEYBOARD()
            )
            user = await UserCurd.registerUser(
                session, user=User.generateUser(message)
            )

        # 调出用户的发布记录
        msg_string_list = user.getUserMsg()
        string = "\n".join(msg_string_list)

        await message.reply_text(
            f"❤您的发布记录如下❤\n{string}", reply_markup=content.KEYBOARD()
        )


@app.on_message(filters=filters.command("getID") & ~filters.me)
@capture_err
async def get_ID(client: Client, message: Message):
    await message.reply(
        f"当前会话的ID:<code>{message.chat.id}</code>",
        reply_markup=content.KEYBOARD(),
    )


# ==== Handle end =====


def getBeijingTime() -> datetime:
    """获取北京时间"""
    utc_now = datetime.utcnow()
    beijing_offset = timedelta(hours=8)
    beijing_now = utc_now + beijing_offset
    return beijing_now


def isTimeout(datetime_obj: datetime):
    """判断是否超时"""
    now = getBeijingTime()
    time_difference = now - datetime_obj
    if time_difference >= timedelta(minutes=9):
        return True
    else:
        return False


async def checkPayStatus(session: AsyncSession, client: Client):
    unNoticePaysRes = await session.execute(
        select(Pay).where(Pay.notice == False)
    )
    unNoticePays = unNoticePaysRes.scalars().all()
    # logger.info(f"当前未提醒的支付数:{len(unNoticePays)}")
    for unNoticePay in unNoticePays:
        if unNoticePay.status == 2:
            noticePay = await PayCurd.noticedUser(session, pay=unNoticePay)
            await client.send_message(
                chat_id=int(noticePay.user_id),
                text=f"订单号:<code>{noticePay.trade_id}</code>\n时间:{noticePay.pay_at}\n请求支付{noticePay.amount}USDT 已经支付成功!👩阿里嘎多！👩",
                reply_markup=content.KEYBOARD(),
            )
            continue
        timeout = isTimeout(datetime_obj=unNoticePay.pay_at)
        if timeout or unNoticePay.status == 3:
            # 手动设置 status=3 已过期
            await session.execute(
                update(Pay)
                .where(Pay.trade_id == unNoticePay.trade_id)
                .values(status=3)
            )
            noticePay = await PayCurd.noticedUser(session, pay=unNoticePay)
            await client.send_message(
                chat_id=int(noticePay.user_id),
                text=f"订单号:<code>{noticePay.trade_id}</code>\n时间:{noticePay.pay_at}\n请求支付{noticePay.amount} USDT\n**已经超时!请重新发起支付!**",
                reply_markup=content.KEYBOARD(),
            )


async def loopCheckPayStatus(client: Client):
    """循环遍历监听 pays 表,查看是否有用户交易成功或者超时,并发送提醒"""
    while True:
        async with AsyncSessionMaker() as session:
            try:
                await checkPayStatus(session=session, client=client)
            except Exception as exc:
                logger.exception(f"check pay status error:{exc}")
        await asyncio.sleep(1)


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

    # 开一个 coroutine 监听
    asyncio.ensure_future(loopCheckPayStatus(client=app))

    await idle()
    await app.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(main())
        loop.run_until_complete(asyncio.sleep(3.0))  # task cancel wait 等待任务结束
