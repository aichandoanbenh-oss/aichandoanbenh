import io
import os
import json
import secrets
import sqlite3
import threading
import warnings
from pathlib import Path
from contextlib import contextmanager

import torch
from PIL import Image, ImageOps, UnidentifiedImageError
from torchvision import models, transforms
from fastapi import FastAPI, Request, Response, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from web.knowledge import information, reply
from web.model_factory import from_checkpoint
from web.rabies import Screening, assess, QUESTIONS

ROOT=Path(__file__).resolve().parents[1]
STATE=Path(os.environ.get('VETLENS_STATE_DIR',str(ROOT/'data/web'))); STATE.mkdir(parents=True,exist_ok=True)
CATALOG=json.loads((ROOT/'models_catalog.json').read_text(encoding='utf-8'))
SPECIES={'dog':'Chó','cattle':'Bò','chicken':'Gà','pig':'Lợn'}
app=FastAPI(title='VetLens · Nhận diện ảnh động vật')
app.mount('/static',StaticFiles(directory=ROOT/'web/static'),name='static')
torch.set_num_threads(4)
MODELS={}; LOCK=threading.Lock()

@contextmanager
def db():
    con=sqlite3.connect(STATE/'history.sqlite3',timeout=30)
    con.row_factory=sqlite3.Row
    try:
        yield con
        con.commit()
    finally: con.close()

with db() as con:
    con.executescript('''CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY, owner TEXT, title TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, chat TEXT, role TEXT, content TEXT, result TEXT, image BLOB, created TEXT DEFAULT CURRENT_TIMESTAMP);''')

@app.middleware('http')
async def session(request:Request,call_next):
    token=request.cookies.get('vet_session','')
    valid=len(token)==64 and all(c in '0123456789abcdef' for c in token)
    request.state.owner=token if valid else secrets.token_hex(32)
    response=await call_next(request)
    if not valid: response.set_cookie('vet_session',request.state.owner,httponly=True,samesite='strict',max_age=365*86400)
    response.headers['X-Content-Type-Options']='nosniff'
    return response

def owned(con,chat,owner):
    if not con.execute('SELECT id FROM chats WHERE id=? AND owner=?',(chat,owner)).fetchone(): raise HTTPException(404,'Không tìm thấy hội thoại.')

def add(con,chat,role,content,result=None,image=None):
    return con.execute('INSERT INTO messages(chat,role,content,result,image) VALUES(?,?,?,?,?)',(chat,role,content,json.dumps(result,ensure_ascii=False) if result else None,image)).lastrowid

@app.get('/')
def index(): return FileResponse(ROOT/'web/static/index.html')

@app.get('/install')
def install(): return FileResponse(ROOT/'web/static/install.html')

@app.get('/sw.js')
def service_worker():
    return FileResponse(ROOT/'web/static/sw.js',media_type='application/javascript',headers={'Cache-Control':'no-cache','Service-Worker-Allowed':'/'})

@app.get('/healthz')
def health(): return {'status':'ok'}

@app.get('/api/models')
def catalog():
    return [{ 'id':s,'name':name,'classes':list(CATALOG[s].get('web_labels_vi',CATALOG[s]['labels_vi']).values()),'available':(ROOT/CATALOG[s].get('web_checkpoint',CATALOG[s]['checkpoint'])).exists()} for s,name in SPECIES.items()]

@app.get('/api/chats')
def chats(request:Request):
    with db() as con: return [dict(r) for r in con.execute('SELECT id,title,created FROM chats WHERE owner=? ORDER BY rowid DESC',(request.state.owner,))]

@app.post('/api/chats')
def create(request:Request):
    chat=secrets.token_hex(16)
    with db() as con: con.execute('INSERT INTO chats(id,owner,title) VALUES(?,?,?)',(chat,request.state.owner,'Hội thoại mới'))
    return {'id':chat}

@app.get('/api/chats/{chat}')
def messages(chat:str,request:Request):
    with db() as con:
        owned(con,chat,request.state.owner)
        return [{'id':r['id'],'role':r['role'],'content':r['content'],'result':stored_result(r['result']),'image':f"/api/images/{r['id']}" if r['image'] else None} for r in con.execute('SELECT * FROM messages WHERE chat=? ORDER BY id',(chat,))]

def stored_result(raw):
    if not raw:return None
    result=json.loads(raw)
    if result.get('kind')!='rabies_screening' and result.get('label'):
        result['info']=information(result['label'])
    return result

@app.delete('/api/chats/{chat}')
def delete(chat:str,request:Request):
    with db() as con:
        owned(con,chat,request.state.owner)
        con.execute('DELETE FROM messages WHERE chat=?',(chat,)); con.execute('DELETE FROM chats WHERE id=?',(chat,))
    return {'ok':True}

@app.get('/api/images/{mid}')
def saved_image(mid:int,request:Request):
    with db() as con:
        r=con.execute('SELECT image FROM messages JOIN chats ON messages.chat=chats.id WHERE messages.id=? AND owner=?',(mid,request.state.owner)).fetchone()
        if not r or not r['image']: raise HTTPException(404)
        return Response(r['image'],media_type='image/jpeg',headers={'Cache-Control':'private, no-store'})

