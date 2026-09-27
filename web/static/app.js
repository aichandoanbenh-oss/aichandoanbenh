const $=s=>document.querySelector(s);
let chat=null,species='dog',busy=false,previewURL=null;
const hints={dog:'Chó: ảnh da hoặc vùng miệng; ảnh không xác nhận hay loại trừ dại.',cattle:'Bò: ảnh da, miệng, chân hoặc bầu vú.',pig:'Lợn: ảnh vùng da bất thường.',chicken:'Gà: ảnh phân, không dùng ảnh toàn thân.'};
function hint(){$('#hint').textContent=hints[species];const entry=$('#rabies-entry');if(entry)entry.hidden=species!=='dog';}hint();
async function api(url,options={}){const r=await fetch(url,options);if(!r.ok){let e;try{e=await r.json();}catch{}throw Error(typeof e?.detail==='string'?e.detail:'Yêu cầu không thành công. Vui lòng thử lại.');}return r.json();}
function node(tag,cls,text){const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el;}
function markStale(){if(!$('#messages .result'))return;$('#messages').classList.add('stale');if(!$('#messages .stale-note'))$('#messages').prepend(node('p','stale-note','Kết quả bên dưới thuộc ảnh hoặc loài trước. Hãy gửi ảnh để phân tích lại.'));}
function status(text){$('#status').textContent=text;}
function setBusy(value){busy=value;document.querySelectorAll('button,textarea,input').forEach(el=>el.disabled=value);$('#send').textContent=value?'Đang xử lý…':'Bắt đầu phân tích →';}
async function history(){const rows=await api('/api/chats');const nav=$('#history');nav.replaceChildren();if(!rows.length)nav.append(node('p','empty-history','Hội thoại của bạn sẽ xuất hiện ở đây.'));for(const r of rows){const row=node('div','history-row'+(chat===r.id?' active':''));const open=node('button','open','◌  '+r.title);open.title=r.title;open.onclick=async()=>{if(busy)return;chat=r.id;clearFile();try{await render();await history();}catch(e){status(e.message);}};const del=node('button','delete','×');del.setAttribute('aria-label','Xóa '+r.title);del.onclick=async()=>{if(busy||!confirm('Xóa hội thoại này và ảnh đã lưu?'))return;try{await api('/api/chats/'+r.id,{method:'DELETE'});if(chat===r.id){chat=null;$('#messages').replaceChildren();$('#welcome').hidden=false;}await history();}catch(e){status(e.message);}};row.append(open,del);nav.append(row);}}
function outlineIcon(emergency=false){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('class','section-icon');svg.setAttribute('aria-hidden','true');const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',emergency?'M12 3 2 21h20L12 3ZM12 9v5m0 3v1':'M8 3h8v3H8zM8 5H5v16h14V5h-3M8 11h8M8 15h8');svg.append(path);return svg;}
function resultCard(r){
 if(r.kind==='rabies_screening')return rabiesCard(r);
 const unknown=r.label==='unknown',healthy=['healthy','Healthy'].includes(r.label);
 const card=node('div','result reference-result'+(unknown?' unknown':healthy?' control-result':''));
 const head=node('div','result-summary compact-summary');
 const badge=node('span','result-alert-icon',unknown?'?':healthy?'i':'!');badge.setAttribute('aria-hidden','true');
 head.append(badge,node('h3','',unknown?'Chưa nhận diện được':healthy?r.name:'Nghi ngờ: '+r.name));
 if(r.scores.length)head.append(node('span','score-badge','Điểm: '+(r.scores[0].score*100).toFixed(1)+'%'));
 card.append(head);
 const meta=node('div','result-meta');
 const speciesName={dog:'Chó',cattle:'Bò',pig:'Lợn',chicken:'Gà'}[r.species]||'Chưa chọn';
 for(const [title,value] of [['Loài vật nuôi',speciesName],['Loại đầu vào',r.species==='chicken'?'Ảnh phân':'Ảnh quan sát'],['Đánh giá chuyên môn','Cần thú y xác minh']]){const tile=node('div','meta-tile');tile.append(node('span','',title),node('strong','',value));meta.append(tile);}card.append(meta);
 const makeGroup=(title,cls)=>{const group=node('details','advice-group '+cls);group.open=true;const summary=node('summary','');summary.append(outlineIcon(),document.createTextNode(title));group.append(summary);card.append(group);return group;};
 const add=(parent,key,title,list=false)=>{if(!r.info[key])return;const section=node('section','care-section'+(key==='urgent'?' emergency':''));section.dataset.key=key;section.append(node('h4','',title));if(list){const ol=node('ol','advice-steps');const sentences=r.info[key].match(/[^.!?]+(?:[.!?]+|$)/g)||[r.info[key]];for(const sentence of sentences)if(sentence.trim())ol.append(node('li','',sentence.trim()));section.append(ol);}else section.append(node('p','text',r.info[key]));parent.append(section);};
 const detail=makeGroup('Thông tin chi tiết','details-group');add(detail,'signs','Dấu hiệu tham khảo');add(detail,'causes','Nguyên nhân');
 const care=makeGroup('Khuyến nghị chăm sóc & điều trị','treatment-group');add(care,'care','Xử trí ban đầu',true);add(care,'treatment','Hướng điều trị',true);add(care,'medications','Thuốc tham khảo — cần thú y xác nhận');
 const urgent=makeGroup('Khi cần thú y ngay','urgent-group');add(urgent,'urgent','Dấu hiệu cần chú ý');
 const prevention=makeGroup('Phòng tránh & theo dõi','prevention-group');add(prevention,'prevention','Cách phòng tránh',true);add(prevention,'monitoring','Theo dõi và kiểm tra',true);
 const scores=node('details','score-disclosure');scores.append(node('summary','','Xem điểm phân loại'));
 for(const [rank,s] of r.scores.slice(0,unknown?1:3).entries()){const row=node('div','score');row.dataset.rank=rank;row.append(node('span','',s.name),node('span','score-label','Điểm phân loại: '+(s.score*100).toFixed(1)+'%'));const track=node('div','track'),bar=node('i');bar.style.width=(s.score*100)+'%';track.append(bar);row.append(track);scores.append(row);}
 scores.append(node('small','','Điểm phân loại tương đối của mô hình, không phải xác suất mắc bệnh đã hiệu chỉnh. Mô tả bạn nhập được lưu để tham khảo; model chỉ phân tích ảnh.'));card.append(scores);
 if(unknown)card.append(node('p','unknown-note','Chưa nhận diện được không có nghĩa là khỏe mạnh.'));
 return card;
}
async function render(){const rows=chat?await api('/api/chats/'+chat):[];const last=rows.filter(m=>m.result).at(-1);if(last){species=last.result.species;document.querySelectorAll('[data-species]').forEach(b=>b.classList.toggle('selected',b.dataset.species===species));hint();}$('#welcome').hidden=rows.length>0;const list=$('#messages');list.replaceChildren();list.classList.remove('stale');for(const m of rows){const el=node('article','message '+m.role);if(m.role==='assistant')el.append(node('div','assistant-label','✦ VETLENS'));if(m.image){const img=node('img');img.src=m.image;img.alt='Ảnh đã gửi';el.append(img);}el.append(m.result?resultCard(m.result):node('div','text',m.content));list.append(el);}if(rows.length)list.lastElementChild?.scrollIntoView({behavior:'smooth',block:'start'});}
function clearFile(){if(previewURL)URL.revokeObjectURL(previewURL);previewURL=null;$('#file').value='';$('#attachment').hidden=true;$('#preview').removeAttribute('src');}
$('#file').onchange=()=>{const f=$('#file').files[0];if(!f)return;markStale();if(f.size>10*1024*1024){clearFile();status('Ảnh tối đa 10 MB.');return;}if(previewURL)URL.revokeObjectURL(previewURL);previewURL=URL.createObjectURL(f);$('#preview').src=previewURL;$('#filename').textContent=f.name;$('#attachment').hidden=false;status('');};
$('#remove').onclick=clearFile;
$('#species').onclick=e=>{const b=e.target.closest('[data-species]');if(!b||busy)return;markStale();species=b.dataset.species;document.querySelectorAll('[data-species]').forEach(x=>x.classList.toggle('selected',x===b));hint();};
$('#new').onclick=()=>{if(busy)return;chat=null;clearFile();$('#question').value='';$('#messages').replaceChildren();$('#welcome').hidden=false;status('');history().catch(e=>status(e.message));};
$('#composer').onsubmit=async e=>{e.preventDefault();if(busy)return;const text=$('#question').value.trim(),file=$('#file').files[0];if(!text&&!file){status('Chọn ảnh hoặc nhập câu hỏi trước khi gửi.');return;}setBusy(true);status(file?'Đang phân tích ảnh, lần đầu có thể mất vài giây…':'Đang trả lời…');try{if(!chat)chat=(await api('/api/chats',{method:'POST'})).id;if(file){const data=new FormData();data.append('species',species);data.append('file',file);data.append('note',text);await api('/api/chats/'+chat+'/predict',{method:'POST',body:data});}else await api('/api/chats/'+chat+'/message',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});clearFile();$('#question').value='';await render();await history();status('');}catch(e){status(e.message);}finally{setBusy(false);}};
document.querySelectorAll('[data-question]').forEach(b=>b.onclick=()=>{if(busy)return;$('#question').value=b.dataset.question;$('#question').focus();});
history().catch(e=>status('Không kết nối được máy chủ: '+e.message));

