import csv, json, datetime, sys, os, re, time, urllib.request, urllib.parse
SKIP_NICHE={"trading"}
rows=[]
try: f=open('/tmp/tom.tsv',encoding='utf-8')
except: sys.exit("no tsv")
for r in csv.reader(f,delimiter='\t'):
    if not r: continue
    code=r[0].strip() if len(r)>0 else ''
    niche=r[1].strip() if len(r)>1 else ''
    judul=r[2].strip() if len(r)>2 else ''
    tagline=r[3].strip() if len(r)>3 else ''
    status=r[5].strip() if len(r)>5 else ''
    lp=r[7].strip() if len(r)>7 else ''            # kolom H = LinkLP
    if not lp.lower().startswith('http'): lp=''
    if not judul: continue
    if niche.lower() in SKIP_NICHE: continue
    nama=judul.split('—')[0].split('–')[0].split(':')[0].strip()
    if len(nama)<3: nama=judul[:40]
    item={"code":code,"niche":niche,"nama":nama,"judul":judul,"tagline":tagline,"status":status}
    if lp: item["lp"]=lp
    rows.append(item)

# ===== FOOTAGE: nama bisnis -> translate TH/VI/MS (BATCH, cached) + flag KHAS INDONESIA =====
# port bisnisPhrase JS ilmuwanlama (ambil produk/jasa dari gaya —/:/- )
_UP2=re.compile(r'\b(3d|ac|ai|umkm|b2b|pc|tv|cctv|hpp|sop|qc|usb|led|apar)\b',re.I)
_JUNK=re.compile(r'\b(stop|gagal|capek|kabur|dikadalin|nyesel|takut|bingung|rugi|boncos|jangan|kenapa|mentok|tumbal|numpuk|tipis|markup|biar|sengaja)\b',re.I)
_SPECIES_OK=re.compile(r'\b(entok|ternak mentok|mentok pedaging)\b',re.I)
def _cl(s):
    s=re.sub(r'[“”"‘’()]','',(s or ''))
    s=re.sub(r'\s+',' ',s).strip().lower()
    s=' '.join(s.split(' ')[:6])
    return _UP2.sub(lambda m:m.group(0).upper(), s)
def _ok(c): return bool(c) and len(c.split(' '))>=2 and (not _JUNK.search(c) or _SPECIES_OK.search(c))
def bisnis_phrase(judul, nama='', niche=''):
    nama=(nama or '').strip(); judul=(judul or ''); niche=(niche or '').lower().strip()
    m=re.match(r'^(bisnis|jasa|usaha|produksi)\s+(.+)',nama,re.I)
    if m: return _cl(m.group(2))
    if re.search(r'[—–]',judul):
        parts=re.split(r'[—–]',judul); seg=(parts[1] if len(parts)>1 else '').split(':')[0]
        if re.search(r'\bjadi\b',seg,re.I): seg=re.split(r'\bjadi\b',seg,flags=re.I)[-1]
        seg=re.sub(r'^\s*(rahasia|cara|stop|sulap|bikin|dari|tukang|jadi|si)\s+','',seg,flags=re.I)
        seg=re.split(r'\s+dengan\s+|\s+untuk\s+|,|\(',seg,flags=re.I)[0]
        c=_cl(seg)
        if _ok(c): return c
    elif ':' in judul and not re.search(r'\s+-\s+',judul):
        after=':'.join(judul.split(':')[1:])
        after=re.split(r'\s+dengan\s+|\s+untuk\s+|\s+pakai\s+|,|\(',after,flags=re.I)[0]
        after=re.sub(r'^\s*(jasa|bisnis|usaha|produksi|produk)\s+','',after,flags=re.I)
        c=_cl(after)
        if _ok(c): return c
    elif re.search(r'\s+-\s+',judul):
        parts=re.split(r'\s+-\s+',judul); after=(parts[1] if len(parts)>1 else '')
        after=re.split(r':|,|\s+yang\s+|\s+untuk\s+|\s+dengan\s+|\s+viral\b|\s+laku\b|\s+modal\b|\s+pasar\b|\s+potensi\b',after,flags=re.I)[0]
        c=_cl(after)
        if _ok(c): return c
    if niche: return niche
    return _cl(judul.split(':')[0].split('—')[0].split('–')[0]) or "bisnis ini"

