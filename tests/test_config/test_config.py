import sys
import os
import six

from spimagine.config.myconfigparser import MyConfigParser

def rel_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__),name))




def test_config():
    
    vals = {
        "id_platform": 99,
        "id_device" : 101,
        "colormap" : "foo",
        "texture_width" : 754,
        "window_width" : 123,
        "window_height": 123,
        "max_steps": 400}

    text = "\n".join(["%s = %s "%(k,v) for k,v in six.iteritems(vals)])

    fpath = rel_path("config_example.txt")
    with open(fpath,"w") as f:
        f.write(text)


    config_parser = MyConfigParser(fpath)

    for k,v in six.iteritems(vals):
        cv = type(v)(config_parser.get(k))
        print(k,v,cv)
        assert v == cv


if __name__ == '__main__':
    test_config()