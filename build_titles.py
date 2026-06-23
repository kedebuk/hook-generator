import csv, json, datetime, sys
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
    if not judul: continue
    nama=judul.split('—')[0].split('–')[0].split(':')[0].strip()
    if len(nama)<3: nama=judul[:40]
    rows.append({"code":code,"niche":niche,"nama":nama,"judul":judul,"tagline":tagline,"status":status})
out={"updated":datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),"count":len(rows),"items":rows}
json.dump(out,open('/Users/kantor/hook-generator/titles.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print("wrote",len(rows),"titles (nama OK)")
