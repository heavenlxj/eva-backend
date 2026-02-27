from typing import Optional

import aiohttp
from fastapi import HTTPException


class StorageService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.upload_endpoint = f"{base_url}/v1/storage/upload"

    async def upload_file(
        self,
        file: bytes,
        bucket_name: str,
        directory_prefix: str,
        file_type: str,
        filename: str = None
    ) -> Optional[str]:
        """
        上传文件到存储服务
        
        Args:
            file: 文件字节数据
            bucket_name: 存储桶名称
            directory_prefix: 目录前缀
            file_type: 文件类型
            filename: 文件名（可选）
        
        Returns:
            dict: 上传响应数据
        
        Raises:
            HTTPException: 当上传失败时抛出
        """
        async with aiohttp.ClientSession() as sess:
            try:
                form_data = aiohttp.FormData()
                form_data.add_field(
                    'file',
                    file,
                    filename=filename or 'file'
                )
                form_data.add_field('bucket_name', bucket_name)
                form_data.add_field('directory_prefix', directory_prefix)
                form_data.add_field('file_type', file_type)

                response = await sess.post(
                    self.upload_endpoint,
                    data=form_data
                )
                response.raise_for_status()
                result = await response.json()
                if result['code'] == 200:
                    return result['data']
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error uploading file: {str(e)}"
                )

            return None
