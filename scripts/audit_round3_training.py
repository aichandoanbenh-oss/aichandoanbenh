"""Audit new training candidates against all existing data and locked tests."""
import concurrent.futures
import json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from prepare_chicken_improvement import describe

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/training_round3_20261114'


def main():
    rows=json.loads((OUT/'downloaded_candidates.json').read_text(encoding='utf-8'))
    if (OUT/'dinev_candidates.json').exists():
        rows+=json.loads((OUT/'dinev_candidates.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(8) as pool:rows=list(pool.map(describe,[r for r in rows if 'error' not in r]))
    existing=json.loads((ROOT/'reports/external_round2_20261114/existing_hash_index.json').read_text(encoding='utf-8'))
    tests=json.loads((ROOT/'thaytri/test/manifest.json').read_text(encoding='utf-8'))
    forbidden_cases=set()
    for i,row in enumerate(rows):
        row['review_id']=i
        if 'error' in row:continue
        near=min(existing,key=lambda old:min((row['phashes'][0]^h).bit_count() for h in old['phashes']))
        pd=min((row['phashes'][0]^h).bit_count() for h in near['phashes'])
        dd=min((row['hashes'][0]^h).bit_count() for h in near['hashes'])
        row['existing_phash']=pd;row['nearest_existing']=near['image_path']
        row['exclude']=pd<=10 or (pd<=14 and dd<=6)
        for test in tests:
            p=min((row['phashes'][0]^h).bit_count() for h in test['phashes'])
            d=min((row['hashes'][0]^h).bit_count() for h in test['hashes'])
            if row['source_url']==test['source_url'] or p<=12 or (p<=16 and d<=8):
                row['exclude']=True;row['test_overlap']=test['image_path']
                if '/cases/' in row['source_group']:forbidden_cases.add(row['source_group'])
                break
    for row in rows:
        if row['source_group'] in forbidden_cases:row['exclude']=True;row['excluded_case_overlap']=True
    (OUT/'audited_new_candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    good=[r for r in rows if not r.get('exclude') and 'error' not in r]
    for start in range(0,len(good),30):
        chunk=good[start:start+30];sheet=Image.new('RGB',(1200,((len(chunk)+4)//5)*190),'#eeeeee');draw=ImageDraw.Draw(sheet)
        for j,row in enumerate(chunk):
            x=j%5*240;y=j//5*190
            with Image.open(ROOT/row['image_path']) as im:sheet.paste(ImageOps.contain(ImageOps.exif_transpose(im).convert('RGB'),(232,145)),(x,y))
            draw.text((x,y+146),f"ID {row['review_id']} | p{row['existing_phash']}\n{row['source_title'][:29]}",fill='black')
        sheet.save(OUT/f'new_training_review_{start//30}.jpg')
    print('NEW AUDIT',len(rows),'eligible',len(good),'sheets',(len(good)+29)//30,flush=True)


if __name__=='__main__':main()
