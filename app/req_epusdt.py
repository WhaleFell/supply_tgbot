import httpx
import hashlib
import urllib.parse
from typing import Dict, Tuple, Union
import asyncio
from datetime import datetime


class EpusdtException(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class EpusdtSDK(object):
    def __init__(self, base_url: str, callback_url: str, sign_key: str) -> None:
        self.base_url = base_url
        self.callback_url = callback_url
        self.sign_key = sign_key

    def epusdtSign(self, parameter: Dict[str, str], signKey: str) -> str:
        parameter = dict(sorted(parameter.items()))
        sign = ""
        urls = ""
        for key, val in parameter.items():
            if val == "":
                continue
            if key != "signature":
                if sign != "":
                    sign += "&"
                    urls += "&"
                sign += f"{key}={val}"
                urls += f"{key}={urllib.parse.quote(str(val).encode())}"
        sign = hashlib.md5(f"{sign}{signKey}".encode()).hexdigest()
        return sign

    def handleAmount(self, amount: Union[str, float, int]) -> Union[int, float]:
        try:
            return int(amount)
        except:
            pass

        try:
            return float("%.2f" % amount)
        except:
            pass

        raise EpusdtException(f"{amount} 格式化错误!")

    async def createPay(self, amount: float) -> Tuple[str, str, str]:
        """
        请求 EPusdt API 新建一个交易,返回交易的 trade_id:str actual_amount:str 实际交易的金额 token:str 交易的 token
        """
        data: dict = {
            "order_id": datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3],
            "amount": self.handleAmount(amount),
            "notify_url": self.callback_url,
            "redirect_url": "",
        }
        sign = self.epusdtSign(parameter=data, signKey=self.sign_key)
        data.update({"signature": sign})
        async with httpx.AsyncClient() as client:
            result = await client.post(
                url=f"{self.base_url}/api/v1/order/create-transaction",
                json=data,
            )
            jdata = result.json()
            if jdata["status_code"] == 200:
                return (
                    jdata["data"]["trade_id"],
                    jdata["data"]["actual_amount"],
                    jdata["data"]["token"],
                )

            raise EpusdtException(f"{data} Response: {result.text}")


async def main():
    epusdtSDK = EpusdtSDK(
        base_url="http://192.168.8.1:8966",
        callback_url="http://192.168.8.219:8000/pay/callback",
        sign_key="lovehyy9420",
    )
    await epusdtSDK.createPay(amount=10.88)


if __name__ == "__main__":
    asyncio.run(main())
