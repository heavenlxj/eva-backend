import aiohttp
from fastapi import HTTPException


class AppConfigService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.endpoint = f"{base_url}/v1/miniprogram/config"

    async def get_config_by_key(self, key: str, version: str = None) -> dict:
        """
        根据key获取配置，支持带版本和不带版本
        :param key: 配置键
        :param version: 版本号，可选
        :return: 配置数据
        """
        async with aiohttp.ClientSession() as sess:
            try:
                url = f"{self.endpoint}/current"
                params = {"key": key}
                if version:
                    params["version"] = version
                
                response = await sess.get(
                    url,
                    params=params
                )
                response.raise_for_status()
                result = await response.json()
                print(result)
                return result.get('data', result)
            except aiohttp.ClientError as e:
                raise HTTPException(status_code=500, detail=f"Error fetching config: {str(e)}") 