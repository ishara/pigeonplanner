
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

    pp_dir = "lib/python3.8/site-packages/pigeonplanner/"

    # Remove all GTK/GLib translations we don't support ourselves.
    supported_languages = os.listdir(os.path.join(pp_dir, "data/languages/"))
    installed_languages = os.listdir("share/locale/")
    for lang in installed_languages:
        if lang not in supported_languages:
            shutil.rmtree("share/locale/" + lang)

    # Remove icons we don't use.
    icon_directories = [
        "share/icons/hicolor",
        "share/icons/Adwaita/256x256",
        "share/icons/Adwaita/512x512",
        "share/icons/Adwaita/*/actions",
        "share/icons/Adwaita/*/apps",
        "share/icons/Adwaita/*/categories",
        "share/icons/Adwaita/*/devices",
        "share/icons/Adwaita/*/emblems",
        "share/icons/Adwaita/*/emotes",
        # "share/icons/Adwaita/*/legacy",
        # "share/icons/Adwaita/*/mimetypes",  # TODO: ?
        "share/icons/Adwaita/*/places",
        "share/icons/Adwaita/*/status",
        "share/icons/Adwaita/*/ui",
    ]
    icons_to_keep = ["*image-missing*"]
    for directory in icon_directories:
        icons = glob.glob(os.path.join(directory, "**", "*.png"), recursive=True)
        for icon in icons:
            if any(fnmatch.fnmatch(icon, pattern) for pattern in icons_to_keep):
                continue
            os.remove(icon)

    ui_src_dir = os.path.join(pp_dir, "ui/*")
    used_icon_names = set()
    checked_icon_names = {"computer", "pda", "phone"}
    for filename in glob.glob("share/icons/Adwaita/*/legacy/**/*.png", recursive=True):
        icon_name, ext = os.path.splitext(os.path.basename(filename))
        if icon_name not in checked_icon_names:
            cmd = """grep -Ir "%s" --include="*.py" --include="*.ui" %s""" % (icon_name, ui_src_dir)
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
            if len(result.stdout) != 0:
                used_icon_names.add(icon_name)
            checked_icon_names.add(icon_name)
        if icon_name not in used_icon_names:
            os.remove(filename)

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
