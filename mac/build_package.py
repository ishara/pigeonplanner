
import shutil
import datetime
import subprocess

from pigeonplanner.core.const import VERSION

print "Setting correct values for Info.plist..."
with open("mac/Info.plist.in") as plist_in:
    template = plist_in.read().format(version=VERSION, year=datetime.datetime.now().year)
with open("mac/Info.plist", "w") as plist_out:
    plist_out.write(template)

print "Creating appbundle..."
subprocess.call(["gtk-mac-bundler", "mac/pigeonplanner.bundle"])

print "Copying bundle to temp folder..."
shutil.copytree("mac/pigeonplanner.app", "mac/package/pigeonplanner.app")

print "Copying meta files to temp folder..."
for f in ["AUTHORS", "CHANGES", "COPYING", "README"]:
    shutil.copyfile(f, "mac/package/%s.txt" % f)

print "Creating dmg image..."
subprocess.call(["hdiutil", "create", "mac/Pigeon_Planner-%s-Intel.dmg" % VERSION, "-ov",
                 "-volname", "Pigeon Planner",
                 "-fs", "HFS+", "-srcfolder", "mac/package"])

print "Cleaning up..."
shutil.rmtree("mac/package")

print "Done!"
