
from dataclasses import dataclass

@dataclass
class VersionInfo:
    """ 版本信息 """
    version: str
    """ 版本号 """
    resource_version: str
    """ 资源版本号 """
    announcement: str
    """ 公告 """
    resource_announcement: str
    """ 资源公告 """