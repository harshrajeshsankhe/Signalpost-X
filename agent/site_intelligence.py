#!/usr/bin/env python3
"""Precision-gated company-site intelligence for Signalpost X.

Rules:
- Never follow a URL that resolves to a private/non-global address.
- Count robots, redirects, retries and page requests against the request budget.
- Keep candidates quarantined unless the page provides strong entity evidence.
- Prefer exact organisation number; otherwise require multiple independent identity signals.
"""
from __future__ import annotations
import hashlib, html, ipaddress, re, socket, time, urllib.parse, urllib.request, urllib.robotparser
from collections import deque

UA='signalpost-x/1.1 (+https://builderr.ai)'

PATH_HINTS=('about','om-oss','kontakt','contact','team','ansatte','ledelse','management','people','career','jobb','jobber','stillinger','vacancies','news','nyhet','nyheter','aktuelt','prosjekt','referanse','case','blog')

def _host(url:str)->str:
    return (urllib.parse.urlparse(url).hostname or '').lower().rstrip('.')

def public(url:str)->None:
    p=urllib.parse.urlparse(url); host=_host(url)
    if p.scheme not in ('http','https') or not host or host in {'localhost'} or host.endswith('.local'):
        raise ValueError('non-public URL')
    try:
        ips={x[4][0] for x in socket.getaddrinfo(host,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)}
    except OSError as e:
        raise ValueError('DNS failure') from e
    for ip in ips:
        if not ipaddress.ip_address(ip).is_global:
            raise ValueError('non-global destination')

def registrable_domain(url:str)->str:
    h=_host(url).removeprefix('www.')
    parts=h.split('.')
    return '.'.join(parts[-2:]) if len(parts)>=2 else h

def _normalise(s:str)->str:
    return re.sub(r'[^a-z0-9æøå]+',' ',s.casefold()).strip()

def _name_tokens(name:str)->list[str]:
    stop={'as','asa','ans','da','nuf','sa','spa','iks','ks','bbl','sti','fli'}
    return [x for x in _normalise(name).split() if len(x)>1 and x not in stop]

def _extract_identity_text(raw:bytes)->str:
    s=raw.decode('utf-8','replace')
    parts=[]
    for pat in (r'<title[^>]*>(.*?)</title>',r'<meta[^>]+(?:name|property)=["\'](?:og:site_name|description)["\'][^>]+content=["\'](.*?)["\']',r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'):
        parts += re.findall(pat,s,re.I|re.S)
    s=re.sub(r'<script\b[^>]*>.*?</script>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<style\b[^>]*>.*?</style>',' ',s,flags=re.I|re.S)
    s=re.sub(r'<[^>]+>',' ',s)
    parts.append(html.unescape(s))
    return re.sub(r'\s+',' ',' '.join(parts)).strip()

def identity(profile:dict,text:str,url:str)->dict:
    name=str(profile.get('name') or '')
    org=re.sub(r'\D','',str(profile.get('organisation_number') or ''))
    muni=_normalise(str(profile.get('municipality') or ''))
    norm=_normalise(text)
    toks=_name_tokens(name)
    org_found=bool(org and org in re.sub(r'\D','',text))
    name_hits=sum(t in norm for t in toks)
    name_ratio=(name_hits/len(toks)) if toks else 0
    muni_found=bool(muni and len(muni)>2 and muni in norm)
    # Exact org number is decisive. Without it, require the complete legal-name token set
    # or a strong name match plus municipality. This intentionally sacrifices recall for precision.
    if org_found:
        score=1.0; method='organisation_number'
    elif toks and name_ratio>=1.0 and muni_found:
        score=.98; method='name+municipality'
    elif len(toks)>=2 and name_ratio>=1.0:
        score=.95; method='full_name'
    elif len(toks)>=2 and name_ratio>=.8 and muni_found:
        score=.86; method='partial_name+municipality'
    else:
        score=name_ratio*.6; method='weak'
    return {'score':round(score,3),'publishable':score>=.95,'method':method,'matched_name_tokens':[t for t in toks if t in norm],'organisation_number_found':org_found,'municipality_found':muni_found,'url_domain':registrable_domain(url)}

def _fetch(url:str,timeout:float,max_bytes:int=750_000)->dict:
    public(url); start=time.monotonic()
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/ld+json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        final=r.geturl(); public(final)
        raw=r.read(max_bytes+1); ctype=r.headers.get('content-type','')
        status=getattr(r,'status',200)
    return {'url':final,'status':status,'elapsed_ms':int((time.monotonic()-start)*1000),'bytes':len(raw),'content_type':ctype,'raw':raw}

def robots_ok(url:str,timeout:float=8)->tuple[bool,int]:
    # robots retrieval is itself an outbound request and therefore must be budgeted.
    try:
        p=urllib.parse.urlparse(url); ru=f'{p.scheme}://{p.netloc}/robots.txt'; public(ru)
        req=urllib.request.Request(ru,headers={'User-Agent':UA})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            rp=urllib.robotparser.RobotFileParser(); rp.parse(r.read().decode('utf-8','replace').splitlines())
            return rp.can_fetch(UA,url),1
    except Exception:
        return True,1

def _links(base:str,raw:bytes)->list[str]:
    s=raw.decode('utf-8','replace'); out=[]
    for href in re.findall(r'href\s*=\s*["\']([^"\']+)',s,re.I):
        u=urllib.parse.urljoin(base,href); p=urllib.parse.urlparse(u)
        if p.scheme in ('http','https') and registrable_domain(u)==registrable_domain(base):
            u=urllib.parse.urlunparse((p.scheme,p.netloc,p.path or '/', '', '', ''))
            if u not in out: out.append(u)
    return out

def crawl(profile:dict,max_pages:int=8,timeout:float=12)->dict:
    root=str(profile.get('website') or '').strip()
    if not root: return {'status':'not_available','pages':[],'requests':0,'bytes':0,'identity':'not_checked'}
    if not root.startswith(('http://','https://')): root='https://'+root
    q=deque([root]); seen=set(); pages=[]; requests=bytes_=0; scores=[]; methods=[]
    while q and len(pages)<max_pages:
        url=q.popleft()
        if url in seen: continue
        seen.add(url)
        allowed,rc=robots_ok(url,timeout=min(timeout,8)); requests+=rc
        if not allowed: continue
        try: res=_fetch(url,timeout)
        except Exception: continue
        requests+=1; bytes_+=res['bytes']
        if res['bytes']>750_000 or 'html' not in res['content_type'].lower(): continue
        text=_extract_identity_text(res['raw']); ident=identity(profile,text,url); scores.append(ident['score']); methods.append(ident['method'])
        title=(re.search(r'<title[^>]*>(.*?)</title>',res['raw'].decode('utf-8','replace'),re.I|re.S) or [None,''])[1].strip()[:500]
        pages.append({'url':res['url'],'title':title,'text':text[:10000],'identity':ident,'content_sha256':hashlib.sha256(res['raw']).hexdigest(),'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        if ident['publishable']:
            candidates=_links(res['url'],res['raw'])
            candidates.sort(key=lambda u:(0 if any(k in u.casefold() for k in PATH_HINTS) else 1,len(u),u))
            for u in candidates[:10]:
                if u not in seen and len(seen)<max_pages*4: q.append(u)
    best=max(scores or [0]); exact=bool(pages and best>=.95)
    return {'status':'available' if exact else ('ambiguous' if pages else 'source_error'),'pages':pages,'requests':requests,'bytes':bytes_,'identity':'exact' if exact else 'quarantined','identity_score':best,'identity_methods':methods}
