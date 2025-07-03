import sys
import json
import base64
import win32crypt
from pathlib import Path
import rich
import art

__VERSION__ = "v3.5.0"
""" 当前版本号 """
__AUTHOR__ = ["Shasnow", "Fuxuan-CN", "DLmaster_361"]
""" 作者 """

GLOBAL_CONSOLE = rich.get_console()
""" 全局控制台 """
FROZEN: bool = getattr(sys, "frozen", False)
""" 是否被打包成exe文件 """
GITHUB_URL: str = (
    "https://github.com/Shasnow/StarRailAssistant/releases/download/{version}/StarRailAssistant_{version}.zip"
)
""" Github下载地址 """
HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Referer": "https://github.com/",
    "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
}
""" 请求头 """
APP_PATH: Path = (
    Path(sys.executable).parent.absolute()
    if FROZEN
    else Path(__file__).parent.absolute()
)
""" 程序运行路径 """
VERSION_FILE: Path = APP_PATH / "version.json"
""" 版本文件路径 """
VERSION_DIR: Path = APP_PATH
""" 版本文件目录 """
VERSION_URL: str = (
    "https://mirrorchyan.com/api/resources/StarRailAssistant/latest?current_version=v{Version}&cdk={CDK}&user_agent=SRAUpdater&channel={Channel}"
)
""" 主版本号获取地址 """
RESOURCE_VERSION_URL: str = (
    "https://mirrorchyan.com/api/resources/StarRailAssistantResource/latest?current_version={Version}&cdk={CDK}&user_agent=SRAUpdater&channel={Channel}"
)
""" 资源文件版本号获取地址 """
RESOURCE_DIR: Path = APP_PATH / "data"  # 疑似无用
""" 资源文件目录 """
if (APP_PATH / "data/globals.json").exists():
    with (APP_PATH / "data/globals.json").open(mode="r", encoding="utf-8") as f:
        config = json.load(f)
    if "Settings" in config and "mirrorchyanCDK" in config["Settings"]:
        _MIRROR_CHYAN_CDK = (
            win32crypt.CryptUnprotectData(
                base64.b64decode(config["Settings"]["mirrorchyanCDK"]),
                None,
                None,
                None,
                0,
            )[1].decode("utf-8")
            if config["Settings"]["mirrorchyanCDK"]
            else ""
        )
    else:
        _MIRROR_CHYAN_CDK = ""
else:
    _MIRROR_CHYAN_CDK = ""
MIRROR_CHYAN_CDK: str = _MIRROR_CHYAN_CDK
""" Mirror酱CDK """
ERROR_REMARK_DICT: dict = {
    1001: "获取版本信息的URL参数不正确",
    7001: "填入的 CDK 已过期",
    7002: "填入的 CDK 错误",
    7003: "填入的 CDK 今日下载次数已达上限",
    7004: "填入的 CDK 类型和待下载的资源不匹配",
    7005: "填入的 CDK 已被封禁",
    8001: "对应架构和系统下的资源不存在",
    8002: "错误的系统参数",
    8003: "错误的架构参数",
    8004: "错误的更新通道参数",
}
""" 错误码字典 """
HASH_URL: str = "https://gitee.com/yukikage/sraresource/raw/main/SRA/hash.json"
""" hash文件下载地址 """
ANNOUNCEMENT_URL: str = "https://gitee.com/yukikage/sraresource/raw/main/SRA/announcement.json"
""" 公告文件下载地址 """
API_URL: str = "https://gitee.com/yukikage/sraresource/raw/main/SRA/api.json"
""" api文件下载地址 """
HASH_FILE: Path = APP_PATH / "data/hash.json"
""" hash文件路径 """
TEMP_DOWNLOAD_DIR: Path = APP_PATH / "temp"
""" 下载临时目录 """
TEMP_DOWNLOAD_FILE: Path = TEMP_DOWNLOAD_DIR / "SRAUpdate.zip"
""" 下载临时文件 """
DOWNLOADING_FILE: Path = TEMP_DOWNLOAD_DIR / "SRAUpdate.zip.downloaded"
""" 正在下载文件 """
UPDATE_EXTRACT_DIR: Path = APP_PATH
""" 更新解压目录 """
UPDATED_PATH: Path = UPDATE_EXTRACT_DIR
""" 更新后的程序路径 """
LOGO = art.text2art("SRAUpdater", font="standard")
""" 启动logo """
