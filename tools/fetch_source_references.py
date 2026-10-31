"""Read public upstream references and licenses; no downloaded code is executed."""
import base64,json,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research'
OUT.mkdir(exist_ok=True)
references=[('measureer/ROGDeltaTray','docs/protocol.md'),('measureer/ROGDeltaTray','LICENSE'),
            ('Dabouben/dsh-daily-tasks','src/usage.ts'),('Dabouben/dsh-daily-tasks','LICENSE'),
            ('NeutronStar714/dsh-budget-watcher','README.md'),('NeutronStar714/dsh-budget-watcher','LICENSE')]
index=[]
for repo,path in references:
    url=f'https://api.github.com/repos/{repo}/contents/{path}'
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'JingliuPet-local-reference-review','Accept':'application/vnd.github+json'})
        with urllib.request.urlopen(req,timeout=20) as response:
            data=json.load(response)
        content=base64.b64decode(data['content'])
        target=OUT/repo.replace('/','__')/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
        index.append(dict(repo=repo,path=path,sha=data['sha'],url=data['html_url']))
        print(repo,path,len(content),'bytes',flush=True)
    except Exception as error:
        print(repo,path,type(error).__name__,str(error)[:120],flush=True)
(OUT/'references.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
