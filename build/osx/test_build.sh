#!/bin/sh

rm -rf build
rm -rf dist

pyinstaller --onefile -y spimagine.spec 
# pyinstaller  -y spimagine.spec 
