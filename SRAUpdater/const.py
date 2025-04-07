import sys
from pathlib import Path
import rich
import art

__VERSION__ = "v3.0.0-bug-fixed"
""" 当前版本号 """
__AUTHOR__ = ["Shasdow", "Fuxuan-CN"]
""" 作者 """

SUPPORT_ANSI = rich.get_console().is_terminal
""" 是否支持ANSI """
FROZEN: bool = getattr(sys, 'frozen', False)
""" 是否被打包成exe文件 """
GITHUB_URL: str = "https://github.com/Shasnow/StarRailAssistant/releases/download/v{version}/StarRailAssistant_v{version}.zip"
""" Github下载地址 """
RESOURCE_URL: str = "https://github.com/Shasnow/SRAresource/releases/download/resource/resource.zip"
""" 资源文件下载地址 """
HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Referer": "https://github.com/",
    "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6"
}
""" 请求头 """
APP_PATH: Path = Path(sys.executable).parent.absolute() if FROZEN else Path(__file__).parent.absolute()
""" 程序运行路径 """
VERSION_FILE: Path = APP_PATH / "version.json"
""" 版本文件路径 """
VERSION_DIR: Path = APP_PATH
""" 版本文件目录 """
VERSION_URL: str = "https://gitee.com/yukikage/StarRailAssistant/releases/download/release/version.json"
""" 版本文件下载地址 """
RESOURCE_DIR: Path = APP_PATH / "data"
""" 资源文件目录 """
HASH_URL: str = "https://gitee.com/yukikage/sraresource/raw/main/SRA/hash.json"
""" hash文件下载地址 """
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