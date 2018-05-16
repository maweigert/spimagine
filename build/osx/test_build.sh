#!/bin/sh

rm -rf build
rm -rf dist

pyinstaller -w -F -y spimagine_cp3.6.spec
# pyinstaller  -y spimagine.spec 
