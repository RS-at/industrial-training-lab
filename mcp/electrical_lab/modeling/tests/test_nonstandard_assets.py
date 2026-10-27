import copy
import json
import unittest
from nonstandard_assets import (TEMPLATE, list_material_sources, intake_checklist, new_asset_template, validate_asset_manifest, render_asset_svg)
from mcp_server import execute, TOOLS, handle

class MaterialWorkflowTests(unittest.TestCase):
    def test_sources_are_reference_links_only(self):
        r=list_material_sources('3d');self.assertGreaterEqual(r['count'],1)
        self.assertTrue(all(x['auto_download'] is False for x in r['sources']))
    def test_intake_private_default(self):
        c=intake_checklist();self.assertEqual(c['visibility'],'private')
        self.assertGreaterEqual(len(c['minimum_materials']),4)
    def test_new_asset_has_no_verified_ports(self):
        d=new_asset_template('machine_001','分拣台')
        self.assertEqual(d['ports'],[])
        self.assertEqual(d['visibility'],'private')
        self.assertEqual(d['verification']['terminals'],'unverified')
    def test_reject_unsafe_ids_dimensions(self):
        self.assertIn('error',new_asset_template('../foo','设备'))
        self.assertIn('error',new_asset_template('machine_22','设备',width_mm=-1))
    def test_template_visual_only(self):
        d=copy.deepcopy(TEMPLATE)
        r=validate_asset_manifest(d);self.assertTrue(r['valid'])
        self.assertTrue(r['capabilities']['illustrative_svg'])
        self.assertFalse(r['capabilities']['terminal_training'])
        self.assertFalse(r['capabilities']['public_distribution'])
        self.assertFalse(r['capabilities']['behavior_simulation'])
    def test_duplicate_port_rejected(self):
        d=copy.deepcopy(TEMPLATE);d['ports'].append(copy.deepcopy(d['ports'][0]))
        self.assertFalse(validate_asset_manifest(d)['valid'])
    def test_verified_requires_source(self):
        d=copy.deepcopy(TEMPLATE);d['ports'][0]['verified']=True
        self.assertFalse(validate_asset_manifest(d)['valid'])
    def test_public_requires_evidence(self):
        d=copy.deepcopy(TEMPLATE);d['visibility']='public';d['rights']['can_redistribute']=True
        self.assertFalse(validate_asset_manifest(d)['valid'])
    def test_svg_escapes_untrusted_labels(self):
        d=copy.deepcopy(TEMPLATE);d['display_name']='<script>alert(1)</script>'
        r=render_asset_svg(d)
        self.assertIn('&lt;script&gt;',r['svg'])
        self.assertNotIn('<script>',r['svg'])
        self.assertIn('非现场接线依据',r['svg'])
    def test_svg_contains_unverified_terminal_flag(self):
        svg=render_asset_svg(copy.deepcopy(TEMPLATE))['svg']
        self.assertIn('待核实',svg)
    def test_missing_geometry_rejected(self):
        d=copy.deepcopy(TEMPLATE);d['geometry']=None
        self.assertFalse(validate_asset_manifest(d)['valid'])
    def test_mcp_new_tools_listed(self):
        names={t['name'] for t in TOOLS}
        self.assertEqual(len(TOOLS),len(names))
        for n in ('list_material_sources','get_asset_intake_checklist','new_nonstandard_asset','validate_asset_manifest','render_nonstandard_svg'):
            self.assertIn(n,names)
        self.assertEqual(len(TOOLS),16)
    def test_mcp_roundtrip(self):
        d=execute('new_nonstandard_asset',{'asset_id':'machine_777','display_name':'测试机'})
        res=execute('validate_asset_manifest',{'manifest':d})
        self.assertTrue(res['valid'])
        out=handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'render_nonstandard_svg','arguments':{'manifest':d}}})
        self.assertFalse(out['result']['isError'])
    def test_no_machine_ready_from_exaggerated_flag_only(self):
        d=copy.deepcopy(TEMPLATE);d['verification']['terminals']='manufacturer_document_verified'
        self.assertFalse(validate_asset_manifest(d)['capabilities']['terminal_training'])

if __name__=='__main__':unittest.main()
