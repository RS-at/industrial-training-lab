import json, sys, pathlib, unittest, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from electrical_core import BASE, validate_wiring, simulate_lamp

class CoreTest(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(validate_wiring(BASE)["valid"])
    def test_reverse_symmetries(self):
        w=[list(pair) for pair in BASE]
        w[0][1]="switch.2"; w[1][0]="switch.1"
        self.assertTrue(validate_wiring(w)["valid"])
    def test_missing(self):
        self.assertFalse(validate_wiring(BASE[:-1])["valid"])
    def test_short(self):
        self.assertEqual(validate_wiring(BASE+[["source.L","source.N"]])["status"],"danger")
    def test_excess(self):
        self.assertFalse(validate_wiring(BASE+[["source.N","starter.1"]])["valid"])
    def test_reject_untrusted_terminal(self):
        self.assertFalse(validate_wiring([["foo","source.N"]])["valid"])
    def test_simulate(self):
        self.assertTrue(simulate_lamp(BASE)["lit"])
        self.assertFalse(simulate_lamp(BASE, fault="starter_stuck_closed")["lit"])
        self.assertEqual(simulate_lamp(BASE[:-1])["status"],"blocked")
    def test_mcp(self):
        p=subprocess.run([sys.executable,"mcp_server.py"],input='\n'.join([
            json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26"}}),
            json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}),
            json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/list"}),
            json.dumps({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"validate_wiring","arguments":{"wires":BASE}}})
        ])+'\n',capture_output=True,text=True,cwd=str(pathlib.Path(__file__).resolve().parents[1]),timeout=6)
        self.assertEqual(p.returncode,0,p.stderr)
        rs=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(len(rs),3)
        self.assertGreaterEqual(len(rs[1]["result"]["tools"]),4)
        self.assertTrue(json.loads(rs[2]["result"]["content"][0]["text"])["valid"])

if __name__=="__main__": unittest.main()