def predict(species,im):
    with LOCK:
        if species not in MODELS:
            p=ROOT/CATALOG[species].get('web_checkpoint',CATALOG[species]['checkpoint'])
            if not p.exists(): raise HTTPException(503,'Chưa có trọng số cho loài này.')
            ck=torch.load(p,map_location='cpu',weights_only=True)
            model=from_checkpoint(ck)
            tf=transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize(ck['mean'],ck['std'])])
            MODELS[species]=(model,tf,ck['classes'])
        model,tf,classes=MODELS[species]
        with torch.inference_mode(): scores=model(tf(im).unsqueeze(0)).softmax(1)[0].tolist()
    ranked=sorted(zip(classes,scores),key=lambda a:a[1],reverse=True)
    label=ranked[0][0]; names=CATALOG[species].get('web_labels_vi',CATALOG[species]['labels_vi'])
    warning='Gợi ý thử nghiệm, chưa xác nhận bệnh. Lớp unknown chỉ học một số ảnh ngoài phạm vi, không bảo đảm phát hiện mọi ảnh lạ.'
    if label=='unknown':warning='Ảnh được phân vào unknown: không hiển thị gợi ý bệnh. Kết quả này không chứng minh con vật khỏe mạnh.'
    elif label=='oral_signs_unverified':warning='Dấu hiệu miệng/nước dãi cần đánh giá; không xác nhận hoặc loại trừ dại. Chỉ 6 ảnh nguồn, chưa đủ đánh giá khả năng tổng quát.'
    if species=='dog':warning+=' Nhánh dấu hiệu miệng đã bỏ sót 1/1 ảnh kiểm thử; không dùng kết quả âm tính để loại trừ dại.'
    return {'species':species,'label':label,'name':names[label],'warning':warning,'scores':[{'label':c,'name':names[c],'score':p} for c,p in ranked], 'info':information(label)}

@app.post('/api/chats/{chat}/predict')
def analyze(chat:str,request:Request,species:str=Form(...),note:str=Form(''),file:UploadFile=File(...)):
    with db() as con: owned(con,chat,request.state.owner)
    if species not in SPECIES: raise HTTPException(400,'Loài không hợp lệ.')
    if len(note)>2000: raise HTTPException(400,'Mô tả tối đa 2.000 ký tự.')
    raw=file.file.read(10*1024*1024+1)
    if len(raw)>10*1024*1024: raise HTTPException(413,'Ảnh tối đa 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.width*source.height>20_000_000: raise ValueError('Ảnh quá lớn (tối đa 20 megapixel).')
                if min(source.size)<32: raise ValueError('Ảnh quá nhỏ; cần ít nhất 32 × 32 pixel.')
                im=ImageOps.exif_transpose(source).convert('RGB'); im.load()
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning) as e:
        raise HTTPException(400,'Ảnh không hợp lệ hoặc vượt giới hạn kích thước.') from e
    result=predict(species,im)
    preview=im.copy(); preview.thumbnail((1200,1200)); output=io.BytesIO(); preview.save(output,format='JPEG',quality=85)
    with db() as con:
        owned(con,chat,request.state.owner)
        add(con,chat,'user',f'Ảnh {SPECIES[species].lower()}'+(f' · {note}' if note else ''),image=output.getvalue())
        add(con,chat,'assistant','Kết quả phân loại ảnh thử nghiệm',result=result)
        con.execute("UPDATE chats SET title=? WHERE id=? AND title='Hội thoại mới'",(f"{SPECIES[species]} · {result['name']}",chat))
    return result

class Question(BaseModel):
    text:str=Field(min_length=1,max_length=2000)

@app.get('/api/rabies/questions')
def rabies_questions(): return QUESTIONS

@app.post('/api/chats/{chat}/rabies')
def rabies_screen(chat:str,answers:Screening,request:Request):
    result=assess(answers)
    names={'yes':'Có','no':'Không','unknown':'Không rõ'}
    with db() as con:
        owned(con,chat,request.state.owner)
        add(con,chat,'user','Sàng lọc nguy cơ bệnh dại ở chó\n\n'+'\n'.join(f'{QUESTIONS[k]} — {names[v]}' for k,v in answers.model_dump().items()))
        add(con,chat,'assistant','Sàng lọc nguy cơ bệnh dại',result=result)
        con.execute("UPDATE chats SET title=? WHERE id=? AND title='Hội thoại mới'",('Chó · Sàng lọc nguy cơ dại',chat))
    return result

@app.post('/api/chats/{chat}/message')
def chat_message(chat:str,question:Question,request:Request):
    if not question.text.strip(): raise HTTPException(400,'Nhập câu hỏi trước khi gửi.')
    with db() as con:
        owned(con,chat,request.state.owner)
        last=con.execute('SELECT result FROM messages WHERE chat=? AND result IS NOT NULL ORDER BY id DESC LIMIT 1',(chat,)).fetchone()
        answer=reply(question.text,json.loads(last['result']) if last else None)
        add(con,chat,'user',question.text); add(con,chat,'assistant',answer)
    return {'text':answer}
