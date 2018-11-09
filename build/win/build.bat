version=`python3 -c "import os, sys;tmp = sys.stdout;sys.stdout = open(os.devnull,'w');sys.stderr= open(os.devnull,'w');import spimagine;sys.stdout = tmp;print(spimagine.__version__)"`


rm -rf build/
rm -rf dist/



pyinstaller.exe -y --icon=spimagine.ico  spimagine.spec
