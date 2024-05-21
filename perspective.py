import cv2 as cv
import numpy as np


dst = [
    [0,0],
    [1, 0],
    [1,1],
    [0, 1]
]


src = [
    [0,1],
    [1,1],
    [1,0],
    [0,0]
]


pers = cv.getPerspectiveTransform(np.array(src, dtype=np.float32), np.array(dst, dtype=np.float32))

print(pers)