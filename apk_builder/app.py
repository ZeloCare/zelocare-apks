import json, os, re, secrets
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
APP=FastAPI(title='ZeloCare APK Build Control'); TOKEN=os.environ['APK_BUILDER_API_TOKEN']; GH_TOKEN=os.environ['GITHUB_WORKFLOW_TOKEN']; REPO='ZeloCare/zelocare-apks'; REF=re.compile(r'^[A-Za-z0-9._/@-]{1,128}$')
class BuildRequest(BaseModel): app:str='all'; mobile_ref:str=Field('main',max_length=128); volunteer_ref:str=Field('main',max_length=128)
def auth(t):
 if not t or not secrets.compare_digest(t,TOKEN): raise HTTPException(401,'Unauthorized')
def gh(method,path,body=None):
 req=Request('https://api.github.com'+path,method=method,data=json.dumps(body).encode() if body else None,headers={'Authorization':f'Bearer {GH_TOKEN}','Accept':'application/vnd.github+json','Content-Type':'application/json'})
 try:
  with urlopen(req,timeout=15) as r:return json.loads(r.read() or '{}')
 except HTTPError as e: raise HTTPException(502,f'GitHub Actions error: {e.code}')
@APP.get('/health')
def health(): return {'status':'ok','executor':'zelocare-static'}
@APP.post('/v1/builds',status_code=status.HTTP_202_ACCEPTED)
def create(p:BuildRequest,x_apk_builder_token:str|None=Header(default=None)):
 auth(x_apk_builder_token)
 if p.app not in ('all','zelocare-mobile','zelocare-volunteer') or not all(REF.fullmatch(v) for v in(p.mobile_ref,p.volunteer_ref)): raise HTTPException(422,'Invalid build request')
 ident=secrets.token_hex(8); gh('POST',f'/repos/{REPO}/actions/workflows/build-apks.yml/dispatches',{'ref':'main','inputs':{'app':p.app,'mobile_ref':p.mobile_ref,'volunteer_ref':p.volunteer_ref,'request_id':ident}}); return {'id':ident,'status':'queued','executor':'zelocare-static'}
@APP.get('/v1/builds/{ident}')
def get(ident:str,x_apk_builder_token:str|None=Header(default=None)):
 auth(x_apk_builder_token); runs=gh('GET',f'/repos/{REPO}/actions/workflows/build-apks.yml/runs?per_page=50').get('workflow_runs',[]); run=next((x for x in runs if x.get('display_title')==f'APK build {ident}'),None)
 return {'id':ident,'status':'queued'} if not run else {'id':ident,'status':run['status'],'conclusion':run['conclusion'],'url':run['html_url']}
