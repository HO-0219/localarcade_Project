from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"Yuni.png"
OUT=ROOT/"frontend"/"public"/"yuni"
CENTERS=[180,420,660,900,1140,1370]
ROWS={"idle":(270,475),"walk":(545,735),"run":(805,990)}
CANVAS=(240,220)

def remove_background(crop:Image.Image)->Image.Image:
    rgb=np.asarray(crop.convert("RGB"),dtype=np.float32)
    h,w,_=rgb.shape
    # The new sheet has a horizontal gray-blue gradient. Estimate it for every
    # scanline from both safe edges, then retain only pixels differing from it.
    left=np.median(rgb[:,:12],axis=1)[:,None,:]
    right=np.median(rgb[:,-12:],axis=1)[:,None,:]
    blend=np.linspace(0,1,w,dtype=np.float32)[None,:,None]
    background=left*(1-blend)+right*blend
    distance=np.sqrt(np.sum((rgb-background)**2,axis=2))
    alpha=np.clip((distance-20)*11,0,255).astype(np.uint8)
    alpha_img=Image.fromarray(alpha,"L").filter(ImageFilter.GaussianBlur(.45))
    rgba=crop.convert("RGBA");rgba.putalpha(alpha_img)
    return rgba

def extract()->None:
    source=Image.open(SOURCE)
    OUT.mkdir(parents=True,exist_ok=True)
    generated={}
    for action,(top,bottom) in ROWS.items():
        folder=OUT/action;folder.mkdir(exist_ok=True)
        generated[action]=[]
        for index,center in enumerate(CENTERS):
            left=max(0,center-108);right=min(source.width,center+108)
            sprite=remove_background(source.crop((left,top,right,bottom)))
            alpha=sprite.getchannel("A");bbox=alpha.point(lambda a:255 if a>45 else 0).getbbox()
            if bbox:
                sprite=sprite.crop((max(0,bbox[0]-3),max(0,bbox[1]-3),min(sprite.width,bbox[2]+3),min(sprite.height,bbox[3]+3)))
            canvas=Image.new("RGBA",CANVAS,(0,0,0,0))
            canvas.alpha_composite(sprite,((CANVAS[0]-sprite.width)//2,CANVAS[1]-sprite.height-5))
            target=folder/f"{index}.png";canvas.save(target,optimize=True);generated[action].append(canvas)
    # No jump row exists in this atlas. Reuse three clean run poses while the
    # physics supplies the actual vertical motion.
    jump=OUT/"jump";jump.mkdir(exist_ok=True)
    for index,source_index in enumerate((1,2,3)):
        generated["run"][source_index].save(jump/f"{index}.png",optimize=True)

if __name__=="__main__":extract()
