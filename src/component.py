import asyncio
import time
from pathlib import Path

from loguru import logger
from packaging import version
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import RichLog, Header, Footer, Label, Button, ProgressBar, Collapsible, Markdown, ListView, \
    Static, Input, ListItem, RadioSet, RadioButton

from src import settings
from src.const import AUTHOR, APP_PATH, VERSION, TEMP_DOWNLOAD_FILE, HASH_URL
from src.util import get_local_version, download_update_async, get_remote_version, hash_check, Castorice, get, \
    hash_calculate, download_file_async


class HomeScreen(Screen):
    SUB_TITLE = f"SRA 更新器 {VERSION}"
    BINDINGS = [("s", "app.switch_mode('settings')", "设置"),
                ("i", "app.switch_mode('integrity')", "文件完整性检查"),
                ("q", "app.quit", "退出"),
                ("r", "refresh", "刷新"),
                ("l", "show_logger", "显示/隐藏日志")]

    CSS = """
    RichLog {
        border: round $accent;
        height: 10;
        background: $background;
    }

    #update-button {
        border: round $success;
        background: $background 0%;
        color: $success;
        text-style: bold;
    }

    .disabled {
        display: none;
    }
    """

    def __init__(self):
        super().__init__()
        self.logger = RichLog()
        self.logger.border_title = "日志"
        self.version_response = None
        self.local_version = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Label(f"欢迎使用 SRA 更新器！作者: {AUTHOR}", id="welcome-label")
        yield Label(f"当前目录: {APP_PATH}", id="app-path")
        yield Label("已安装的版本: ", id="installed-version")
        yield Label(f"最新的版本: 获取中", id="latest-version")
        yield Label(f"更新渠道: {'Mirror 酱' if settings.get_mirrorchyan_cdk() != '' else 'GitHub + 代理'}",
                    id="update-channel")
        yield Button("立即更新", id="update-button", classes="disabled")
        yield Horizontal(
            Label("下载进度:", id="progress-label"),
            ProgressBar(id="download-progress", show_percentage=True, show_eta=True),
            classes="disabled",
            id="progress-container")
        yield Collapsible(Markdown(id='release-note'), title="更新内容", collapsed=False)
        yield self.logger

    @on(Button.Pressed, "#update-button")
    @work
    async def update(self):
        # 禁用下载按钮，防止重复点击
        download_button = self.query_one("#update-button", Button)
        download_button.disabled = True
        if not await self.pre_check():
            await self.download()
            await self.hash_check()
        self.unzip()
        download_button.disabled = False

    async def pre_check(self):
        if TEMP_DOWNLOAD_FILE.exists():
            logger.info("检测到已有下载的更新包，正在进行校验...")
            return await self.hash_check()
        else:
            return False

    async def download(self):
        """处理下载按钮点击事件，异步下载更新文件并显示进度"""
        if not self.version_response:
            logger.info("没有获取到版本信息，无法下载")
            self.notify("没有获取到版本信息，无法下载")
            return

        # 显示进度条
        progress_container = self.query_one("#progress-container", Horizontal)
        progress_container.remove_class("disabled")

        progress_bar = self.query_one("#download-progress", ProgressBar)
        progress_label = self.query_one("#progress-label", Label)

        # 初始化进度条
        progress_bar.progress = 0

        def size_callback(total_size):
            if total_size > 0:
                progress_bar.update(total=total_size)
            else:
                progress_bar.update(total=0)

        # 定义进度回调函数
        def progress_callback(downloaded_size):
            progress_bar.update(progress=downloaded_size)
            progress_label.update(
                f"下载中: {self._format_size(downloaded_size)} / {self._format_size(progress_bar.total)}")

        try:
            logger.info(f"开始下载更新包: {self.version_response.data}")
            await download_update_async(self.version_response.data, size_callback=size_callback,
                                        progress_callback=progress_callback)

            logger.info("下载完成！")
            self.notify("下载完成！")

            # 下载完成后更新UI
            progress_label.update(f"下载完成: {self._format_size(progress_bar.total)}")
        except Exception as e:
            logger.error(f"下载过程中发生错误: {str(e)}")
            self.notify(f"下载失败: {str(e)}")

    async def hash_check(self) -> bool:
        progress_label = self.query_one("#progress-label", Label)
        progress_label.update("正在校验文件完整性...")
        logger.info("正在校验文件完整性...")
        if await hash_check(self.version_response.data):
            progress_label.update("文件校验通过！")
            logger.info("文件校验通过！")
            return True
        else:
            progress_label.update("文件校验失败！")
            logger.error("文件校验失败，可能下载的文件已损坏，请重试！")
            return False

    def unzip(self):
        """解压下载的更新包"""
        if Castorice.look("SRA.exe"):
            Castorice.touch("SRA.exe")
            time.sleep(2)

        if TEMP_DOWNLOAD_FILE.exists():
            try:
                logger.info("解压更新文件")
                if not Path.exists(APP_PATH / "tools/7z.exe"):
                    logger.info(
                        f"解压工具丢失，请手动解压{TEMP_DOWNLOAD_FILE}到当前文件夹"
                    )
                    self.notify("解压失败", severity="error")
                    return
                command = f'"{APP_PATH}\\tools\\7z" x "{TEMP_DOWNLOAD_FILE}" -y'
                cmd = 'cmd.exe /c start "" ' + command
                Castorice.life(cmd, shell=True)
                self.app.exit()

            except Exception as e:
                logger.error(f"解压时出错: {e}")
                self.notify("解压失败", severity="error")

    def _format_size(self, size_bytes):
        """格式化文件大小显示

        Args:
            size_bytes: 文件大小（字节）

        Returns:
            str: 格式化后的文件大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def on_mount(self) -> None:
        self.get_local_version()
        self._get_remote_version()
        log_area = self.query_one(RichLog)

        def log_sink(message: str):
            log_area.write(message.strip())

        logger.add(log_sink, format="{time:HH:mm:ss} | {level} | {message}")

    def action_show_logger(self):
        self.logger.visible = not self.logger.visible

    def action_refresh(self):
        self.get_local_version()
        self._get_remote_version()

    def get_local_version(self):
        self.local_version = get_local_version()
        self.query_one("#installed-version", Label).update(f"已安装的版本: {self.local_version}")

    @work
    async def _get_remote_version(self) -> bool:
        """异步获取并显示远程版本信息

        Returns:
            bool: 是否成功获取版本信息
        """
        latest_version_label = self.query_one("#latest-version", Label)

        try:
            logger.info("正在获取最新版本信息...")
            self.version_response = await get_remote_version()
            self.check_code(self.version_response.code)
            latest_version = self.version_response.data.version_name if self.version_response.data.version_name else "获取失败"
            if self.version_response.data.cdk_expired_time != 0:
                self.query_one("#update-channel", Label).update(
                    f"更新渠道: Mirror 酱 - CDK 剩余: {self.check_remaining_time(self.version_response.data.cdk_expired_time)}")
            if version.parse(latest_version) > version.parse(self.local_version):
                self.query_one("#update-button", Button).remove_class("disabled")
                self.app.bell()
                self.notify("有新版本可用！")
                await self.query_one("#release-note", Markdown).update(self.version_response.data.release_note)
            latest_version_label.update(f"最新的版本: {latest_version}")
            logger.info("获取成功")

            return True

        except Exception as e:
            logger.error(f"获取版本信息时发生错误: {str(e)}")
            latest_version_label.update("最新的版本: 获取失败")
            return False

    def check_remaining_time(self, expired_timestamp: int) -> str:
        """检查CDK剩余时间并返回对应的备注信息

        Args:
            expired_timestamp: CDK过期时间戳

        Returns:
            str: 备注信息
        """
        from datetime import datetime
        expired_time = datetime.fromtimestamp(expired_timestamp)
        remaining_time = expired_time - datetime.now()
        if remaining_time.total_seconds() <= 0:
            return "已过期"
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{days}天 {hours}小时 {minutes}分钟"

    def check_code(self, code: int) -> None:
        """检查返回码并返回对应的备注信息

        Args:
            code: 返回码

        Returns:
            str: 备注信息
        """
        from src.const import ERROR_REMARK_DICT
        msg: str | None = ERROR_REMARK_DICT.get(code, None)
        if msg is not None:
            self.notify(msg, severity='error')


class SettingsScreen(Screen):
    BINDINGS = [("escape", "app.switch_mode('home')", "返回"),
                ("ctrl+s", "save_settings", "保存设置")]
    SUB_TITLE = "设置"
    CSS = """
    Label {
    height: 3;
    content-align-horizontal: center;
    content-align-vertical: middle;
    }

    ListView {
    width: 35;
    height: auto;
    margin: 2 2;
    }
    Input {
    width: 35;
    height: auto;
    border: round $accent;
    background: $background;
    }
    RadioSet {
    width: 20;
    height: auto;
    border: round $accent;
    background: $background;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Static("设置选项" if settings.can_save_settings() else "设置选项 由于未安装SRA，对设置的修改是临时的",
                     id="settings-title")
        yield Horizontal(
            Label("Mirror 酱 CDK:", id="cdk-label"),
            Input(value=settings.get_mirrorchyan_cdk(), placeholder="请输入 Mirror 酱 CDK", password=True,
                  id="cdk-input"),
        )
        yield Horizontal(
            Label("Proxys:", id="proxys-label"),
            ListView(*[ListItem(Static(proxy)) for proxy in settings.get_proxys()], id="proxys-list"),
        )
        yield Horizontal(
            Label("更新通道:", id="update-channel-label"),
            RadioSet(
                RadioButton("stable", id="stable", value=settings.get_channel()=="stable"),
                RadioButton("beta", id="beta", value=settings.get_channel()=="beta"),
            )
        )

    def action_save_settings(self):
        cdk_label = self.query_one("#cdk-input", Input)
        settings.set_mirrorchyan_cdk(cdk_label.value)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        settings.set_channel(event.pressed.id)


class IntegrityScreen(Screen):
    SUB_TITLE = "文件完整性检查"
    BINDINGS = [("escape", "app.switch_mode('home')", "返回")]
    CSS = """
    #download-missing-button,
    #check-button{
        border: round $success;
        background: $background 0%;
        color: $success;
        text-style: bold;
    }
    .disabled {
        display: none;
    }
    """
    inconsistent_files = []
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Label("文件完整性检查", id="integrity-title")
        yield Horizontal(
            Button("开始检查", id="check-button"),
            Button("下载缺失文件", id="download-missing-button", classes="disabled")
        )
        yield Horizontal(
            Label("等待检查:", id="progress-label"),
            ProgressBar(id="check-progress", show_percentage=True, show_eta=True),
            classes="",
            id="progress-container")
        yield Collapsible(Markdown(id='check-result'), title="检查结果", collapsed=True)

    @on(Button.Pressed, "#check-button")
    @work
    async def integrity_check(self):
        check_button = self.query_one("#check-button", Button)
        check_button.disabled = True
        progress_label = self.query_one("#progress-label", Label)
        try:
            # 1. 获取哈希字典
            hash_dict = await get(HASH_URL)
            if not isinstance(hash_dict, dict):
                raise ValueError("Invalid hash data format")

            # 2. 初始化进度条
            progress_bar = self.query_one("#check-progress", ProgressBar)
            progress_bar.progress=0
            progress_bar.total = len(hash_dict)

            # 3. 检查文件完整性
            self.inconsistent_files.clear()
            for filename, expected_hash in hash_dict.items():
                progress_label.update(f"正在检查: {filename}")

                # 计算实际哈希值（假设 hash_calculate 是同步函数）
                actual_hash = hash_calculate(filename)
                if actual_hash != expected_hash:
                    self.inconsistent_files.append(filename)

                progress_bar.advance(1)
                await asyncio.sleep(0)  # 让出事件循环，避免 UI 卡顿

            # 4. 显示结果
            result_md = (
                "以下文件完整性检查未通过:\n\n" + "\n".join(f"- {file}" for file in self.inconsistent_files)
                if self.inconsistent_files
                else "所有文件完整性检查均通过！"
            )
            await self.query_one("#check-result", Markdown).update(result_md)
            progress_label.update("检查完成")
            if self.inconsistent_files:
                self.query_one("#download-missing-button", Button).remove_class("disabled")

        except Exception as e:
            # 错误处理（如网络请求失败）
            error_md = f"**检查失败**: {str(e)}"
            await self.query_one("#check-result", Markdown).update(error_md)
            progress_label.update("检查中断")
        finally:
            check_button.disabled = False

    @on(Button.Pressed, "#download-missing-button")
    @work
    async def download_missing_files(self):
        if not self.inconsistent_files:
            return
        download_button = self.query_one("#download-missing-button", Button)
        download_button.disabled = True
        progress_label = self.query_one("#progress-label", Label)
        progress_label.update("正在下载缺失文件...")
        progress_bar = self.query_one("#check-progress", ProgressBar)
        progress_bar.total=len(self.inconsistent_files)
        progress_bar.progress=0
        logger.info("正在下载缺失文件...")
        if Castorice.look("SRA.exe"):
            Castorice.touch("SRA.exe")
            time.sleep(2)
        try:
            for filename in self.inconsistent_files:
                progress_label.update(f"正在下载: {filename}")
                file_url = f"https://resource.starrailassistant.top/SRA/{filename}"  # 替换为实际文件下载 URL
                await download_file_async(file_url)
                progress_bar.advance(1)
                await asyncio.sleep(0)  # 让出事件循环，避免 UI 卡顿
            progress_label.update("下载完成")
            logger.info("下载完成")
        except Exception as e:
            progress_label.update(f"下载失败: {str(e)}")
            logger.error(f"下载失败: {str(e)}")
        finally:
            download_button.disabled = False


