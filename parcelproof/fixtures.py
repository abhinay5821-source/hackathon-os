"""Generate explicitly synthetic fixed-camera recordings, never real parcel footage."""
from pathlib import Path
import argparse
import cv2
import numpy as np


def generate(directory):
    root=Path(directory); root.mkdir(parents=True,exist_ok=True)
    base=np.full((240,320,3),180,dtype=np.uint8)
    cv2.rectangle(base,(60,65),(115,130),(40,100,220),-1)
    cv2.rectangle(base,(190,65),(240,130),(200,70,40),-1)
    missing=base.copy(); missing[65:131,190:241]=180
    occluded=base.copy(); occluded[35:205,30:290]=20
    cases={'packing':base,'unchanged':base,'missing':missing,'occluded':occluded,'poor_light':(base*.15).astype(np.uint8)}
    for name,frame in cases.items():
        writer=cv2.VideoWriter(str(root/(name+'.avi')),cv2.VideoWriter_fourcc(*'MJPG'),10,(320,240))
        if not writer.isOpened(): raise RuntimeError('MJPG encoder unavailable')
        for _ in range(20): writer.write(frame)
        writer.release()
    (root/'SYNTHETIC.txt').write_text('All videos are generated synthetic scenes. No real-world validation.\n')
    return root

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory');generate(p.parse_args().directory)
