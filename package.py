import os
import shutil

if __name__ == "__main__":

    os.system("pyinstaller -i=SRAicon.ico --onefile main.py -n SRAUpdater")

    shutil.copytree("tools", "dist/tools", dirs_exist_ok=True)

    shutil.make_archive(
        base_name="SRAUpdater",
        format="zip",
        root_dir="dist",
        base_dir=".",
    )
