"""Generate explicitly synthetic fixed-camera recordings, never real parcel footage."""
from pathlib import Path
import argparse
import cv2
import numpy as np


def generate(directory):
    root=Path(directory); root.mkdir(parents=True,exist_ok=True)
    base=np.full((240,320,3),180,dtype=np.uint8)
    # Synthetic calibration marks make fixed-camera shifts observable at the border.
    for point in ((10,10),(310,10),(10,230),(310,230)):
        cv2.circle(base,point,5,(20,20,20),-1)
    cv2.rectangle(base,(60,65),(115,130),(40,100,220),-1)
    cv2.rectangle(base,(190,65),(240,130),(200,70,40),-1)
    missing=base.copy(); missing[65:131,190:241]=180
    rearranged=base.copy()
    rearranged[65:131,60:116]=180; rearranged[65:131,190:241]=180
    cv2.rectangle(rearranged,(190,65),(245,130),(40,100,220),-1)
    cv2.rectangle(rearranged,(60,65),(110,130),(200,70,40),-1)
    occluded=base.copy(); occluded[35:205,30:290]=20
    shifted=np.roll(base,12,axis=1); shifted[:,:12]=180
    local_occlusion=base.copy(); local_occlusion[60:140,185:245]=20
    brighter=np.clip(base.astype(np.int16)+45,0,255).astype(np.uint8)
    cases={'packing':[base]*20,'unchanged':[base]*20,'missing':[missing]*20,
           'rearranged':[rearranged]*20,
           'occluded':[occluded]*20,'poor_light':[(base*.15).astype(np.uint8)]*20,
           'camera_shift':[shifted]*20,
           'localized_occlusion':[local_occlusion]*20,'illumination_drift':[brighter]*20,
           'unstable':[base if i % 2 else np.roll(base,18,axis=1) for i in range(20)]}
    for name,frames in cases.items():
        writer=cv2.VideoWriter(str(root/(name+'.avi')),cv2.VideoWriter_fourcc(*'MJPG'),10,(320,240))
        if not writer.isOpened(): raise RuntimeError('MJPG encoder unavailable')
        for frame in frames: writer.write(frame)
        writer.release()
    (root/'SYNTHETIC.txt').write_text('All videos are generated synthetic scenes. No real-world validation.\n')
    return root

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory');generate(p.parse_args().directory)