function rabiesCard(r){
 const card=node('div','result');card.append(node('div','kicker','SÀNG LỌC NGUY CƠ BỆNH DẠI'),node('h3','',r.name),node('p','warning',r.method));
 const info=node('div','info-grid');for(const [key,title] of [['signs','Cơ sở cảnh báo'],['causes','Thông tin về bệnh dại'],['care','Việc cần làm']])info.append(node('h4','',title),node('p','text',r.info[key]));card.append(info);
 for(const source of r.sources){const link=node('a','source-link',source.name);link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';card.append(link);}return card;
}
const entry=node('button','rabies-entry','Sàng lọc nguy cơ bệnh dại ở chó →');entry.id='rabies-entry';entry.type='button';$('#composer').before(entry);entry.hidden=species!=='dog';
const modal=node('dialog','rabies-dialog');document.body.append(modal);
entry.onclick=async()=>{
 if(busy)return;modal.replaceChildren();
 try{
  const questions=await api('/api/rabies/questions');const form=node('form');
  form.append(node('h2','','Sàng lọc nguy cơ bệnh dại'),node('p','warning','Không cần ảnh. Không đến gần chó nghi dại để chụp ảnh hoặc kiểm tra miệng. Nếu có người bị cắn/cào hay nước bọt tiếp xúc niêm mạc/vết thương, rửa ngay và đến cơ sở y tế; không chờ điền biểu mẫu.'));
  for(const [key,title] of Object.entries(questions)){const label=node('label','rabies-question',title);const select=node('select');select.name=key;select.required=true;for(const [value,text] of [['','Chọn câu trả lời'],['yes','Có'],['no','Không'],['unknown','Không rõ']]){const o=node('option','',text);o.value=value;select.append(o);}label.append(select);form.append(label);}
  const error=node('p','','');error.setAttribute('role','alert');const send=node('button','','Xem hướng dẫn');send.type='submit';const cancel=node('button','','Đóng');cancel.type='button';cancel.onclick=()=>modal.close();form.append(error,send,cancel);
  form.onsubmit=async e=>{e.preventDefault();if(busy)return;const answers=Object.fromEntries(new FormData(form));setBusy(true);error.textContent='Đang lưu kết quả…';try{if(!chat)chat=(await api('/api/chats',{method:'POST'})).id;await api('/api/chats/'+chat+'/rabies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(answers)});modal.close();await render();await history();status('');}catch(e){error.textContent=e.message;}finally{setBusy(false);}};
  modal.append(form);modal.showModal();
 }catch(e){status(e.message);}
};

$('#history-toggle').onclick=()=>{const nav=$('#history');nav.hidden=!nav.hidden;if(!nav.hidden){nav.scrollIntoView({behavior:'smooth',block:'start'});nav.querySelector('button')?.focus();}};

const about=node('details','');about.append(node('summary','','Thông tin mô hình'));const aboutText=node('p','');aboutText.textContent='4 loài · AI thử nghiệm. Chó · Ảnh bệnh da hoặc dấu hiệu miệng/nước dãi. Nhánh miệng còn rất ít dữ liệu và đã bỏ sót ảnh test; không loại trừ dại. Không đến gần chó nghi dại để chụp ảnh.';about.append(aboutText);document.querySelector('.sidebar-bottom').append(about);
