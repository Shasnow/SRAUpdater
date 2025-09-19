import dataclasses
import hashlib
import json
from typing import Any

import aiohttp
from loguru import logger

from src import settings
from src.const import VERSION_URL, HEADERS, TEMP_DOWNLOAD_FILE, GITHUB_URL, API_URL


@dataclasses.dataclass
class VersionResponseData:
    """版本响应数据模型"""
    version_name: str = ""
    version_number: int = 0
    url: str = ""
    sha256: str = ""
    channel: str = ""
    os: str = ""
    arch: str = ""
    update_type: str = ""
    filesize: int = 0  # NOQA
    cdk_expired_time: int = 0
    release_note: str = ""

    def __init__(self, data: dict = None):
        if data is None:
            data = {}
        self.version_name = data.get("version_name", "")
        self.version_number = data.get("version_number", 0)
        self.url = data.get("url", "")
        self.sha256 = data.get("sha256", "")
        self.channel = data.get("channel", "")
        self.os = data.get("os", "")
        self.arch = data.get("arch", "")
        self.update_type = data.get("update_type", "")
        self.filesize = data.get("filesize", 0)  # NOQA
        self.cdk_expired_time = data.get("cdk_expired_time", 0)
        self.release_note = data.get("release_note", "")


@dataclasses.dataclass
class VersionResponseBody:
    """版本响应体模型"""
    code: int = 0
    msg: str = ""
    data: VersionResponseData = None


def get_local_version() -> str:
    """获取本地版本号"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            version_data = json.load(f)
        return version_data.get("version", "0.0.0")
    except FileNotFoundError:
        return "0.0.0"
    except json.JSONDecodeError:
        return "0.0.0"


async def get(url, timeout=10) -> dict[str, Any]:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()


async def get_remote_version() -> VersionResponseBody:
    """异步获取远程版本号

    Returns:
        VersionResponseBody: 版本响应数据

    Raises:
        aiohttp.ClientError: 网络请求错误
        asyncio.TimeoutError: 请求超时
        json.JSONDecodeError: JSON 解析错误
    """
    data = await get(VERSION_URL.format(version=get_local_version(), cdk=settings.get_mirrorchyan_cdk(),
                                          channel=settings.get_channel()))
    return VersionResponseBody(code=data.get("code", 0), msg=data.get("msg"),
                               data=VersionResponseData(data.get("data")))


async def download_file_async(url: str, timeout: int = 60, size_callback=None, progress_callback=None) -> None:
    """异步下载文件并支持进度回调

    Args:
        url: 下载链接
        timeout: 超时时间(秒)
        size_callback: 文件大小回调函数，接收总字节数
        progress_callback: 进度回调函数，接收已下载字节数

    Raises:
        aiohttp.ClientError: 网络请求错误
        asyncio.TimeoutError: 请求超时
    """
    import aiohttp
    import os

    # 确保temp目录存在
    os.makedirs(os.path.dirname(TEMP_DOWNLOAD_FILE), exist_ok=True)
    logger.info("开始下载文件: {}", url)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.get(url, headers=HEADERS) as response:
            response.raise_for_status()

            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            if size_callback:
                size_callback(total_size)

            with open(TEMP_DOWNLOAD_FILE, 'wb') as f:
                # 使用chunk_size为8192进行流式下载
                async for chunk in response.content.iter_chunked(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 调用进度回调函数
                        if progress_callback:
                            progress_callback(downloaded_size)


async def download_update_async(version_data: VersionResponseData, timeout: int = 60, size_callback=None,
                                progress_callback=None) -> None:
    """异步下载更新文件并支持进度回调

    Args:
        version_data: 版本响应数据
        timeout: 超时时间(秒)
        size_callback: 文件大小回调函数
        progress_callback: 进度回调函数

    Raises:
        aiohttp.ClientError: 网络请求错误
        asyncio.TimeoutError: 请求超时
    """
    if version_data.url != "":
        await download_file_async(version_data.url, timeout, size_callback, progress_callback)
    else:
        for proxy in settings.get_proxys():
            try:
                await download_file_async(proxy + GITHUB_URL.format(version=version_data.version_name), timeout,
                                          size_callback,
                                          progress_callback)
                return
            except Exception as e:
                logger.error(e)
                continue
        raise Exception("所有代理均无法下载文件，请检查网络连接。")


def hash_calculate(file_path, hash_algo=hashlib.sha256) -> str:
    """
    计算文件的哈希值。
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            return hash_algo(data).hexdigest()
    except FileNotFoundError:
        return ""


async def hash_check(version_data: VersionResponseData) -> bool:
    """
    检查文件的哈希值是否与预期值匹配。
    """
    sha256 = version_data.sha256
    if sha256 == "":
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(API_URL) as response:
                response.raise_for_status()
                data = await response.json()
                sha256 = data.get("sha256", "")
    return sha256 == hash_calculate(TEMP_DOWNLOAD_FILE)


import psutil


# noinspection SpellCheckingInspection
class Castorice:
    """
    - Easter Egg:

    你懂的，因为，她啊，碰一下生命就会导致生命的离去...

    - 介绍: \n
    「欢迎来到奥赫玛，我是遐蝶。
     抱歉，与他人保持一定距离是我的习惯…如果阁下愿意，我自然可以站近些。
    「死荫的侍女」遐蝶 Castorice那敬爱死亡的国度，终日飘雪的哀地里亚，今日已沉入甘甜的酣眠。
    冥河的女儿遐蝶，寻索「死亡」火种的黄金裔，启程吧。
    你要呵护世间魂灵的恸哭，拥抱命运的孤独——生死皆为旅途，当蝴蝶停落枝头，那凋零的又将新生。
    """

    @staticmethod
    def touch(process: str | int) -> None:
        """ 触摸一个进程 """
        try:
            if isinstance(process, str):
                for p in psutil.process_iter():
                    if p.name() == process:
                        _process = psutil.Process(p.pid)
                        _process.kill()
                        return
            else:
                _process = psutil.Process(process)
                _process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    @staticmethod
    def look(process_name: str) -> bool:
        """
        Check if there is any running process that contains the given name string.

        Args:
            process_name (str): Name of the process to be searched.
        Returns:
            True if the process is running, otherwise False.
        """
        # Iterate over all running processes
        for proc in psutil.process_iter(['name']):
            try:
                # Check if process name contains the given name string
                if process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    @staticmethod
    def life(path: str, shell=False) -> bool:
        """运行指定exe程序

        Args:
            shell: 通过shell运行
            path: 程序路径

        Returns:
            True if opened successfully, False otherwise.
        """
        try:
            psutil.Popen(path, shell=shell)
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False
