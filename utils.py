
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