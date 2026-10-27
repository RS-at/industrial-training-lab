import unittest
from industrial_catalog import DEVICES,search_devices,get_device,scaffold_lab,validate_signal_links,validate_hmi_tags,list_categories

class CatalogTests(unittest.TestCase):
    def test_required_devices(self):
        required=['robot.abb','robot.kuka','plc.siemens.s7_1200','plc.siemens.s7_1500','plc.inovance.h3u','hmi.mcgs.touch','motion.servo_drive','motion.stepper_driver','low.mcb_1pn','pneu.valve_5_2']
        for k in required:self.assertIn(k,DEVICES)
    def test_scopes(self):
        self.assertEqual(get_device('robot.abb')['implementation_status'],'catalog_only')
        self.assertEqual(get_device('low.fluorescent')['implementation_status'],'teaching_logic_simulation')
    def test_search_and_categories(self):
        self.assertTrue(search_devices('西门子')['count']>1)
        self.assertGreaterEqual(len(list_categories()),8)
    def test_scaffold_cannot_claim_simulator(self):
        obj=scaffold_lab('PLC+HMI示意',['plc.siemens.s7_1200','hmi.mcgs.touch'])
        self.assertEqual(obj['development_status'],'spec_only_not_simulated')
        self.assertFalse(obj['devices'][0]['pinout_verified'])
    def test_unknown_scaffold_id(self):
        self.assertIn('error',scaffold_lab('example',['no.such.device']))
    def test_abstract_links_ok(self):
        devices=[{'id':'plc','ports':{'Q0':{'direction':'out','kind':'digital','voltage':'24VDC'}}},{'id':'lamp','ports':{'IN':{'direction':'in','kind':'digital','voltage':'24VDC'}}}]
        links=[{'from_device':'plc','from_port':'Q0','to_device':'lamp','to_port':'IN'}]
        self.assertTrue(validate_signal_links(devices,links)['valid'])
    def test_abstract_links_mismatch(self):
        devices=[{'id':'plc','ports':{'Q0':{'direction':'out','kind':'digital','voltage':'24VDC'}}},{'id':'dev','ports':{'IN':{'direction':'in','kind':'analog','voltage':'220VAC'}}}]
        links=[{'from_device':'plc','from_port':'Q0','to_device':'dev','to_port':'IN'}]
        self.assertFalse(validate_signal_links(devices,links)['valid'])
    def test_hmi_tags(self):
        self.assertTrue(validate_hmi_tags([{'name':'Start','type':'bool'}],[{'name':'StartButton','plc_tag':'Start','type':'bool'}])['valid'])
        self.assertFalse(validate_hmi_tags([{'name':'Start','type':'bool'}],[{'name':'StartButton','plc_tag':'Start','type':'int'}])['valid'])

if __name__=='__main__':unittest.main()
