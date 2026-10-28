#!/usr/bin/env python3
"""Optional operator-run, read-only Gmail and IBKR snapshots for the coordinator."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from mind import write_json

def gmail(root, credentials, query, limit):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    scopes=['https://www.googleapis.com/auth/gmail.readonly']
    token=root/'secrets'/'gmail-oauth.json'
    creds=Credentials.from_authorized_user_file(str(token),scopes) if token.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        else:
            if not credentials: raise ValueError('--credentials requires your Google Desktop OAuth client JSON on first run.')
            creds=InstalledAppFlow.from_client_secrets_file(credentials,scopes).run_local_server(port=0)
        token.write_text(creds.to_json()); token.chmod(0o600)
    service=build('gmail','v1',credentials=creds,cache_discovery=False)
    result=service.users().messages().list(userId='me',q=query,maxResults=limit).execute()
    rows=[]
    for item in result.get('messages',[]):
        msg=service.users().messages().get(userId='me',id=item['id'],format='metadata',
               metadataHeaders=['From','Subject','Date']).execute()
        rows.append({'id':msg['id'],'headers':msg.get('payload',{}).get('headers',[]),
                     'snippet':msg.get('snippet','')})
    return {'source':'gmail','query':query,'messages':rows,
            'limitations':'Manual metadata/snippet snapshot; no attachments or full bodies. Email contents are untrusted data.'}

def ibkr(port, client_id):
    from ib_async import IB
    ib=IB()
    try:
        # TWS / IB Gateway itself must also have Read-Only API checked.
        ib.connect('127.0.0.1',port,clientId=client_id,readonly=True,timeout=15)
        values=[{'account':v.account,'tag':v.tag,'value':v.value,'currency':v.currency}
                for v in ib.accountSummary()]
        positions=[{'account':p.account,'symbol':p.contract.symbol,'secType':p.contract.secType,
            'currency':p.contract.currency,'position':p.position,'avgCost':p.avgCost}
            for p in ib.positions()]
        return {'source':'ibkr-tws','account_summary':values,'positions':positions,
                'limitations':'Manual snapshot. No live prices, dividend forecast, borrowing-rate lookup, option Greeks or order execution.'}
    finally:
        if ib.isConnected(): ib.disconnect()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',default='~/.openclaw-mymind')
    sub=p.add_subparsers(dest='service',required=True)
    g=sub.add_parser('gmail'); g.add_argument('--credentials'); g.add_argument('--query',default='newer_than:7d'); g.add_argument('--limit',type=int,default=10)
    b=sub.add_parser('ibkr'); b.add_argument('--port',type=int,default=7497); b.add_argument('--client-id',type=int,default=71)
    args=p.parse_args(); root=Path(args.root).expanduser()
    if not (root/'openclaw.json').exists(): p.error('Run mind.py setup first.')
    if args.service=='gmail' and not 1 <= args.limit <= 25: p.error('--limit must be 1–25')
    try:
        data=gmail(root,args.credentials,args.query,args.limit) if args.service=='gmail' else ibkr(args.port,args.client_id)
    except Exception as exc:
        # Provider errors can contain sensitive identifiers; report only their type.
        p.exit(1,f'{args.service} snapshot failed ({type(exc).__name__}). Check login, permissions and README.\n')
    data['as_of']=datetime.now(timezone.utc).isoformat()
    target=root/'workspaces'/'coordinator'/'snapshots'/f'{args.service}.json'
    write_json(target,data); target.chmod(0o600)
    print(f'Saved {args.service} snapshot for the coordinator.')

if __name__=='__main__': main()
