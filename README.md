# SRAUpdater

SRAUpdater是星穹铁道助手StarRailAssistant的附属，为其提供更新、文件完整性检查服务。

基本用法：
默认通过to_exe脚本打包为SRAUpdater.exe后使用。双击运行即可开始检查更新。
在下载时，可以通过Ctrl+C取消下载。

进阶：
```bash
SRAUpdater -h
```
用于查看帮助信息
```bash
SRAUpdater -u URL
```
指定下载文件url。是的，SRA更新器不止能用来更新SRA，也可以借助它下载任何其他文件，只需将`URL`替换为需要下载的文件链接。
```bash
SRAUpdater -p PROXY
```
指定下载代理。如果你有自己的代理网站，使用此参数来设置它，只需将`PROXY`替换为你的代理网站。
```bash
SRAUpdater -np
```
禁用代理。np不是no problem，而是no proxy。如果你要下载的文件不需要经过代理，或者要使用加速器下载，使用此参数来关闭代理。
```bash
SRAUpdater -nv
```
禁用SSL证书验证。当使用加速器下载时，除了需要使用上面的-np参数，还有可能遇到SSL证书验证失败，此时使用此参数关闭SSL证书认证来完成下载。
```bash
SRAUpdater -f
```
强制更新。也许由于种种原因你的SRA处于旧的版本，但更新器却说这是最新版本（这通常是由于version文件错误导致的）。使用此参数来进行一次强制更新，即无论是否是最新版本，都下载一次最新版本。
```bash
SRAUpdater -i
```
进行文件完整性检查。此参数会检测SRA的所有文件是否是最新的。如果有则准备下载。
```bash
SRAUpdater -vb
```
显示完整的日志信息。通常与其他参数混合使用，输出更完整的日志。
```bash
SRAUpdater -v
```
显示当前版本信息。
```bash
SRAUpdater -timeout
```
设置请求超时时间。