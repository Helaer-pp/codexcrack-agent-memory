"""Render two views of one tight display ROI from previously saved detections."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


PANEL = (720, 360)


class RoiComparison:
    def __init__(self):
        self.last_relative_extent = None
        self.font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 17)

    def crop_box(self, row, size):
        p1, p2 = np.array(row['anchors'])
        center = (p1 + p2) / 2
        spacing = np.linalg.norm(p2 - p1)
        points = [p for segment in row['segments'] for p in segment]
        if row['tip_px'] is not None:
            points.append(row['tip_px'])
        if points:
            relative = np.asarray(points) - center
            self.last_relative_extent = np.array([relative.min(0), relative.max(0)])
        # On a missing frame, keep the last view aligned to the current anchors.
        # Its contents are always drawn from this frame alone.
        forward = (p2 - p1)[::-1] * [1, -1]
        extent = [center, center + .5 * forward]
        if self.last_relative_extent is not None:
            extent.extend(center + self.last_relative_extent)
        pad = max(6, .14 * spacing)
        lo, hi = np.min(extent, axis=0) - pad, np.max(extent, axis=0) + pad
        # Use an integer 2:1 box to preserve pixel aspect on both panels.
        half_width = int(np.ceil(max((hi[0]-lo[0])/2, hi[1]-lo[1], spacing*.48)))
        half_width = max(1, min(half_width, size[0]//2, size[1]))
        w, h = 2 * half_width, half_width
        x, y = np.clip(np.rint((lo+hi)/2 - [w/2, h/2]).astype(int), 0, np.array(size)-[w,h])
        box = (int(x), int(y), int(x+w), int(y+h))
        if not all(x <= a < x+w and y <= b < y+h for a,b in points):
            raise ValueError(f"Confirmed path outside display ROI in frame {row['frame']}")
        return box

    def render(self, image, row):
        box = self.crop_box(row, image.size)
        patch = image.crop(box).resize(PANEL, Image.Resampling.BICUBIC).convert('RGB')
        overlay = patch.copy()
        draw = ImageDraw.Draw(overlay)
        scale = PANEL[0] / (box[2] - box[0])
        def xy(p):
            return ((p[0]-box[0]+.5)*scale-.5, (p[1]-box[1]+.5)*scale-.5)
        for segment in row['segments']:
            if len(segment) >= 2:
                draw.line([xy(p) for p in segment], fill='#ef4339', width=2)
        tip = row['tip_px']
        if tip is not None:
            x,y = xy(tip)
            draw.ellipse((x-5,y-5,x+5,y+5), outline='#ffb000', width=2)
            text = f'({tip[0]:.2f}, {tip[1]:.2f}) px'
            draw.rectangle(draw.textbbox((6,4), text, font=self.font), fill='#17212a')
            draw.text((6,4), text, font=self.font, fill='#ffd267')
        canvas = Image.new('RGB',(PANEL[0]*2+2,PANEL[1]),'#17212a')
        canvas.paste(patch,(0,0))
        canvas.paste(overlay,(PANEL[0]+2,0))
        return canvas, box


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    parser.add_argument('images',type=Path)
    parser.add_argument('dest',type=Path)
    args = parser.parse_args()
    output_root = Path(__file__).resolve().parents[2] / 'output'
    if not args.dest.resolve().is_relative_to(output_root):
        parser.error('Output must be inside the project output folder.')
    rows = [json.loads(line) for line in (args.run/'paths.jsonl').read_text(encoding='utf-8').splitlines()]
    args.dest.mkdir(parents=True,exist_ok=False)
    frames = args.dest/'frames'
    frames.mkdir()
    exporter = RoiComparison()
    for i, row in enumerate(rows,1):
        if row['frame'] != i:
            raise ValueError('Frame sequence mismatch')
        with Image.open(args.images/row['image']) as source:
            frame, box = exporter.render(source.convert('L'),row)
            name = f"{i:04d}_{Path(row['image']).stem}.png"
            frame.save(frames/name)
            with Image.open(frames/name) as saved:
                raw = source.convert('L').crop(box).resize(PANEL,Image.Resampling.BICUBIC).convert('RGB')
                assert np.array_equal(raw,saved.crop((0,0,*PANEL)))
                if row['tip_px'] is None and not row['segments']:
                    assert np.array_equal(raw,saved.crop((PANEL[0]+2,0,saved.width,saved.height)))
    assert len(list(frames.glob('*.png'))) == len(rows)
    print(f'{len(rows)} ROI pairs verified.')

if __name__=='__main__':
    main()

