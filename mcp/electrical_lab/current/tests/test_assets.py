import copy
import unittest
from asset_tools import (new_asset_spec, validate_asset_spec, plan_render_pipeline,
                         generate_svg_asset, simulate_motion_step, ASSET_SOURCES)
from mcp_server import TOOLS, execute, handle

class TestIndustrialAssets(unittest.TestCase):
    def setUp(self):
        self.spec=new_asset_spec('非标气动搬运机构', drawings=['owner:photo_front.jpg'])
        self.spec['asset_id']='school.pneumatic.fixture_01'

    def test_spec_has_no_fabricated_terminals(self):
        self.assertEqual(self.spec['terminals'], [])
        self.assertFalse(self.spec['source']['verified_against_manual'])
    def test_validate_draft(self):
        result=validate_asset_spec(self.spec)
        self.assertTrue(result['ok'])
        self.assertTrue(any('未测量' in w for w in result['warnings']))
    def test_manufacturer_stage_requires_evidence(self):
        a=copy.deepcopy(self.spec)
        a['stage']='manufacturer_reviewed'
        self.assertFalse(validate_asset_spec(a)['ok'])
    def test_duplicate_pins(self):
        a=copy.deepcopy(self.spec)
        a['terminals']=[{'label':'A1'},{'label':'A1'}]
        self.assertFalse(validate_asset_spec(a)['ok'])
    def test_real_device_write_rejected(self):
        a=copy.deepcopy(self.spec)
        a['control']['real_device_connection']=True
        self.assertFalse(validate_asset_spec(a)['ok'])
    def test_rights_warning(self):
        result=validate_asset_spec(self.spec)
        self.assertTrue(any('许可' in w for w in result['warnings']))
    def test_svg_is_safe_and_marked(self):
        a=copy.deepcopy(self.spec);a['name']='<script>alert(1)</script>'
        svg=generate_svg_asset(a)['svg']
        self.assertIn('&lt;script&gt;',svg)
        self.assertNotIn('<script>',svg)
        self.assertIn('未按实物校验',svg)
    def test_svg_has_terminal_labels(self):
        a=copy.deepcopy(self.spec)
        a['terminals']=[{'label':'A1'},{'label':'A2'}]
        self.assertIn('A1',generate_svg_asset(a)['svg'])
    def test_render_cpu_gpu_split(self):
        strategy=plan_render_pipeline(self.spec, 'classroom_low_end')
        self.assertEqual(strategy['mode'],'2d_svg')
        self.assertEqual(plan_render_pipeline(self.spec, need_3d=True)['mode'],'3d_webgl')
    def test_motion_linear(self):
        motion={'type':'linear','min_position':0,'max_position':100,'max_speed_per_s':20,'units':'mm'}
        val=simulate_motion_step(motion,95,'extend',500)
        self.assertEqual(val['position'],100)
        val=simulate_motion_step(motion,95,'retract',500)
        self.assertEqual(val['position'],85)
    def test_motion_bad_values(self):
        with self.assertRaises(ValueError):
            simulate_motion_step({'type':'linear','min_position':0,'max_position':50,'max_speed_per_s':10},0,'extend',501)
    def test_mcp_tool_count_and_call(self):
        self.assertEqual(len(TOOLS),17)
        self.assertGreaterEqual(len(execute('list_asset_sources',{})),4)
        request={'jsonrpc':'2.0','method':'tools/call','params':{'name':'plan_render_pipeline','arguments':{'spec':self.spec}},'id':5}
        result=handle(request)
        self.assertFalse(result['result']['isError'])
    def test_existing_device_catalog_preserved(self):
        self.assertIn('items',execute('search_industrial_devices',{'query':'西门子'}))

if __name__=='__main__':unittest.main()
