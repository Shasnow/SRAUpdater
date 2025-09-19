# SRAUpdater

星穹铁道助手(StarRailAssistant)更新器 - 提供便捷的更新管理、文件完整性检查与配置管理服务

## 🚀 项目介绍

SRAUpdater 是星穹铁道助手(StarRailAssistant)的官方更新工具，专为简化SRA的更新流程、确保文件完整性而设计。它提供了图形界面(GUI)和命令行界面(CLI)两种操作方式，满足不同用户的使用习惯。

## ✨ 功能特性

- **自动更新**: 检查并下载最新版本的SRA，支持断点续传
- **文件完整性检查**: 验证SRA文件的完整性并提供自动修复功能
- **配置管理**: 管理CDK、更新通道、代理服务器等设置
- **双界面支持**: 简洁易用的图形界面，以及功能强大的命令行界面
- **多更新通道**: 支持GitHub + 代理和Mirror酱专属通道
- **实时进度展示**: 美观的下载进度条和操作状态提示

## 📋 系统要求

- Windows 10/11 操作系统
- Python 3.9+ (如需从源码运行)
- 稳定的网络连接(用于更新和检查)

## 📦 安装方法

### 从发布版本安装

1. 访问 [GitHub Releases](https://github.com/Shasnow/SRAUpdater/releases) 下载最新的发布版本
2. 将下载的压缩包解压到任意目录
3. 运行 `SRAUpdater.exe` 启动程序

### 从源码运行

1. 克隆本仓库
   ```bash
   git clone https://github.com/Shasnow/SRAUpdater.git
   cd SRAUpdater
   ```

2. 创建虚拟环境并安装依赖
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. 运行程序
   ```bash
   python main.py
   ```

## 🖥️ 使用说明

### 图形界面模式

直接运行 `SRAUpdater.exe` 或 `python main.py` (源码方式) 启动图形界面：

- **主页**: 显示版本信息和快速操作按钮
- **设置**: 配置CDK、更新通道和代理
- **完整性检查**: 检查并修复SRA文件

### 命令行模式

SRAUpdater 提供了功能丰富的命令行接口，可以高效地执行各项任务：

```bash
# 启动图形界面(无参数)
python main.py

# 检查并更新SRA到最新版本
python main.py update

# 检查SRA文件完整性
python main.py check

# 检查并自动修复SRA文件完整性
python main.py check --repair

# 查看当前配置
python main.py settings --show-only

# 进入配置管理交互模式
python main.py settings
```

## ⚙️ 配置选项

### Mirror酱CDK

设置Mirror酱专属CDK以获取专属更新服务：

```bash
python main.py settings
# 在交互界面中输入CDK
```

### 更新通道

支持以下更新通道：
- `stable`: 稳定版(默认)
- 其他通道(根据SRA官方提供)

### 代理服务器

设置代理服务器以加速GitHub下载：
- 默认代理: `https://gh-proxy.com/`
- 可在设置界面或通过CLI添加自定义代理

## 🛠️ 项目结构

```
SRAUpdater/
├── src/                # 源代码目录
│   ├── cli.py          # 命令行接口实现
│   ├── component.py    # GUI组件定义
│   ├── const.py        # 常量定义
│   ├── encryption.py   # 加密相关功能
│   ├── settings.py     # 配置管理
│   └── util.py         # 工具函数
├── tools/              # 工具文件
│   ├── 7z.dll          # 7-Zip解压库
│   └── 7z.exe          # 7-Zip解压程序
├── main.py             # 主程序入口
├── package.py          # 打包脚本
└── requirements.txt    # 依赖列表
```

## 🔧 开发说明

如果你想参与开发或修改本项目：

1. Fork并克隆仓库
2. 创建新分支进行开发
3. 提交修改并创建Pull Request

## 📝 版本历史

当前版本：v4.0.0

## 👨‍💻 贡献者

- Shasnow
- Fuxuan-CN
- DLmaster_361

## 📄 许可证

[MIT License](https://opensource.org/licenses/MIT)

## ❓ 常见问题

### Q: 更新失败怎么办？
A: 尝试使用 `--repair` 参数进行完整性检查和修复，或检查网络连接和代理设置。

### Q: 如何切换更新通道？
A: 通过设置界面或命令行 `settings` 命令进行切换。

### Q: Mirror酱CDK有什么用？
A: Mirror酱CDK可以提供专属的更新服务和加速下载体验。

## 📞 联系我们

如有问题或建议，请在 [GitHub Issues](https://github.com/Shasnow/SRAUpdater/issues) 中提交反馈。