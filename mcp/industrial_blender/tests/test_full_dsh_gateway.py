import json
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import dsh_gateway as g

class DshCoverage(unittest.TestCase):
    def test_routes_cover_full_engine_surface(self):
        for path in ('/launch','/act','/cmd','/loop','/view','/plan','/headless','/perf','/opt','/worker','/job','/txn','/preset','/lease','/release'):
            self.assertIn(path, g.POST_ROUTES)
        for path in ('/doctor','/health','/status','/commands','/who','/frame.png'):
            self.assertIn(path,g.GET_ROUTES)
    def test_refuse_arbitrary_url_and_route(self):
        with patch.dict('os.environ',{'INDUSTRIAL_DSH_URL':'http://192.0.2.1:9877'}):
            with self.assertRaises(ValueError):g.base_url()
        with self.assertRaises(ValueError):g.request('/notfound',{})
        with self.assertRaises(ValueError):g.request('/../../etc/passwd')
    def test_ndjson_final_wins_over_heartbeat(self):
        self.assertEqual(g.parse_json(b'{}\n{"heartbeat":1}\n{"ok":true,"result":{"count":186}}\n'), {'ok':True,'result':{'count':186}})
    def test_business_failure_not_pass(self):
        with patch.object(g,'request',return_value={'ok':False,'error':'invalid geometry'}):
            a=g.route_call('/plan',{'op':'gate_run','args':{}})
            self.assertEqual(a['transport'],'OK')
            self.assertFalse(a['upstream_ok'])
    def test_upstream_not_included(self):
        state=g.discover_upstream(Path(__file__).resolve().parents[1])
        self.assertIn('source_present',state)
        self.assertIn('repo',state)
    def test_image_signature_validation(self):
        with patch.object(g.urllib.request,'urlopen') as call:
            class Response:
                headers={'content-type':'image/png'}
                def __enter__(self):return self
                def __exit__(self,*a):pass
                def __init__(self):self.done=False
                def read(self,n):
                    if self.done:return b''
                    self.done=True
                    return b'\x89PNG\r\n\x1a\n' + b'fake payload'
            call.return_value=Response()
            self.assertTrue(g.request('/frame.png',query={'size':500},binary=True).startswith(b'\x89PNG'))
    def test_unknown_result_is_not_success(self):
        with patch.object(g,'request',side_effect=g.DshUnavailable('not ready')):
            x=g.route_call('/act',{'code':'print(1)'})
            self.assertEqual(x['transport'],'UNRESOLVED')
    def test_get_json(self):
        with patch.object(g.urllib.request,'urlopen') as call:
            class R:
                headers={'content-type':'application/json'}
                def __enter__(self):return self
                def __exit__(self,*a):pass
                def __init__(self):self.done=False
                def read(self,n):
                    if self.done:return b''
                    self.done=True
                    return b'{"kind":"ok"}'
            call.return_value=R()
            self.assertEqual(g.request('/doctor',timeout=3), {'kind':'ok'})

if __name__=='__main__':unittest.main()
