import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from time import sleep
from packaging import version
from typing import Generator
from urllib.parse import urlparse
import requests
from rich.progress import track
from rich.panel import Panel
from rich.style import Style

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
    GITHUB_URL,
    VERSION_URL,
    RESOURCE_VERSION_URL,
    APP_PATH,
    LOGO,
    GLOBAL_CONSOLE,
    MIRROR_CHYAN_CDK,
    ERROR_REMARK_DICT,
)
from .data_models import VersionInfo
from .exec_hook import set_exechook, ExtractException
from .help_beautiful import RichHelpFormatter
from .process_bar import download_progress_bar
from .updater_logger import logging
from .utils import Castorice


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
        self.console = GLOBAL_CONSOLE
        self.__config_console()
        self.__print_logo()
        self.init_version_file()
        self.proxys = []
        self.get_proxys()
        self.no_proxy = False
        self.verify_ssl = True
        self.force_update = False
        self.if_use_mirrorchyan = True
        set_exechook()

    def __config_console(self) -> None:
        """
        配置控制台。
        """
        self.console._highlight = False
        self.console.legacy_windows = True

    @staticmethod
    def __auto_headers(url: str) -> dict[str, str]:
        """
        自动生成请求头。
        """
        headers = HEADERS.copy()
        # 提取URL中的域名
        parse_result = urlparse(url)
        domain_url = rf"{parse_result.scheme}://{parse_result.netloc}"
        headers["Referer"] = domain_url
        headers["Host"] = parse_result.netloc
        return headers

    def __error_occurred(
        self,
        action_desc: str | None,
        exc: Exception,
        need_exit: bool = True,
        no_stack: bool = False,
    ) -> None:
        """
        发生异常后打印错误信息。
        """
        self.logger.error(f"在尝试'{action_desc}'的时候发生错误: {exc}")
        if not no_stack:
            stack = ExtractException(type(exc), exc, exc.__traceback__, panel=True)
            self.console.print(stack)
        if need_exit:
            sys.exit(1)

    def __print_logo(self):
        """
        打印启动logo。
        """
        self.console.print(LOGO, style=Style(color="magenta"))
        self.console.print(f"[bold yellow]SRAUpdater {__VERSION__}[/bold yellow]")
        self.console.print(f"[bold blue]作者：({' '.join(__AUTHOR__)})[/bold blue]")
        self.console.print(f"当前路径{APP_PATH}")
        self.console.print(f"[bold grey]{'=' * self.console.width}")

    def init_version_file(self):
        """
        初始化版本信息文件。
        """
        try:
            if not VERSION_FILE.exists():
                self.logger.info("初始化版本信息...")
                version_info = {
                    "version": "0.0.0",
                    "resource_version": "0.0.0",
                    "Announcement": "",
                    "Proxys": [
                        "https://github.tbedu.top/",
                        "https://gitproxy.click/",
                        "https://github.akams.cn/",
                        "https://gh-proxy.ygxz.in/",
                        "https://ghps.cc/",
                        "",
                    ],
                }
                if not VERSION_FILE.exists():
                    with open(VERSION_FILE, "w", encoding="utf-8") as json_file:
                        json.dump(version_info, json_file, indent=4)
        except Exception as e:
            self.__error_occurred("初始化版本信息", e, need_exit=True)

    def get_proxys(self):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            self.proxys = json.load(f)["Proxys"]

    @staticmethod
    def get_current_version() -> VersionInfo:
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
            response = requests.get(
                VERSION_URL.format(Version=v.version, CDK="", Channel="stable"),
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            version_info = response.json()
            response = requests.get(
                RESOURCE_VERSION_URL.format(
                    Version=v.version, CDK="", Channel="stable"
                ),
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            resource_version_info = response.json()
        except requests.RequestException as e:
            self.__error_occurred("获取版本信息", e, need_exit=True)
            return ""

        remote_version = version_info["data"]["version_name"]
        remote_resource_version = resource_version_info["data"]["version_name"]
        new_announcement = version_info["data"]["release_note"]

        self.logger.info(f"当前版本：{v.version}")
        self.logger.info(f"当前资源版本：{v.resource_version}")
        self.logger.info(f"远程版本：{remote_version}")
        self.logger.info(f"远程资源版本：{remote_resource_version}")

        if (
            version.parse(remote_version) > version.parse(v.version)
            or self.force_update
        ):
            self.logger.info(f"发现新版本：{remote_version}")
            self.console.print(f"[bold green]发现新版本：{remote_version}[/bold green]")
            self.console.print(f"[bold blue]更新说明：\n{new_announcement}[/bold blue]")

            if MIRROR_CHYAN_CDK:

                response = requests.get(
                    VERSION_URL.format(
                        Version=v.version, CDK=MIRROR_CHYAN_CDK, Channel="stable"
                    ),
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )
                info = response.json()

                if info["code"] == 0:

                    with requests.get(
                        info["data"]["url"],
                        allow_redirects=True,
                        timeout=10,
                        stream=True,
                    ) as response:
                        if response.status_code == 200:
                            return response.url

                else:

                    self.console.print(
                        f"[bold red]Mirror酱获取更新链接失败: {ERROR_REMARK_DICT[info['code']]if info['code'] in ERROR_REMARK_DICT else info['msg']}，转用通用方法更新[/bold red]"
                    )
                    self.if_use_mirrorchyan = False
                    return GITHUB_URL.format(version=remote_version)

            else:

                return GITHUB_URL.format(version=remote_version)

        if version.parse(remote_resource_version) > version.parse(v.resource_version):
            self.logger.info(f"发现资源更新：{remote_resource_version}")
            self.console.print(
                f"[bold green]发现资源更新：{remote_resource_version}[/bold green]"
            )
            self.console.print(
                f"[bold blue]更新说明：\n{resource_version_info["data"]["release_note"]}[/bold blue]"
            )

            if MIRROR_CHYAN_CDK:

                response = requests.get(
                    RESOURCE_VERSION_URL.format(
                        Version=v.resource_version,
                        CDK=MIRROR_CHYAN_CDK,
                        Channel="stable",
                    ),
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )
                info = response.json()

                if info["code"] == 0:

                    with requests.get(
                        info["data"]["url"],
                        allow_redirects=True,
                        timeout=10,
                        stream=True,
                    ) as response:
                        if response.status_code == 200:
                            return response.url

                else:

                    self.console.print(
                        f"[bold red]Mirror酱获取更新链接失败: {ERROR_REMARK_DICT[info['code']]if info['code'] in ERROR_REMARK_DICT else info['msg']}，转用通用方法更新[/bold red]"
                    )
                    self.if_use_mirrorchyan = False
                    self.integrity_check(confirm=True)
                    return ""

            else:

                self.integrity_check(confirm=True)
                return ""

        if new_announcement != v.announcement:
            self.update_announcement(new_announcement)

        self.logger.info("已经是最新版本")
        self.console.print("[bold green]已经是最新版本[/bold green]")
        return ""

    @staticmethod
    def update_announcement(new_announcement: str):
        """
        更新公告信息。
        """
        with open(VERSION_FILE, "r+", encoding="utf-8") as json_file:
            version_info = json.load(json_file)
            version_info["Announcement"] = new_announcement
            json_file.seek(0)
            json.dump(version_info, json_file, indent=4, ensure_ascii=False)
            json_file.truncate()

    def __warp_proxy(self, url: str) -> Generator[str, None, str | None]:
        """
        给下载连接添加代理前缀
        """
        if self.no_proxy or (MIRROR_CHYAN_CDK and self.if_use_mirrorchyan):
            yield url
            return None
        for proxy in self.proxys:
            if isinstance(proxy, str):
                self.logger.debug(f"使用代理: {proxy}")
                url = f"{proxy}{url}"
                yield url
        self.logger.warning("所有代理都尝试完成")
        # 尝试了所有的代理

    def download(self, download_url: str) -> None:
        """
        下载更新文件。
        """
        try:
            if not TEMP_DOWNLOAD_DIR.exists():
                TEMP_DOWNLOAD_DIR.mkdir()
            if TEMP_DOWNLOAD_FILE.exists():
                os.remove(TEMP_DOWNLOAD_FILE)
            self.logger.info("下载更新文件")
            response = requests.get(
                download_url, stream=True, headers=HEADERS, verify=self.verify_ssl
            )
            response.raise_for_status()

            total_size = int(response.headers.get("Content-Length", 0))
            with download_progress_bar as progress:
                task = progress.add_task(
                    "[bold blue]下载中...",
                    filename="SRAUpdate.zip",
                    start=True,
                    total=total_size,
                    completed=0,
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
        except KeyboardInterrupt:
            print("下载更新已取消")
            os.remove(DOWNLOADING_FILE)
            os.system("pause")
            sys.exit(0)

    def unzip(self):
        """
        解压更新文件。
        """
        if Castorice.look("SRA.exe"):
            Castorice.touch("SRA.exe")
            sleep(2)
        if TEMP_DOWNLOAD_FILE.exists():
            try:
                self.logger.info("解压更新文件")
                if not Path.exists(APP_PATH / "tools/7z.exe"):
                    self.console.print(
                        f"[bold red]解压工具丢失，请手动解压{TEMP_DOWNLOAD_FILE}到当前文件夹[/bold red]"
                    )
                    os.system("pause")
                    return
                command = f'"{APP_PATH}\\tools\\7z" x {TEMP_DOWNLOAD_FILE} -y'
                cmd = 'cmd.exe /c start "" ' + command
                Castorice.life(cmd, shell=True)

            except Exception as e:
                self.logger.error(f"解压更新时出错: {e}")
                self.console.print(f"[bold red]解压更新时出错: {e}[/bold red]")
                self.console.print("[bold cyan] 尝试手动解压覆盖试试？ [bold cyan]")

    def integrity_check(self, confirm: bool = False):
        """
        检查文件完整性。
        """
        try:
            self.logger.info("检查文件完整性...")
            response = requests.get(HASH_URL, timeout=10)
            saved_hashes = response.json()
            # self.logger.debug(saved_hashes)
        except requests.RequestException as e:
            self.__error_occurred("获取哈希值", e, need_exit=True)
            return

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
            self.console.print(
                f"[bold yellow]{len(inconsistent_files)} 个文件丢失或不是最新的[/bold yellow]"
            )
            if not confirm:
                ans = input("是否开始下载缺失文件？(Y/n)")
                if ans.strip().lower() == "n":
                    return
            if Castorice.look("SRA.exe"):
                Castorice.touch("SRA.exe")
                sleep(2)
            self.download_all(inconsistent_files)
        else:
            self.logger.info("所有文件均为最新")
            self.console.print(
                "[bold green]检查完成，没有文件损坏或者丢失[/bold green]"
            )

    @staticmethod
    def hash_calculate(file_path, hash_algo=hashlib.sha256):
        """
        计算文件的哈希值。
        """
        with open(file_path, "rb") as f:
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
                self.simple_download(
                    f"https://pub-f5eb43d341f347bb9ab8712e19a5eb51.r2.dev/SRA/{file.as_posix()}",
                    file,
                )
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
        panel = Panel(
            f"{panel_msg}",
            style=Style(color="green"),
            title="[bold yellow]版本信息[bold yellow]",
        )
        self.console.print(panel)

    def simple_download(self, url: str, path: str | Path):
        """
        简单下载文件。
        """
        try:
            self.logger.info(f"正在下载 {path} ...")
            response = requests.get(url, stream=True, headers=HEADERS)
            response.raise_for_status()
            total_size = int(response.headers.get("Content-Length", 0))
            with open(UPDATED_PATH / path, "wb") as f:
                for chunk in track(
                    response.iter_content(chunk_size=8192),
                    total=total_size / 8192,
                    description=path,
                ):
                    f.write(chunk)

            self.logger.info(f"{path} 下载完成")
        except requests.RequestException as e:
            self.logger.warning(f"下载更新时出错: {e}")

    @staticmethod
    def launch_with_args() -> None:
        """
        带参数启动。
        """

        if sys.platform == "win32":
            if any(arg.startswith("--multiprocessing-fork") for arg in sys.argv):
                return

        parser = argparse.ArgumentParser(
            prog="SRAUpdater",
            description="SRA更新器命令行工具",
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument("-u", "--url", help="指定文件下载链接")
        # parser.add_argument("-d","--directory", help="The directory where the file was downloaded")
        parser.add_argument(
            "-p",
            "--proxy",
            nargs="+",
            help="代理链接，如果没有则使用默认的内置代理列表",
        )
        parser.add_argument("-np", "--no-proxy", action="store_true", help="不使用代理")
        parser.add_argument(
            "-nv", "--no-verify", action="store_true", help="不要进行SSL证书验证"
        )
        parser.add_argument(
            "-v", "--version", action="store_true", help="获取当前版本信息"
        )
        parser.add_argument("-f", "--force", action="store_true", help="强制更新")
        parser.add_argument(
            "-i", "--integrity-check", action="store_true", help="检查文件完整性"
        )
        parser.add_argument(
            "-vb", "--verbose", action="store_true", help="显示详细日志信息"
        )
        parser.add_argument(
            "-timeout", "--timeout", type=int, default=10, help="设置请求超时时间"
        )
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
            updater.proxys.insert(0, args.proxy)

        if args.no_verify:
            updater.verify_ssl = False

        if args.force:
            updater.force_update = True

        if args.url is not None:
            updater.download(args.url)
            updater.unzip()
        else:
            updater.check_for_updates()


if __name__ == "__main__":
    sra_updater = SRAUpdater()
    sra_updater.check_for_updates()