_AUTH=re.compile(r'\b(pempek|empek|mpek|tekwan|kemplang|gudeg|krecek|nasi liwet|nasi padang|rendang|dendeng|gulai|soto|coto|rawon|gado-?gado|ketoprak|pecel|lotek|karedok|rujak|asinan|lontong|ketupat|opor|semur|sayur asem|oncom|peuyeum|getuk|gethuk|klepon|cenil|serabi|surabi|kue putu|putu ayu|dawet|cendol|es teler|es campur|bakso|mie ayam|mi ayam|batagor|siomay|cireng|cilok|cimol|seblak|basreng|rempeyek|peyek|kerupuk|krupuk|rengginang|opak|jamu|beras kencur|kunyit asam|wedang|bandrek|batik|jumputan|tenun|songket|ulos|wayang|angklung|gamelan|keris|ukiran jepara|anyaman|gerabah|tempe|tahu|gula aren|gula merah|terasi|petis)\b',re.I)
def is_authentic(judul, tagline=''):
    return bool(_AUTH.search((judul or '')+' '+(tagline or '')))

CACHE_F=os.path.join(os.path.dirname(os.path.abspath(__file__)),'footage_tx_cache.json')
try: TX=json.load(open(CACHE_F,encoding='utf-8'))
except Exception: TX={}
_UA={"User-Agent":"Mozilla/5.0 (Macintosh)"}
def _one(p,tl):
    url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=id&tl="+tl+"&dt=t&q="+urllib.parse.quote(p)
    d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers=_UA),timeout=20))
    return "".join(s[0] for s in d[0] if s and s[0])
def _batch(phrases, tl):
    res=[]
    for i in range(0,len(phrases),40):
        chunk=phrases[i:i+40]; lines=[]
        try:
            url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=id&tl="+tl+"&dt=t&q="+urllib.parse.quote("\n".join(chunk))
            d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers=_UA),timeout=25))
            full="".join(seg[0] for seg in d[0] if seg and seg[0]); lines=full.split("\n")
        except Exception:
            lines=[]
        if len(lines)!=len(chunk):
            lines=[]
            for p in chunk:
                try: lines.append(_one(p,tl))
                except Exception: lines.append('')
                time.sleep(0.15)
        res.extend(lines); time.sleep(0.4)
    return res

need={}
for it in rows:
    ph=bisnis_phrase(it['judul'], it.get('nama',''), it.get('niche','')); it['fxkw']=ph
    au=is_authentic(it['judul'], it.get('tagline',''))
    if au: it['auth']=1
    k=ph.lower().strip()
    if k and k not in TX: need[k]=(ph,au)
nak=[k for k,v in need.items() if not v[1]]; na=[need[k][0] for k in nak]
auk=[k for k,v in need.items() if v[1]];     au_=[need[k][0] for k in auk]
if na:
    th=_batch(na,'th'); vi=_batch(na,'vi'); ms=_batch(na,'ms')
    for i,k in enumerate(nak):
        TX[k]={'th':(th[i] if i<len(th) else ''),'vi':(vi[i] if i<len(vi) else ''),'ms':(ms[i] if i<len(ms) else '')}
if au_:
    ms=_batch(au_,'ms')
    for i,k in enumerate(auk):
        TX[k]={'ms':(ms[i] if i<len(ms) else '')}
for it in rows:
    fx=TX.get(it['fxkw'].lower().strip())
    if fx and any(fx.values()): it['fx']={kk:vv for kk,vv in fx.items() if vv}
try: json.dump(TX,open(CACHE_F,'w',encoding='utf-8'),ensure_ascii=False)
except Exception: pass

out={"updated":datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),"count":len(rows),"items":rows}
json.dump(out,open('/Users/kantor/hook-generator/titles.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print("wrote",len(rows),"titles (trading di-skip),",sum(1 for x in rows if x.get('lp')),"punya LP","| fx:",sum(1 for x in rows if x.get('fx')),"auth:",sum(1 for x in rows if x.get('auth')))
