from .updater_logger import logging
from .const import (
    HEADERS, 
    VERSION_FILE,
    UPDATED_PATH,
    TEMP_DOWNLOAD_FILE, 
    DOWNLOADING_FILE, 
    TEMP_DOWNLOAD_DIR, 
    HASH_URL,
    __VERSION__,
    __AUTHOR__,
    UPDATE_EXTRACT_DIR,
    VERSION_URL
)
from .data_models import VersionInfo
from .process_bar import download_progress_bar
from .help_beautiful import RichHelpFormatter
from .decorators import Issue
from pathlib import Path
import json
import requests
import hashlib
from rich.console import Console
import argparse
from rich.panel import Panel
from rich.style import Style
import art
import sys
import zipfile
from typing import Generator
from .exec_hook import set_exechook, ExtractException
from urllib.parse import urlparse

class SRAUpdater:
    """
    主要的更新器类，负责版本检查、文件下载、完整性校验和更新应用。
    """

    def __init__(self, verbose: bool = False, timeout: int = 10) -> None:
        self.verbose = verbose
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.verbose:
            logging.disable(logging.DEBUG)
        self.console = Console()
        self.__print_logo()
        self.init_version_file()
        self.proxys = [
            "https://gitproxy.click/",
            "https://cdn.moran233.xyz/",
            "https://gh.llkk.cc/",
            "https://github.akams.cn/",
            "https://www.ghproxy.cn/",
            "https://ghfast.top/"
        ]
        self.no_proxy = False
        self.verify_ssl = True
        set_exechook()

    def __auto_headers(self, url: str) -> dict[str, str]:
        """
        自动生成请求头。
        """
        headers = HEADERS.copy()
        # 提取URL中的域名
        parse_result = urlparse(url)
        domain_url = fr"{parse_result.scheme}://{parse_result.netloc}"
        headers["Referer"] = domain_url
        headers["Host"] = parse_result.netloc
        return headers

    def __error_occurred(self, action_desc: str | None, exc: Exception, need_exit: bool = True, no_stack: bool = False) -> None:
        """
        发生异常后打印错误信息。
        """
        self.logger.error(f"再尝试'{action_desc}'的时候发生错误: {exc}")
        if not no_stack:
            stack = ExtractException(type(exc), exc, exc.__traceback__, panel=True)
            self.console.print(stack)
        if need_exit:
            sys.exit(1)

    def __print_logo(self):
        """
        打印启动logo。
        """
        self.console.print(art.text2art("SRAUpdater", font="big"), style=Style(color="magenta"))
        self.console.print(f"[bold yellow]SRAUpdater {__VERSION__}[/bold yellow]")
        self.console.print(f"[bold blue]作者：({' '.join(__AUTHOR__)})[/bold blue]")
        self.console.print(f"[bold grey]{'=' * self.console.width}")

    def init_version_file(self):
        """
        初始化版本信息文件。
        """
        try:
            if not VERSION_FILE.exists():
                self.logger.info("初始化版本信息...")
                version_info = {"version": "0.0.0", "resource_version": "0.0.0", "Announcement": ""}
                if not VERSION_FILE.exists():
                    with open(VERSION_FILE, "w", encoding="utf-8") as json_file:
                        json.dump(version_info, json_file, indent=4)
        except Exception as e:
            self.__error_occurred("初始化版本信息", e, need_exit=True)

    def get_current_version(self) -> VersionInfo:
        """
        获取当前版本信息。
        """
        with open(VERSION_FILE, "r", encoding="utf-8") as json_file:
            version_info_local = json.load(json_file)
            version = version_info_local.get("version")
            resource_version = version_info_local.get("resource_version")
            announcement = version_info_local.get("Announcement")
        return VersionInfo(version, resource_version, announcement, "")

    def check_for_updates(self):
        """
        检查是否有可用的更新。
        """
        self.logger.info("检查版本信息...")
        version = self.get_current_version()
        try:
            url = self.version_check(version)
            if url:
                for warped_url in self.__warp_proxy(url):
                    try:
                        self.download(warped_url)
                        break
                    except requests.exceptions.RequestException as e:
                        self.logger.warning(f"链接失败: {e}，尝试下一个代理...")
                self.unzip()
        except Exception as e:
            self.__error_occurred("检查并更新", e)

    def version_check(self, v: VersionInfo) -> str:
        """
        检查版本信息，比较本地版本和远程版本。
        """
        try:
            response = requests.get(VERSION_URL, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            version_info = response.json()
        except requests.RequestException as e:
            self.__error_occurred("获取版本信息", e, need_exit=True)

        remote_version = version_info.get("version")
        remote_resource_version = version_info.get("resource_version")
        new_announcement = version_info.get("announcement") if version_info.get("announcement") else version_info.get("Announcement")

        self.logger.info(f"当前版本：{v.version}")
        self.logger.info(f"当前资源版本：{v.resource_version}")
        self.logger.info(f"远程版本：{remote_version}")
        self.logger.info(f"远程资源版本：{remote_resource_version}")

        if remote_version > v.version:
            self.logger.info(f"发现新版本：{remote_version}")
            self.console.print(f"[bold green]发现新版本：{remote_version}[/bold green]")
            self.console.print(f"[bold blue]更新说明：\n{new_announcement}[/bold blue]")
            return f"https://github.com/Shasnow/StarRailAssistant/releases/download/v{remote_version}/StarRailAssistant_v{remote_version}.zip"
        if remote_resource_version > v.resource_version:
            self.logger.info(f"发现资源更新：{remote_resource_version}")
            self.console.print(f"[bold green]发现资源更新：{remote_resource_version}[/bold green]")
            self.console.print(f"[bold blue]更新说明：\n{version_info.get("resource_announcement")}[/bold blue]")
            return ""
        if new_announcement != v.announcement:
            self.update_announcement(new_announcement)
        self.logger.info("已经是最新版本")
        self.console.print("[bold green]已经是最新版本[/bold green]")
        return ""

    def update_announcement(self, new_announcement: str):
        """
        更新公告信息。
        """
        with open(VERSION_FILE, "r+", encoding="utf-8") as json_file:
            version_info = json.load(json_file)
            version_info["Announcement"] = new_announcement
            json_file.seek(0)
            json.dump(version_info, json_file, indent=4, ensure_ascii=False)
            json_file.truncate()

    def __warp_proxy(self, url: str) -> Generator[str, None, None]:
        """
        给下载连接添加代理前缀
        """
        if not self.no_proxy:
            for proxy in self.proxys:
                if isinstance(proxy, str):
                    self.logger.debug(f"使用代理: {proxy}")
                    url = f"{proxy}{url}"
                    yield url
            self.logger.warning("所有代理都尝试完成")
        return url # 尝试了所有的代理

    def download(self, download_url: str) -> None:
        """
        下载更新文件。
        """
        try:
            if not TEMP_DOWNLOAD_DIR.exists():
                TEMP_DOWNLOAD_DIR.mkdir()
            self.logger.info("下载更新文件")
            response = requests.get(download_url, stream=True, headers=HEADERS, verify=self.verify_ssl)
            response.raise_for_status()

            total_size = int(response.headers.get("Content-Length", 0))
            with download_progress_bar as progress:
                task = progress.add_task(
                    "[bold blue]下载中...",
                    filename="SRAUpdate.zip",
                    start=True,
                    total=total_size,
                    completed=0
                )
                with open(DOWNLOADING_FILE, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
                        progress.refresh()
                progress.remove_task(task)
            DOWNLOADING_FILE.rename(TEMP_DOWNLOAD_FILE)
            self.logger.info("下载完成！")
            self.console.print("[bold green]下载完成！[/bold green]")
        except requests.RequestException as e:
            self.__error_occurred("下载更新文件", e)
        except requests.exceptions.SSLError as e:
            self.logger.warning(f"SSL证书验证失败: {e}")
            raise

    @Issue("解压的时候SRAUpdater.exe也会被替换，用于实现更新，但是此进程仍在运行导致PermissionError。", wait_for_look=True)
    def unzip(self):
        """
        解压更新文件。
        """
        if TEMP_DOWNLOAD_FILE.exists():
            try:
                self.logger.info("解压更新文件")
                with zipfile.ZipFile(TEMP_DOWNLOAD_FILE, 'r') as zip_ref:
                    zip_ref.extractall(UPDATE_EXTRACT_DIR)
                TEMP_DOWNLOAD_FILE.unlink()
                if TEMP_DOWNLOAD_DIR.exists():
                    TEMP_DOWNLOAD_DIR.rmdir()
                self.logger.info("解压完成！")
                self.console.print("[bold green]解压完成！[/bold green]")
            except Exception as e:
                self.logger.error(f"解压更新时出错: {e}")
                self.console.print(f"[bold red]解压更新时出错: {e}[/bold red]")
                self.console.print("[bold cyan] 尝试手动解压覆盖试试？ [bold cyan]")

    def integrity_check(self):
        """
        检查文件完整性。
        """
        try:
            self.logger.info("检查文件完整性...")
            response = requests.get(HASH_URL, timeout=10)
            saved_hashes = response.json()
            ## self.logger.debug(saved_hashes)
        except requests.RequestException as e:
            self.__error_occurred("获取哈希值", e, need_exit=True)

        inconsistent_files = []
        for file_path, saved_hash in saved_hashes.items():
            current_path: Path = Path(UPDATED_PATH) / file_path
            if current_path.exists():
                self.logger.debug(f"检查 {file_path} 文件完整性")
                current_hash = self.hash_calculate(current_path)
                if current_hash != saved_hash:
                    self.logger.warning(f"{file_path} 文件不完整或损坏")
                    inconsistent_files.append(Path(file_path))
            else:
                self.logger.debug(f"{file_path} 文件不存在")
                inconsistent_files.append(Path(file_path))

        if inconsistent_files:
            self.logger.info(f"{len(inconsistent_files)} 个文件丢失或不是最新的")
            self.console.print(f"[bold yellow]{len(inconsistent_files)} 个文件丢失或不是最新的[/bold yellow]")
            self.download_all(inconsistent_files)
        else:
            self.logger.info("所有文件均为最新")
            self.console.print("[bold green]检查完成，没有文件损坏或者丢失[/bold green]")

    @staticmethod
    def hash_calculate(file_path, hash_algo=hashlib.sha256):
        """
        计算文件的哈希值。
        """
        with open(file_path, 'rb') as f:
            data = f.read()
            return hash_algo(data).hexdigest()

    def download_all(self, filelist: list[Path]):
        """
        下载所有丢失或不一致的文件。
        """
        self.logger.info("下载所需文件...")
        for file in filelist:
            try:
                if file.exists():
                    file.unlink()
                self.simple_download(f"https://pub-f5eb43d341f347bb9ab8712e19a5eb51.r2.dev/SRA/{file}", file)
            except Exception as e:
                self.__error_occurred(f"下载 {file} 文件", e)
    
    def display_version(self):
        """
        显示当前版本信息。
        """
        ass_ver = self.get_current_version()
        panel_msg = f"""
[bold yellow] 更新器版本: {__VERSION__}[bold yellow] \n
[bold magenta]作者: {' '.join(__AUTHOR__)}[bold blue] \n
[bold green]当前版本: {ass_ver.version}[bold green] \n
[bold green]当前资源版本: {ass_ver.resource_version}[bold yellow] \n
"""
        panel = Panel(f"{panel_msg}", style=Style(color="green"), title="[bold yellow]版本信息[bold yellow]")
        self.console.print(panel)

    def simple_download(self, url: str, path: str):
        """
        简单下载文件。
        """
        try:
            response = requests.get(url, stream=True, headers=HEADERS)
            response.raise_for_status()
            with open(UPDATED_PATH / path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.info(f"{path} 下载完成")
        except requests.RequestException as e:
            self.logger.warning(f"下载更新时出错: {e}")

    @staticmethod
    def update_with_args() -> None:
        """
        命令行参数更新。
        """

        if sys.platform == "win32":
            if any(arg.startswith('--multiprocessing-fork') for arg in sys.argv):
                return
        
        parser = argparse.ArgumentParser(
            prog="SRAUpdater",
            description="星穹铁道助手更新器命令行工具",
            formatter_class=RichHelpFormatter
        )
        parser.add_argument("-u", "--url", help="指定文件下载链接")
        # parser.add_argument("-d","--directory", help="The directory where the file was downloaded")
        parser.add_argument("-p", "--proxy", nargs="+", help="代理链接，如果没有则使用默认的内置代理列表")
        parser.add_argument("-np", "--no-proxy", action="store_true", help="不想使用代理")
        parser.add_argument("-nv", "--no-verify", action="store_true", help="不要进行SSL证书验证")
        parser.add_argument("-v", "--version", action="store_true", help="获取当前版本信息")
        parser.add_argument("-f", "--force", action="store_true", help="强制更新")
        parser.add_argument("-i", "--integrity-check", action="store_true", help="检查文件完整性")
        parser.add_argument("-vb", "--verbose", action="store_true", help="显示详细日志信息")
        parser.add_argument("-timeout", "--timeout", type=int, default=10, help="设置请求超时时间")
        args = parser.parse_args()

        updater = SRAUpdater(args.verbose, args.timeout)

        if args.version:
            updater.display_version()
            return

        if args.integrity_check:
            updater.integrity_check()
            return

        if args.no_proxy:
            updater.no_proxy = True

        if args.proxy:
            updater.proxys.append(args.proxy)

        if args.no_verify:
            updater.verify_ssl = False

        if args.force:
            updater.check_for_updates()
            return

        if args.url is not None:
            updater.download(args.url)
            updater.unzip()
        else:
            updater.check_for_updates()

if __name__ == '__main__':
    sra_updater = SRAUpdater()
    sra_updater.check_for_updates()