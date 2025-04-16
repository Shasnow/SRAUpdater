""" make argparse help message beautiful """
import argparse
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from .const import GLOBAL_CONSOLE

class RichHelpFormatter(argparse.HelpFormatter):
    """
    使用 Rich 美化 argparse 的帮助信息。
    """
    def __init__(self, prog, indent_increment=2, max_help_position=30, width=None):
        super().__init__(prog, indent_increment, max_help_position, width)
        self.console = GLOBAL_CONSOLE

    def _format_usage(self, usage, actions, groups, prefix):
        """
        美化使用方法部分。
        """
        usage_text = super()._format_usage(usage, actions, groups, prefix)
        if not self.console.is_terminal:
            return usage_text
        return f"[bold green]{usage_text}[/bold green]"

    def _format_action(self, action):
        """
        美化动作（参数）部分。
        """
        help_text = super()._format_action(action)
        lines = help_text.split("\n")
        formatted_lines = []
        for line in lines:
            if line.startswith("  --"):
                # 美化参数名称
                parts = line.split(" ", 1)
                option = parts[0]
                description = parts[1] if len(parts) > 1 else ""
                # 检查是否有默认值
                if action.default is not argparse.SUPPRESS:
                    if not self.console.is_terminal:
                        default = f" (default: {action.default})"
                    else:
                        default = f" (default: [bold cyan]{action.default}[/bold cyan])"
                else:
                    default = ""
                # 检查参数类型
                if action.type:
                    type_name = action.type.__name__
                    type_text = f" ([bold cyan]{type_name}[/bold cyan])" if self.console.is_terminal else f" (Type: {type_name})"
                else:
                    type_text = ""
                formatted_lines.append(f"{option} {description}{type_text}{default}")
            else:
                formatted_lines.append(line)
        return "\n".join(formatted_lines)

    def _format_text(self, text):
        """
        美化普通文本部分。
        """
        return f"[bold magenta]{text}[/]"
    
    
    def _format_help(self) -> str:
        """ 美化帮助信息 """
        help_text = super().format_help()
        return help_text

    def format_help(self) -> None:
        """
        将美化后的帮助信息包装为 Rich 的 Panel。
        """
        help_text = self._format_help()
        title = f"[bold red]{self._prog if self._prog else 'Usage'}[/bold red]"
        panel = Panel(Text.from_markup(help_text), title=title, style=Style(color="yellow"))
        self.console.print(panel)