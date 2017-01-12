"""

mweigert@mpi-cbg.de
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import numpy as np
from spimagine.models.keyframe_model import KeyFrameList, KeyFrame, TransformData
from spimagine import Quaternion


def test_keyframes():

    k = KeyFrameList()

    k.addItem(KeyFrame(0, TransformData()))

    k.addItem(KeyFrame(1, TransformData(zoom=.0, quatRot=Quaternion(.71, .71, 0, 0), bounds=[0]*6)))

    print("interpolating.....")
    for t in np.linspace(0,1.,10):
        print(k.getTransform(t))


def test_json():
    k = KeyFrameList()

    k.addItem(KeyFrame(0, TransformData()))

    k.addItem(KeyFrame(1, TransformData(zoom=.0, quatRot=Quaternion(.71, .71, 0, 0), bounds=[0]*6)))


    s = k._to_JSON()

    print(s)

    k2 = KeyFrameList._from_JSON(s)


    print(k2.getTransform(.1))


if __name__ == '__main__':


    test_keyframes()

    test_json()