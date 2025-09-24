import dataclasses
import json
import os

from loguru import logger

from src import encryption


@dataclasses.dataclass
class Settings:
    """设置数据模型"""
    mirrorchyan_cdk: str
    """ Mirror酱CDK """
    proxys: list[str]
    """ 系统代理 """
    channel: str = "stable"
    """ 更新通道 """


temp_settings = Settings(mirrorchyan_cdk="", proxys=["https://gh-proxy.com/", "", ])


def get_mirrorchyan_cdk() -> str:
    """获取 MirrorChyan CDK"""
    try:
        with open('data/globals.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        cdk = config.get('mirrorchyanCDK','')
        return encryption.win_decryptor(cdk)
    except KeyError:
        return temp_settings.mirrorchyan_cdk
    except FileNotFoundError:
        return temp_settings.mirrorchyan_cdk
    except json.JSONDecodeError:
        return temp_settings.mirrorchyan_cdk


def get_proxys() -> list[str]:
    """获取系统代理"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get("Proxys", [])
    except FileNotFoundError:
        return temp_settings.proxys
    except json.JSONDecodeError:
        return temp_settings.proxys


def set_mirrorchyan_cdk(cdk: str):
    """设置 MirrorChyan CDK"""
    try:
        if not os.path.exists('data'):
            temp_settings.mirrorchyan_cdk = cdk
            return
        if not os.path.exists('data/globals.json'):
            temp_settings.mirrorchyan_cdk = cdk
            return
        with open('data/globals.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        config["mirrorchyanCDK"] = encryption.win_encryptor(cdk)
        with open('data/globals.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"设置 MirrorChyan CDK 失败: {e}")


def set_proxys(proxys: list[str]):
    """设置系统代理"""
    try:
        if not os.path.exists('version.json'):
            temp_settings.proxys = proxys
            return
        with open('version.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        config["Proxys"] = proxys
        with open('version.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"设置系统代理失败: {e}")

def get_channel() -> str:
    """获取更新通道"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get("channel", "stable")
    except FileNotFoundError:
        return temp_settings.channel
    except json.JSONDecodeError:
        return temp_settings.channel

def set_channel(channel: str):
    """设置更新通道"""
    try:
        if not os.path.exists('version.json'):
            temp_settings.channel = channel
            return
        with open('version.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        config["channel"] = channel
        with open('version.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"设置更新通道失败: {e}")


def can_save_settings() -> bool:
    return os.path.exists('data/globals.json') and os.path.exists('version.json')
