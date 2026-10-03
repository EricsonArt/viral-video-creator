import cv2, numpy as np, json
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
_seg=None
def seg():
    global _seg
    if _seg is None:
        o=vision.ImageSegmenterOptions(base_options=mpt.BaseOptions(model_asset_path="models/selfie_multiclass.tflite"),
            running_mode=vision.RunningMode.IMAGE, output_confidence_masks=True, output_category_mask=False)
        _seg=vision.ImageSegmenter.create_from_options(o)
    return _seg
def fg_conf(bgr, x0,y0,x1,y1):
    """foreground confidence (1 - background) for crop; returns float map in crop size"""
    rgb=cv2.cvtColor(bgr[y0:y1,x0:x1],cv2.COLOR_BGR2RGB)
    h,w=rgb.shape[:2]; side=max(h,w)
    sq=np.zeros((side,side,3),np.uint8); sq[:h,:w]=rgb
    r=seg().segment(mp.Image(image_format=mp.ImageFormat.SRGB,data=sq))
    bgc=r.confidence_masks[0].numpy_view()
    fg=1.0-bgc
    fg=cv2.resize(fg,(side,side),interpolation=cv2.INTER_CUBIC)[:h,:w]
    return np.clip(fg,0,1)
