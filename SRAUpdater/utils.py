import subprocess
import sys
import psutil

class Castorice:
    """
    - Easter Egg:

    你懂的，因为，她啊，碰一下生命就会导致生命的离去...

    - 介绍: \n
    「欢迎来到奥赫玛，我是遐蝶。 
     抱歉，与他人保持一定距离是我的习惯…如果阁下愿意，我自然可以站近些。 
    「死荫的侍女」遐蝶 Castorice那敬爱死亡的国度，终日飘雪的哀地里亚，今日已沉入甘甜的酣眠。 
    冥河的女儿遐蝶，寻索「死亡」火种的黄金裔，启程吧。
    你要呵护世间魂灵的恸哭，拥抱命运的孤独——生死皆为旅途，当蝴蝶停落枝头，那凋零的又将新生。
    """

    @staticmethod
    def touch(process: str | int) -> None:
        """ 触摸一个进程 """
        try:
            if isinstance(process, str):
                for p in psutil.process_iter():
                    if p.name() == process:
                        _process = psutil.Process(p.pid)
                        _process.kill()
                        return
            else:
                _process = psutil.Process(process)
                _process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    @staticmethod
    def look(process_name: str) -> bool:
        #既然这样太卜自己再给这两函数起个贴切的名字吧
        """
        Check if there is any running process that contains the given name string.

        Args:
            process_name (str): Name of the process to be searched.
        Returns:
            True if the process is running, otherwise False.
        """
        # Iterate over all running processes
        for proc in psutil.process_iter(['name']):
            try:
                # Check if process name contains the given name string
                if process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    @staticmethod
    def life(path: str, shell=False) -> bool:
        """运行指定exe程序

        Args:
            shell: 通过shell运行
            path: 程序路径

        Returns:
            True if opened successfully, False otherwise.
        """
        try:
            subprocess.Popen(path, shell=shell)
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False
