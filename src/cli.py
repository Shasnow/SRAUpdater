import asyncio
import json
import sys
import time
from datetime import datetime

from packaging import version
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
)
from rich.prompt import Prompt
from rich.table import Table

from src import settings
from src.const import APP_PATH, VERSION, TEMP_DOWNLOAD_FILE, HASH_URL, ERROR_REMARK_DICT, ANNOUNCEMENT_URL
from src.util import (
    get_local_version, download_update_async, get_remote_version,
    hash_check, Castorice, get, hash_calculate, download_file_async
)

# -------------------------- 1. 初始化 Rich 控制台（全局单例） --------------------------
console = Console(highlight=False)  # highlight=False 避免自动高亮文本


class SRACLI:
    def __init__(self):
        self.local_version = None
        self.version_response = None  # 远程版本信息
        self.inconsistent_files = []  # 完整性检查不通过的文件

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小（字节 → B/KB/MB/GB），带 Rich 颜色"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"[cyan]{size_bytes:.2f} {unit}[/cyan]"
            size_bytes /= 1024.0
        return f"[cyan]{size_bytes:.2f} PB[/cyan]"

    def get_local_version(self):
        """获取本地已安装版本 - 用表格展示本地信息"""
        self.local_version = get_local_version()

        # 构建本地信息表格
        local_table = Table(show_header=False, box=None, padding=(0, 2))
        local_table.add_row("[bold]已安装版本:", f"[green]{self.local_version}[/green]")
        local_table.add_row("[bold]当前目录:", f"[blue]{APP_PATH}[/blue]")
        channel = "Mirror 酱" if settings.get_mirrorchyan_cdk() != "" else "GitHub + 代理"
        local_table.add_row("[bold]更新渠道:", f"[yellow]{channel}[/yellow]")

        console.print("\n[bold]📌 本地信息[/bold]")
        console.print(local_table)

    async def _get_remote_version(self) -> bool:
        """异步获取远程版本信息 - 带加载提示和彩色输出"""
        with console.status("[bold green]🔍 正在获取最新版本信息...", spinner="dots"):
            try:
                self.version_response = await get_remote_version()
            except Exception as e:
                console.print(f"\n[bold red]❌ 获取版本信息失败:[/bold red] {str(e)}")
                return False

        # 检查返回码
        code = self.version_response.code
        if code in ERROR_REMARK_DICT:
            console.print(f"\n[bold red]❌ 版本获取失败:[/bold red] {ERROR_REMARK_DICT[code]}")
            return False

        # 解析远程版本
        latest_version = self.version_response.data.version_name or "未知"
        console.print(f"\n[bold]📡 远程版本信息[/bold]")
        console.print(f"[bold]最新版本:[/bold] [green]{latest_version}[/green]")

        # 检查 CDK 有效期（Mirror 酱专属）
        if self.version_response.data.cdk_expired_time != 0:
            remaining = self._check_remaining_time(self.version_response.data.cdk_expired_time)
            console.print(f"[bold]Mirror 酱 CDK 剩余时间:[/bold] [orange1]{remaining}[/orange1]")

        # 版本对比（带颜色高亮）
        if version.parse(latest_version) > version.parse(self.local_version):
            rprint(f"\n[bold green]🎉 发现新版本！[/bold green]")
            rprint(f"  当前版本: [yellow]{self.local_version}[/yellow] → 最新版本: [green]{latest_version}[/green]")
            # 用 Panel 展示更新内容（更美观）
            release_note = self.version_response.data.release_note or "无更新内容描述"
            console.print("\n[bold]📄 更新内容[/bold]")
            console.print(Markdown(release_note, justify="left"))
            return True
        else:
            console.print(f"\n[bold green]✅ 当前已是最新版本[/bold green] ({self.local_version})")
            return False

    def _check_remaining_time(self, expired_timestamp: int) -> str:
        """计算 CDK 剩余时间 - 带颜色提示（过期/即将过期/正常）"""
        expired_time = datetime.fromtimestamp(expired_timestamp)
        remaining_time = expired_time - datetime.now()

        if remaining_time.total_seconds() <= 0:
            return "[red]已过期[/red]"

        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # 即将过期（7天内）标橙色，否则标绿色
        if days < 7:
            return f"[orange1]{days}天 {hours}小时 {minutes}分钟[/orange1] (即将过期)"
        else:
            return f"[green]{days}天 {hours}小时 {minutes}分钟[/green]"

    async def pre_check(self) -> bool:
        """预检查：已下载更新包校验 - 带进度提示"""
        if TEMP_DOWNLOAD_FILE.exists():
            console.print(f"\n[bold yellow]⚠️  检测到已下载的更新包:[/bold yellow] {TEMP_DOWNLOAD_FILE}")
            with console.status("[bold blue]🔍 正在校验更新包完整性...", spinner="line"):
                result = await self.hash_check()
            return result
        else:
            return False

    async def hash_check(self) -> bool:
        """文件哈希校验 - 带明确结果颜色"""
        try:
            result = await hash_check(self.version_response.data)
            if result:
                console.print("[bold green]✅ 哈希校验通过[/bold green]")
                return True
            else:
                console.print("[bold red]❌ 哈希校验失败（文件可能损坏）[/bold red]")
                # 删除损坏文件（带确认）
                if TEMP_DOWNLOAD_FILE.exists():
                    TEMP_DOWNLOAD_FILE.unlink()
                    console.print(f"[bold cyan]🗑️  已删除损坏的更新包:[/bold cyan] {TEMP_DOWNLOAD_FILE}")
                return False
        except Exception as e:
            console.print(f"[bold red]❌ 校验过程出错:[/bold red] {str(e)}")
            return False

    async def download_update(self) -> bool:
        """异步下载更新包 - 用 Rich 动态进度条替代文本进度"""
        if not self.version_response:
            console.print("[bold red]❌ 无远程版本信息，无法下载[/bold red]")
            return False

        console.print(f"\n[bold blue]📥 开始下载更新包[/bold blue]: {self.version_response.data.version_name}")
        progress = Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            transient=True,  # 任务完成后自动隐藏进度条
        )
        download_task = progress.add_task("[bold]下载中...", total=0)

        # 进度回调函数（更新 Rich 进度条）
        def size_callback(total_size: int):
            if total_size > 0:
                progress.update(download_task, total=total_size)
            else:
                progress.update(download_task, total=0, description="[bold yellow]获取文件大小中...[/bold yellow]")

        def progress_callback(downloaded_size: int):
            downloaded_str = self._format_size(downloaded_size)
            total_str = self._format_size(progress.tasks[download_task].total)
            progress.update(
                download_task,
                completed=downloaded_size,
                description=f"[bold]下载中: {downloaded_str} / {total_str}[/bold]"
            )

        # 启动下载（带进度条）
        with progress:
            try:
                await download_update_async(
                    self.version_response.data,
                    size_callback=size_callback,
                    progress_callback=progress_callback
                )
            except Exception as e:
                console.print(f"\n[bold red]❌ 下载失败:[/bold red] {str(e)}")
                return False

        console.print("\n[bold green]✅ 下载完成！[/bold green]")
        return True

    def unzip_update(self) -> bool:
        """解压更新包 - 带步骤提示和颜色"""
        console.print("\n[bold blue]📦 开始解压更新包[/bold blue]")
        if not TEMP_DOWNLOAD_FILE.exists():
            console.print("[bold red]❌ 未找到更新包，解压失败[/bold red]")
            return False

        # 关闭 SRA.exe（若运行）
        if Castorice.look("SRA.exe"):
            with console.status("[bold yellow]🔌 正在关闭运行中的 SRA.exe...", spinner="dots"):
                Castorice.touch("SRA.exe")
                time.sleep(2)
            console.print("[bold green]✅ 已关闭 SRA.exe[/bold green]")

        # 检查 7z 工具
        seven_zip_path = APP_PATH / "tools/7z.exe"
        if not seven_zip_path.exists():
            console.print(f"[bold red]❌ 解压工具缺失:[/bold red] {seven_zip_path}")
            console.print(f"[bold cyan]💡 提示:[/bold cyan] 请手动解压 {TEMP_DOWNLOAD_FILE} 到当前文件夹")
            return False

        # 执行解压命令
        try:
            command = f'"{seven_zip_path}" x "{TEMP_DOWNLOAD_FILE}" -y'
            cmd = 'cmd.exe /c start "" ' + command
            Castorice.life(cmd, shell=True)
            console.print(f"\n[bold green]✅ 已启动解压程序[/bold green]")
            console.print(f"[bold]解压命令:[/bold] [blue]{command}[/blue]")
            console.print(f"[bold cyan]💡 提示:[/bold cyan] 解压完成后请重新启动 SRA")
            return True
        except Exception as e:
            console.print(f"[bold red]❌ 解压失败:[/bold red] {str(e)}")
            return False

    async def integrity_check(self, auto_repair: bool = False) -> bool:
        """文件完整性检查 - 用 Rich 进度条和表格展示结果"""
        console.print(Panel("[bold green]📋 SRA 文件完整性检查[/bold green]", border_style="green", padding=1))

        # 步骤1: 获取远程哈希字典
        with console.status("[bold blue]步骤1/3: 获取远程哈希列表...", spinner="dots"):
            try:
                hash_dict = await get(HASH_URL)
                if not isinstance(hash_dict, dict):
                    raise ValueError("远程哈希数据格式无效（非字典类型）")
                total_files = len(hash_dict)
                console.print(f"[bold green]✅ 步骤1完成[/bold green]: 成功获取 {total_files} 个文件的哈希信息")
            except Exception as e:
                console.print(f"[bold red]❌ 步骤1失败[/bold red]: {str(e)}")
                return False

        # 步骤2: 逐个校验（带分组进度条）
        console.print(f"\n[bold blue]步骤2/3: 校验 {total_files} 个文件完整性[/bold blue]")
        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(bar_width=None, style="cyan", complete_style="green"),
            TimeRemainingColumn(),
            transient=False,
        )
        check_task = progress.add_task("[bold]正在校验文件...", total=total_files)
        self.inconsistent_files.clear()

        with progress:
            for idx, (filename, expected_hash) in enumerate(hash_dict.items(), 1):
                file_path = APP_PATH / filename
                # 更新进度条描述（显示当前校验的文件）
                progress.update(check_task, description=f"[bold]校验中: {filename}[/bold]")

                try:
                    actual_hash = hash_calculate(file_path)
                    if actual_hash != expected_hash:
                        self.inconsistent_files.append((filename, "哈希不匹配", "red"))
                    else:
                        self.inconsistent_files.append((filename, "校验通过", "green"))
                except FileNotFoundError:
                    self.inconsistent_files.append((filename, "文件缺失", "red"))
                except Exception as e:
                    self.inconsistent_files.append((filename, f"校验错误: {str(e)}", "yellow"))

                progress.update(check_task, advance=1)
                await asyncio.sleep(0)  # 让出事件循环，避免卡顿

        # 步骤3: 展示结果（用表格分类）
        console.print("\n[bold blue]步骤3/3: 校验结果汇总[/bold blue]")
        # 筛选不同状态的文件
        passed = [f for f, status, color in self.inconsistent_files if status == "校验通过"]
        failed = [f for f, status, color in self.inconsistent_files if status in ["哈希不匹配", "文件缺失"]]
        errors = [f for f, status, color in self.inconsistent_files if "校验错误" in status]

        # 结果统计表格
        result_table = Table(show_header=True, header_style="bold cyan")
        result_table.add_column("状态", justify="center")
        result_table.add_column("文件数量", justify="center")
        result_table.add_row("[green]✅ 校验通过[/green]", str(len(passed)))
        result_table.add_row("[red]❌ 校验失败/缺失[/red]", str(len(failed)))
        result_table.add_row("[yellow]⚠️  校验错误[/yellow]", str(len(errors)))
        console.print(result_table)

        # 显示失败/错误文件详情（按需展开）
        if failed or errors:
            console.print("\n[bold red]❌ 异常文件详情[/bold red]")
            detail_table = Table(show_header=True, header_style="bold cyan")
            detail_table.add_column("文件名")
            detail_table.add_column("状态")
            for filename, status, color in self.inconsistent_files:
                if status != "校验通过":
                    detail_table.add_row(filename, f"[{color}]{status}[/{color}]")
            console.print(detail_table)

            # 自动修复（若启用）
            if auto_repair and (failed or errors):
                console.print("\n[bold yellow]⚠️  启动自动修复...[/bold yellow]")
                await self.download_missing_files()
        else:
            console.print("\n[bold green]🎉 所有文件均通过校验！[/bold green]")

        return len(failed) == 0 and len(errors) == 0

    async def download_missing_files(self) -> bool:
        """下载缺失文件 - 带批量进度条"""
        # 筛选需要修复的文件（缺失/哈希不匹配）
        need_repair = [f for f, status, color in self.inconsistent_files if status in ["文件缺失", "哈希不匹配"]]
        if not need_repair:
            console.print("[bold green]✅ 无需要修复的文件[/bold green]")
            return True

        console.print(f"\n[bold blue]📥 开始修复 {len(need_repair)} 个异常文件[/bold blue]")
        # 关闭 SRA.exe（若运行）
        if Castorice.look("SRA.exe"):
            with console.status("[bold yellow]🔌 关闭 SRA.exe 中...", spinner="dots"):
                Castorice.touch("SRA.exe")
                time.sleep(2)
            console.print("[bold green]✅ 已关闭 SRA.exe[/bold green]")

        # 批量下载进度条
        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(bar_width=None, style="cyan", complete_style="green"),
            TimeRemainingColumn(),
            transient=False,
        )
        repair_task = progress.add_task("[bold]修复中...", total=len(need_repair))
        success_count = 0

        with progress:
            for idx, filename in enumerate(need_repair, 1):
                file_url = f"https://resource.starrailassistant.top/SRA/{filename}"
                file_path = APP_PATH / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)  # 创建父目录

                # 更新进度条描述
                progress.update(repair_task, description=f"[bold]修复: {filename}[/bold]")
                try:
                    await download_file_async(file_url)
                    success_count += 1
                    console.print(f"\n[bold green]✅ 修复成功[/bold green]: {filename}")
                except Exception as e:
                    console.print(f"\n[bold red]❌ 修复失败[/bold red]: {filename} → {str(e)}")

                progress.update(repair_task, advance=1)
                await asyncio.sleep(0)

        # 修复结果汇总
        console.print("\n[bold blue]📊 修复结果汇总[/bold blue]")
        summary_table = Table(show_header=True, header_style="bold cyan")
        summary_table.add_column("总文件数", justify="center")
        summary_table.add_column("修复成功", justify="center")
        summary_table.add_column("修复失败", justify="center")
        summary_table.add_row(
            str(len(need_repair)),
            f"[green]{success_count}[/green]",
            f"[red]{len(need_repair) - success_count}[/red]"
        )
        console.print(summary_table)
        return success_count > 0

    async def update_flow(self):
        """完整更新流程 - 带流程标题和步骤分隔"""
        console.print(Panel(f"[bold green]🚀 SRA 更新流程 (v{VERSION})[/bold green]", border_style="green", padding=1))

        # 1. 获取本地/远程版本
        self.get_local_version()
        has_new_version = await self._get_remote_version()
        if not has_new_version:
            await self.update_announcement()
            return

        # 2. 预检查（已下载包校验）
        pre_check_pass = await self.pre_check()
        if pre_check_pass:
            console.print("[bold yellow]⚠️  直接使用已校验通过的更新包[/bold yellow]")
        else:
            # 3. 下载更新包
            download_success = await self.download_update()
            if not download_success:
                console.print("[bold red]❌ 下载失败，更新流程终止[/bold red]")
                return
            # 4. 下载后校验
            if not await self.hash_check():
                console.print("[bold red]❌ 校验失败，更新流程终止[/bold red]")
                return

        # 5. 解压更新包
        if self.unzip_update():
            sys.exit(0)
        console.print("\n" + "=" * 50)
        console.print("[bold green]🎉 更新流程所有步骤完成！[/bold green]")
        console.print("=" * 50)

    async def settings_manage(self, show_only: bool = False):
        """配置管理 - 用表格展示配置，Rich Prompt 优化交互"""
        console.print(Panel("[bold blue]⚙️ SRA 配置管理[/bold blue]", border_style="blue", padding=1))

        # 展示当前配置（表格形式）
        config_table = Table(show_header=True, header_style="bold cyan")
        config_table.add_column("配置项", justify="left")
        config_table.add_column("当前值", justify="left")
        # CDK（隐藏敏感信息）
        cdk = settings.get_mirrorchyan_cdk()
        cdk_display = "***已设置***" if cdk else "未设置"
        config_table.add_row("[bold]Mirror 酱 CDK", f"[yellow]{cdk_display}[/yellow]")
        # 更新通道
        channel = settings.get_channel()
        config_table.add_row("[bold]更新通道", f"[green]{channel}[/green] (stable/beta)")
        # 代理列表
        proxys = settings.get_proxys() or ["无"]
        proxys_display = "\n".join(proxys)
        config_table.add_row("[bold]代理列表", f"[blue]{proxys_display}[/blue]")
        console.print(config_table)

        # 仅查看模式：不进入交互
        if show_only:
            return

        # 交互修改（用 Rich Prompt 替代 input，支持自动补全）
        while True:
            console.print("\n[bold cyan]请选择操作（输入编号）:[/bold cyan]")
            console.print("1. 修改 Mirror 酱 CDK")
            console.print("2. 切换更新通道")
            console.print("3. 保存配置并退出")

            choice = Prompt.ask(
                "[bold]请输入选项",
                choices=["1", "2", "3"],
                default="3",
                show_choices=False
            )

            if choice == "1":
                new_cdk = Prompt.ask(
                    "[bold]请输入新的 Mirror 酱 CDK[/bold]（为空则清空）",
                    password=True  # 密码模式，输入时隐藏
                )
                settings.set_mirrorchyan_cdk(new_cdk)
                console.print(f"[bold green]✅ CDK 已更新[/bold green]: {'***已设置***' if new_cdk else '未设置'}")

            elif choice == "2":
                new_channel = Prompt.ask(
                    "[bold]请选择更新通道[/bold]",
                    choices=["stable", "beta"],
                    default=settings.get_channel(),
                    show_choices=True
                )
                settings.set_channel(new_channel)
                console.print(f"[bold green]✅ 更新通道已切换为[/bold green]: [green]{new_channel}[/green]")

            elif choice == "3":
                console.print("[bold green]✅ 配置已保存，退出管理[/bold green]")
                break

    async def update_announcement(self):
        """
        更新公告信息。
        """
        console.print("[bold blue]📢 更新公告信息[/bold blue]")
        try:
            announcement = await get(ANNOUNCEMENT_URL)
            with open("version.json", "r+", encoding="utf-8") as json_file:
                version_info = json.load(json_file)
                version_info["Announcement"] = announcement.get("Announcement", [])

                version_info["Proxys"] = announcement.get("Proxys", "")
                json_file.seek(0)
                json.dump(version_info, json_file, indent=4, ensure_ascii=False)
                json_file.truncate()
            console.print("[bold green]✅ 公告信息已更新[/bold green]")
        except Exception as e:
            console.print("[bold red]❌ 获取公告信息失败:[/bold red] {str(e)}")
            return



