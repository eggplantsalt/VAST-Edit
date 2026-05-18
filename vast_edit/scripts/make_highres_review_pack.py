#!/usr/bin/env python3
"""Generate high-resolution grouped review cards for VAST-Edit semantic judging."""
from __future__ import annotations
import argparse, html, json
from collections import defaultdict
from pathlib import Path
from typing import Iterable, List
from PIL import Image, ImageDraw, ImageFont

VARIANTS = ["clean", "benign", "attack", "scrambled"]

def read_jsonl(path: Path) -> List[dict]:
    rows=[]
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line: rows.append(json.loads(line))
    return rows

def write_jsonl(rows: Iterable[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')

def base_scene_key(base_id: str, family: str) -> str:
    suffix='__'+family
    return base_id[:-len(suffix)] if base_id.endswith(suffix) else base_id

def group_id(row: dict) -> str:
    return base_scene_key(row.get('base_id',''), row.get('attack_family',''))+'__'+row.get('attack_family','')

def load_font(size:int):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf']:
        if Path(p).exists():
            return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def fit_width(img: Image.Image, width:int) -> Image.Image:
    if img.width == width: return img
    h=max(1,int(round(img.height*width/img.width)))
    return img.resize((width,h), Image.Resampling.LANCZOS)

def crop_center(img: Image.Image, frac: float=0.48) -> Image.Image:
    w,h=img.size
    cw,ch=max(1,int(w*frac)),max(1,int(h*frac))
    left=(w-cw)//2; top=(h-ch)//2
    return img.crop((left,top,left+cw,top+ch)).resize((w,h), Image.Resampling.LANCZOS)

def text_lines(draw, text, font, max_width):
    words=str(text or '').split()
    lines=[]; cur=''
    for word in words:
        trial=(cur+' '+word).strip()
        if draw.textbbox((0,0), trial, font=font)[2] <= max_width or not cur:
            cur=trial
        else:
            lines.append(cur); cur=word
    if cur: lines.append(cur)
    return lines[:4]

def make_card(gid: str, rows_by_variant: dict, out_path: Path, panel_width:int=768) -> dict:
    font=load_font(22); small=load_font(18); title_font=load_font(28)
    row_imgs=[]
    meta0=next(iter(rows_by_variant.values()))
    dummy=Image.new('RGB',(10,10)); d=ImageDraw.Draw(dummy)
    header_lines=[f'Group: {gid}', f'Family: {meta0.get("attack_family")}', f'Model: {meta0.get("model_name")}']
    header_h=18+len(header_lines)*36
    for variant in VARIANTS:
        row=rows_by_variant.get(variant)
        if not row: continue
        inp=fit_width(Image.open(row['input_keyframe']).convert('RGB'), panel_width)
        out=fit_width(Image.open(row['output_image']).convert('RGB'), panel_width)
        zoom=fit_width(crop_center(Image.open(row['input_keyframe']).convert('RGB')), panel_width//2)
        h=max(inp.height,out.height,zoom.height)+150
        w=panel_width*2+panel_width//2+80
        canvas=Image.new('RGB',(w,h),'white'); draw=ImageDraw.Draw(canvas)
        x0=20; x1=x0+panel_width+20; x2=x1+panel_width+20
        canvas.paste(inp,(x0,70)); canvas.paste(out,(x1,70)); canvas.paste(zoom,(x2,70))
        draw.text((x0,10), f'{variant.upper()} | input keyframe', fill=(0,0,0), font=font)
        draw.text((x1,10), 'edited output', fill=(0,0,0), font=font)
        draw.text((x2,10), 'center zoom cue check', fill=(0,0,0), font=font)
        y=max(inp.height,out.height,zoom.height)+80
        meta=f"sample_id: {row.get('sample_id')}"
        draw.text((20,y), meta, fill=(40,40,40), font=small); y+=26
        for label,key in [('authorized', 'authorized_instruction'),('attack_intent','attack_intent')]:
            prefix=label+': '
            lines=text_lines(draw, prefix+str(row.get(key,'')), small, w-40)
            for line in lines:
                draw.text((20,y), line, fill=(70,30,30) if label=='attack_intent' else (30,60,30), font=small); y+=24
        row_imgs.append(canvas)
    total_w=max(i.width for i in row_imgs)
    total_h=header_h+sum(i.height for i in row_imgs)+20
    card=Image.new('RGB',(total_w,total_h),(245,245,245)); draw=ImageDraw.Draw(card)
    y=12
    for line in header_lines:
        draw.text((20,y), line, fill=(0,0,0), font=title_font if y==12 else font); y+=36
    y=header_h
    for img in row_imgs:
        card.paste(img,(0,y)); y+=img.height
    out_path.parent.mkdir(parents=True, exist_ok=True); card.save(out_path)
    return {'group_id':gid,'review_card':str(out_path),'sample_ids':[rows_by_variant[v]['sample_id'] for v in VARIANTS if v in rows_by_variant],'variants':list(rows_by_variant.keys()),'attack_family':meta0.get('attack_family'),'base_group':base_scene_key(meta0.get('base_id',''),meta0.get('attack_family',''))}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--results_jsonl', required=True)
    ap.add_argument('--output_dir', required=True)
    ap.add_argument('--panel_width', type=int, default=768)
    args=ap.parse_args()
    rows=[r for r in read_jsonl(Path(args.results_jsonl)) if r.get('status')=='ok']
    grouped=defaultdict(dict)
    for r in rows: grouped[group_id(r)][r['variant']]=r
    out=Path(args.output_dir); cards=[]
    for gid, byv in sorted(grouped.items()):
        if all(v in byv for v in VARIANTS):
            safe=''.join(c if c.isalnum() or c in '-_' else '_' for c in gid)[:160]
            cards.append(make_card(gid, byv, out/'review_cards'/f'{safe}.png', args.panel_width))
    write_jsonl(cards, out/'manifest.jsonl')
    index=['<html><head><meta charset="utf-8"><title>VAST-Edit High-Res Review Pack</title></head><body>','<h1>VAST-Edit High-Res Review Pack v0.1</h1>']
    for c in cards:
        rel=html.escape(str(Path(c['review_card']).relative_to(out)))
        index.append(f"<h2>{html.escape(c['group_id'])}</h2><p>{html.escape(c['attack_family'])}</p><img src='{rel}' style='max-width:100%; height:auto;'>")
    index.append('</body></html>')
    (out/'index.html').write_text('\n'.join(index), encoding='utf-8')
    print(json.dumps({'review_cards':len(cards),'output_dir':str(out),'manifest':str(out/'manifest.jsonl'),'index':str(out/'index.html')}, indent=2))
if __name__=='__main__': main()