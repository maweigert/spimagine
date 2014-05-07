#!/bin/sh

iconName=spimagine 


pyinstaller -w -F -y spimagine.spec 

sed -i "" "s/icon-windowed/$iconName/g" dist/SpImagine.app/Contents/Info.plist

./convert2icns $iconName.png
cp $iconName.icns dist/SpImagine.app/Contents/Resources/
mv dist/spimagine_render dist/SpImagine.app/Contents/MacOS
