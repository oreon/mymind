from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import tempfile
import unittest
import mind
import reminders

class MindTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'profile'
        self.config=mind.provision(self.root,'google/test-model','123456','123456:TEST_ONLY')
        self.workspace=self.root/'workspaces'/'coordinator'
        # November 1 follows the Atlantic clock change, useful for timezone tests.
        self.now=datetime(2026,11,2,13,0,tzinfo=timezone.utc)
    def tearDown(self): self.temp.cleanup()
    def test_nested_routes_and_boundaries(self):
        entries=self.config['agents']['entries']
        for route in [('coordinator','health','meditation','breath'),
                      ('coordinator','career','studio','marketing')]:
            for parent,child in zip(route,route[1:]):
                self.assertIn(child,entries[parent]['subagents']['allowAgents'])
        for aid,entry in entries.items():
            self.assertTrue(set(entry['subagents']['allowAgents']) <= entries.keys())
            for dangerous in ['exec','message','browser','nodes','cron']:
                self.assertNotIn(dangerous,entry['tools']['allow'])
            self.assertEqual('write' in entry['tools']['allow'],aid=='coordinator')
    def test_setup_refuses_overwrite(self):
        before=(self.root/'openclaw.json').read_bytes()
        with self.assertRaises(FileExistsError):
            mind.provision(self.root,'google/test','123456')
        self.assertEqual(before,(self.root/'openclaw.json').read_bytes())
    def test_sends_once_and_survives_restart(self):
        sent=[]
        self.assertEqual(reminders.tick(self.root,self.now,sender=sent.append),'sent')
        self.assertEqual(reminders.tick(self.root,self.now+timedelta(minutes=2),sender=sent.append),'quiet')
        self.assertEqual(reminders.tick(self.root,self.now+timedelta(minutes=30),sender=sent.append),'sent')
        self.assertEqual(len(sent),2)
    def test_no_retry_after_uncertain_send(self):
        def fail(text): raise TimeoutError('redacted')
        self.assertEqual(reminders.tick(self.root,self.now,sender=fail),'failed-or-uncertain')
        sent=[]
        self.assertEqual(reminders.tick(self.root,self.now,sender=sent.append),'quiet')
        self.assertFalse(sent)
    def test_pause_snooze_quiet_hours_and_daily_cap(self):
        s=json.loads((self.workspace/'checkins.json').read_text())
        s['enabled']=False
        self.assertFalse(reminders.due(self.now,s,{}))
        s['enabled']=True; s['snooze_until']=(self.now+timedelta(hours=2)).isoformat()
        self.assertFalse(reminders.due(self.now,s,{}))
        s['snooze_until']=None
        self.assertFalse(reminders.due(self.now.replace(hour=3),s,{}))
        self.assertTrue(reminders.due(self.now,s,{}))
        self.assertFalse(reminders.due(self.now,s,{'day':'2026-11-02','count':24}))
        self.assertTrue(reminders.due(self.now,s,{'day':'2026-11-01','count':24}))
    def test_dst_wall_clock_window(self):
        s=json.loads((self.workspace/'checkins.json').read_text())
        # 08:00 Atlantic changes from 11 UTC to 12 UTC on November 1.
        self.assertTrue(reminders.due(datetime(2026,10,31,11,tzinfo=timezone.utc),s,{}))
        self.assertFalse(reminders.due(datetime(2026,11,1,11,tzinfo=timezone.utc),s,{}))
        self.assertTrue(reminders.due(datetime(2026,11,1,12,tzinfo=timezone.utc),s,{}))
    def test_dry_run_no_delivery_state(self):
        preview=reminders.tick(self.root,self.now,dry_run=True)
        self.assertIn('studio-001',preview)
        self.assertFalse((self.root/'reminder-delivery.json').exists())
    def test_malformed_snooze_fails_closed(self):
        s=json.loads((self.workspace/'checkins.json').read_text())
        s['snooze_until']='2026-11-02T15:00:00'
        with self.assertRaises(ValueError): reminders.due(self.now,s,{})
    def test_completed_tasks_not_reminded(self):
        mind.write_json(self.workspace/'progress.json',{'tasks':[{'id':'done-1','status':'done','title':'Finished'}]})
        self.assertNotIn('Finished',reminders.message(self.workspace))

if __name__=='__main__': unittest.main()
