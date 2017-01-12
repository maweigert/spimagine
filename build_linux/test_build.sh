#!/bin/sh

rm -rf build
rm -rf dist

# pyinstaller --onedir -y spimagine.spec 
pyinstaller --onefile -y spimagine.spec 
