rm dist/*
python setup.py sdist bdist_wheel
# python setup.py register -r pypitest
# twine upload -r pypitest dist/gputools*

python setup.py register 
twine upload dist/spimagine*
