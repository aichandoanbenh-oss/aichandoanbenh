"""Collect training candidates; no test images or model predictions are consulted."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/training_round3_20261114'
RAW=ROOT/'data/raw/training_round3_20261114'


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    probes=[]
    for name in ['poultry_training_sources.json','poultry_training_sources_extra.json']:
        probes.extend(json.loads((OUT/name).read_text(encoding='utf-8')))
    index=BeautifulSoup((OUT/'case_index.html').read_text(encoding='utf-8'),'html.parser')
    cases=[{'url':urljoin('https://www.poultrydvm.com',a['href']),'case_title':a.get('title','')}
           for a in index.find_all('a',href=True) if a['href'].startswith('/cases/') and
           any(w in a.get('title','').lower() for w in ['eye','blind','neck','head','pox','comb','scalp','beak','face','ear'])]
    def page(row):
        try:
            response=requests.get(row['url'],timeout=20);response.raise_for_status()
            soup=BeautifulSoup(response.text,'html.parser')
            return {**row,'html':response.text,'images':[{'src':i.get('src',''),'alt':i.get('alt','')} for i in soup.find_all('img') if '/photos/' in i.get('src','') or '/cases/' in i.get('src','')]}
        except Exception as e:return {**row,'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(5) as pool:case_pages=list(pool.map(page,cases))
    (OUT/'case_pages.json').write_text(json.dumps(case_pages),encoding='utf-8')
    probes+=case_pages
    candidates=[]
    for probe in probes:
        for image in probe.get('images',[]):
            src=image.get('src','')
            if not src or any(t in src for t in ['/egg/','/eggs/','/legs_feet/','/droppings/']):continue
            candidates.append({'page_url':probe['url'],'source_url':urljoin(probe['url'],src),
                               'source_title':probe.get('case_title',probe['url'].rsplit('/',1)[-1]),
                               'source_group':probe['url'], 'class_name':'unreviewed',
                               'license':'Copyright source/contributor; local training research only, no public redistribution permission asserted'})
    candidates=list({r['source_url']:r for r in candidates}.values())
    def download(row):
        dest=RAW/(hashlib.sha256(row['source_url'].encode()).hexdigest()[:20]+'.jpg')
        try:
            if not dest.exists():
                response=requests.get(row['source_url'],timeout=(10,25));response.raise_for_status();dest.write_bytes(response.content)
            with Image.open(dest) as im:im.verify()
            return {**row,'image_path':dest.relative_to(ROOT).as_posix()}
        except Exception as e:return {**row,'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(6) as pool:candidates=list(pool.map(download,candidates))
    (OUT/'downloaded_candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2),encoding='utf-8')
    print('NEW TRAIN CANDIDATES',len(candidates),'downloaded',sum('error' not in r for r in candidates),flush=True)


if __name__=='__main__':main()
