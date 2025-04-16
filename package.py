import os
import shutil

if __name__ == "__main__":

    os.system("pyinstaller --onefile SRAUpdater/__main__.py -n SRAUpdater")

    shutil.copytree("SRAUpdater/tools", "dist/tools", dirs_exist_ok=True)

    shutil.make_archive(
        base_name="SRAUpdater",
        format="zip",
        root_dir="dist",
        base_dir=".",
    )
