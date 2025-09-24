import sys
from pathlib import Path

VERSION = "4.0.0"
AUTHOR = "Shasnow, Fuxuan-CN, DLmaster_361"  # NOQA
FROZEN: bool = getattr(sys, "frozen", False)
APP_PATH: Path = Path(sys.argv[0]).parent.absolute()
GITHUB_URL: str = (
    "https://github.com/Shasnow/StarRailAssistant/releases/download/{version}/StarRailAssistant_{version}.zip"
)
API_URL: str = "https://gitee.com/yukikage/sraresource/raw/main/SRA/api.json"
HASH_URL: str = "https://gitee.com/yukikage/sraresource/raw/main/SRA/hash.json"
ANNOUNCEMENT_URL: str = "https://gitee.com/yukikage/sraresource/raw/main/SRA/announcement.json"
VERSION_URL = "https://mirrorchyan.com/api/resources/StarRailAssistant/latest?current_version=v{version}&cdk={cdk}&user_agent=SRAUpdater&channel={channel}"
TEMP_DOWNLOAD_DIR: Path = APP_PATH / "temp"
""" 下载临时目录 """
TEMP_DOWNLOAD_FILE: Path = TEMP_DOWNLOAD_DIR / "SRAUpdate.zip"
""" 下载临时文件 """
DOWNLOADING_FILE: Path = TEMP_DOWNLOAD_DIR / "SRAUpdate.zip.downloaded"
""" 正在下载文件 """
HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Referer": "https://github.com/",
    "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
}
""" 请求头 """
ERROR_REMARK_DICT: dict[int, str] = {
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
