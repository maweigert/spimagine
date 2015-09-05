#!/bin/sh

iconName=spimagine 

echo "removing old files..."

rm -rf build
rm -rf dist

echo "building app..."

pyinstaller -w -F -y spimagine.spec 

echo "prettify bundle..."

sed -i "" "s/icon-windowed/$iconName/g" dist/SpImagine.app/Contents/Info.plist

./convert2icns $iconName.png
cp $iconName.icns dist/SpImagine.app/Contents/Resources/
mv dist/spimagine_render dist/SpImagine.app/Contents/MacOS

#create the dmg
echo "creating the dmg..." 
hdiutil create dist/SpImagine.dmg -srcfolder dist/SpImagine.app/
