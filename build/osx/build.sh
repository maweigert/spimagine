#!/bin/sh

#get the version string
version=`python3 -c "import os, sys;tmp = sys.stdout;sys.stdout = open(os.devnull,'w');sys.stderr= open(os.devnull,'w');import spimagine;sys.stdout = tmp;print(spimagine.__version__)"`


iconName=spimagine 

# echo "removing old files..."

# rm -rf build
# rm -rf dist

# echo "building app..."

# #onefile
# pyinstaller -w -F -y spimagine_cp3.6.spec
# #ondedir
# # pyinstaller -w -D -y spimagine.spec 



# echo "prettify bundle..."

# sed -i "" "s/icon-windowed/$iconName/g" dist/spimagine.app/Contents/Info.plist

# ./convert2icns $iconName.png
# cp $iconName.icns dist/spimagine.app/Contents/Resources/


#create the dmg
echo "creating the dmg..."
# hdiutil create dist/spimagine_v${version}.dmg -srcfolder dist/spimagine.app/
rm dist/spimagine_v${version}.dmg
appdmg dmg.json dist/spimagine_v${version}.dmg

