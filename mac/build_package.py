
import os
import sys
import glob
import shutil
import fnmatch
import datetime
import subprocess

from pigeonplanner.core.const import VERSION


def build_app():
    print("Setting correct values for Info.plist...")
    with open("mac/Info.plist.in") as plist_in:
        template = plist_in.read().format(version=VERSION, year=datetime.datetime.now().year)
    with open("mac/Info.plist", "w") as plist_out:
        plist_out.write(template)

    print("Compiling launcher...")
    cmd = "gcc -L$PREFIX/lib `python3-config --cflags --ldflags --embed` -o mac/pigeonplanner-launcher mac/python-launcher.c"
    subprocess.call([cmd], shell=True)

    print("Creating appbundle...")
    subprocess.call(["gtk-mac-bundler", "mac/pigeonplanner.bundle"])

    print("Cleaning up appbundle...")

    orig_working_dir = os.getcwd()
    os.chdir("mac/pigeonplanner.app/Contents/Resources/")

    # Remove all GTK/GLib translations we don't support ourselves.
    supported_languages = os.listdir("lib/python3.8/site-packages/pigeonplanner/data/languages/")
    installed_languages = os.listdir("share/locale/")
    for lang in installed_languages:
        if lang not in supported_languages:
            shutil.rmtree("share/locale/" + lang)

    os.chdir(orig_working_dir)


def build_dmg():
    print("Copying bundle to temp folder...")
    shutil.copytree("mac/pigeonplanner.app", "mac/package/pigeonplanner.app")

    print("Copying meta files to temp folder...")
    for f in ["AUTHORS", "CHANGES", "COPYING", "README"]:
        shutil.copyfile(f, "mac/package/%s.txt" % f)

    print("Creating dmg image...")
    subprocess.call(["hdiutil", "create", "mac/Pigeon_Planner-%s-Intel.dmg" % VERSION, "-ov",
                     "-volname", "Pigeon Planner",
                     "-fs", "HFS+", "-srcfolder", "mac/package"])

    print("Cleaning up...")
    shutil.rmtree("mac/package")


if __name__ == "__main__":
    if "-a" in sys.argv:
        # Build only appbundle
        build_app()
    else:
        build_app()
        build_dmg()
    print("Done!")
