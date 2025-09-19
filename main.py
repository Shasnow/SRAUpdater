import argparse
import asyncio
from typing import Iterable

from loguru import logger
from textual.app import App, SystemCommand
from textual.screen import Screen

from src.cli import SRACLI
from src.component import HomeScreen, SettingsScreen, IntegrityScreen
from src.const import VERSION, AUTHOR

logger.remove(0)


class SRAUpdaterApp(App):
    TITLE = "SRA Updater"
    SUB_TITLE = f"SRA 更新器 {VERSION}"
    MODES = {
        "home": HomeScreen,
        "settings": SettingsScreen,
        "integrity": IntegrityScreen,
    }
    DEFAULT_MODE = "home"

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield SystemCommand("Change themes", "切换主题", self.action_change_theme)
        yield SystemCommand("Open settings", "打开设置", lambda: self.switch_mode("settings"))
        yield SystemCommand("Quit the application", "退出应用", self.action_quit)
        if screen.query("HelpPanel"):
            yield SystemCommand(
                "Hide keys and help panel",
                "隐藏帮助面板",
                self.action_hide_help_panel,
            )
        else:
            yield SystemCommand(
                "Show keys and help panel",
                "显示帮助面板",
                self.action_show_help_panel,
            )
def parse_cli_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog="SRA CLI Tool",
        description=f"SRA 辅助工具（CLI 版 v{VERSION}）- 支持更新、完整性检查、配置管理",
        epilog=f"作者: {AUTHOR}"
    )

    # 子命令：支持 update/check/settings
    subparsers = parser.add_subparsers(
        dest="command",  # 存储选中的子命令
        required=False,  # 允许无命令（默认进入交互菜单）
        help="可用命令：update（更新）、check（完整性检查）、settings（配置管理）, 对每个命令使用 -h 查看详细帮助"
    )

    # 子命令 1: update（更新 SRA）
    parser_update = subparsers.add_parser(
        "update",
        help="检查并更新 SRA 到最新版本"
    )

    # 子命令 2: check（完整性检查）
    parser_check = subparsers.add_parser(
        "check",
        help="检查 SRA 文件完整性，支持自动修复"
    )
    parser_check.add_argument(
        "-r", "--repair",
        action="store_true",  # 带 -r 则自动修复
        help="自动下载并修复异常文件（无需手动确认）"
    )

    # 子命令 3: settings（配置管理）
    parser_settings = subparsers.add_parser(
        "settings",
        help="查看或修改 SRA 配置（CDK/更新通道等）"
    )
    parser_settings.add_argument(
        "-s", "--show-only",
        action="store_true",  # 带 -s 则仅查看不修改
        help="仅显示当前配置，不进入交互修改模式"
    )

    return parser.parse_args()

async def main(args):
    cli = SRACLI()

    # 2. 根据参数执行对应命令
    if args.command == "update":
        # 执行更新流程：python sra_cli.py update
        await cli.update_flow()

    elif args.command == "check":
        # 执行完整性检查：python sra_cli.py check [-r]
        await cli.integrity_check(auto_repair=args.repair)

    elif args.command == "settings":
        # 执行配置管理：python sra_cli.py settings [-s]
        await cli.settings_manage(show_only=args.show_only)


if __name__ == '__main__':
    args=parse_cli_args()
    if args.command is not None:
        asyncio.run(main(args))
    else:
        app = SRAUpdaterApp()
        app.run()
