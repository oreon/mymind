#!/usr/bin/env python3
"""Model-free owner-only Telegram check-ins. No inbound polling; OpenClaw owns replies."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from mind import write_json

def due(now, settings, delivery):
    if not settings.get('enabled'): return False
    interval=int(settings['interval_minutes'])
    if not 5 <= interval <= 1440: raise ValueError('interval_minutes must be 5–1440')
    local=now.astimezone(ZoneInfo(settings['timezone']))
    start=datetime.strptime(settings['start'],'%H:%M').time()
    end=datetime.strptime(settings['end'],'%H:%M').time()
    current=local.time().replace(tzinfo=None)
    active=(start <= current < end) if start < end else (current >= start or current < end)
    if start == end or not active: return False
    snooze=settings.get('snooze_until')
    if snooze:
        until=datetime.fromisoformat(snooze.replace('Z','+00:00'))
        if until.tzinfo is None: raise ValueError('snooze_until must include timezone')
        if now < until: return False
    day=local.date().isoformat()
    count=delivery.get('count',0) if delivery.get('day') == day else 0
    if count >= int(settings['max_per_day']): return False
    slot=int(now.timestamp()) // (interval*60)
    # Also avoid a burst if the interval is changed during the current period.
    last=delivery.get('attempted_at',0)
    return delivery.get('slot') != slot and now.timestamp()-last >= interval*60-1

def message(workspace):
    progress=json.loads((workspace/'progress.json').read_text())
    task=next((t for t in progress.get('tasks',[]) if t.get('status') in ('doing','todo')),None)
    text='Quick check-in: what are you doing now, and is it how you want to spend this half hour?'
    if task:
        text += f"\n\nOne possible next step [{task['id']}]: {task['title']}"
    return text+'\n\nReply naturally, or say “done TASK-ID”, “change”, “snooze two hours”, or “pause reminders”.'

def tick(root, now=None, dry_run=False, sender=None):
    now=now or datetime.now(timezone.utc)
    root=Path(root)
    config=json.loads((root/'reminder-settings.json').read_text())
    workspace=Path(config['workspace'])
    settings=json.loads((workspace/'checkins.json').read_text())
    runtime=root/'reminder-delivery.json'
    state=json.loads(runtime.read_text()) if runtime.exists() else {}
    if not due(now,settings,state): return 'quiet'
    text=message(workspace)
    if dry_run: return text
    local=now.astimezone(ZoneInfo(settings['timezone']))
    day=local.date().isoformat()
    count=state.get('count',0) if state.get('day') == day else 0
    # Persist attempt before sending: a timeout may still have delivered the message.
    # No automatic retry of an uncertain send; restart never generates catch-up spam.
    state={'day':day,'count':count+1,'slot':int(now.timestamp())//(int(settings['interval_minutes'])*60),
           'attempted_at':now.timestamp(),'status':'attempted'}
    write_json(runtime,state)
    try:
        if sender: sender(text)
        else:
            token=(root/'secrets'/'telegram-token').read_text().strip()
            data=json.dumps({'chat_id':config['chat_id'],'text':text}).encode()
            request=Request(f'https://api.telegram.org/bot{token}/sendMessage',data=data,
                            headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=20) as response:
                result=json.load(response)
            if not result.get('ok'): raise RuntimeError('Telegram rejected the message')
        state['status']='sent'
    except Exception:
        # Never print exceptions containing the token-bearing Telegram URL.
        state['status']='failed-or-uncertain'
    write_json(runtime,state)
    return state['status']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',default='~/.openclaw-mymind')
    p.add_argument('--once',action='store_true'); p.add_argument('--dry-run',action='store_true')
    args=p.parse_args(); root=Path(args.root).expanduser()
    with (root/'reminder-worker.lock').open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: p.error('A reminder worker is already running.')
        while True:
            try: print(tick(root,dry_run=args.dry_run),flush=True)
            except Exception: print('Check-in skipped: invalid or unavailable local settings. See README.',flush=True)
            if args.once or args.dry_run: break
            time.sleep(20)

if __name__ == '__main__': main()
