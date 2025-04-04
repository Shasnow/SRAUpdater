from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn

# 下载进度条
download_progress_bar = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
    transient=False,
)