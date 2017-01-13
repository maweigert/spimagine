#!/bin/sh

#get the version string
version=`python -c "import os, sys;tmp = sys.stdout;sys.stdout = open(os.devnull,'w');sys.stderr= open(os.devnull,'w');import spimagine;sys.stdout = tmp;print(spimagine.__version__)"`


iconName=spimagine 

echo "removing old files..."

rm -rf build
rm -rf dist

echo "building app..."

#onefile
pyinstaller -w -F -y spimagine.spec
#ondedir
# pyinstaller -w -D -y spimagine.spec 

echo "prettify bundle..."

sed -i "" "s/icon-windowed/$iconName/g" dist/spimagine.app/Contents/Info.plist

./convert2icns $iconName.png
cp $iconName.icns dist/spimagine.app/Contents/Resources/

# mv dist/spimagine_render dist/spimagine.app/Contents/MacOS

#create the dmg
echo "creating the dmg..."
hdiutil create dist/spimagine_v${version}.dmg -srcfolder dist/spimagine.app/
# hdiutil create dist/spimagine.dmg -srcfolder dist/spimagine.app/
