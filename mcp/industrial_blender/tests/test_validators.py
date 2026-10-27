import json
import struct
from pathlib import Path
from server.validators import validate_terminals,inspect_glb,check_artifacts


def spec(pos=None):
    return {'components':[{'id':'LAMP','expected_terminals':[
        {'id':'LAMP_L1','expected_world_mm':pos},
        {'id':'LAMP_L2','expected_world_mm':[10,0,0]}]}], 'max_position_error_mm':2,'min_terminal_spacing_mm':2}


def snap():
    return {'terminals':[
        {'component_id':'LAMP','terminal_id':'LAMP_L1','world_mm':[0,0,0]},
        {'component_id':'LAMP','terminal_id':'LAMP_L2','world_mm':[10,0,0]}]}


def test_missing_position_is_unresolved():
    r=validate_terminals(snap(),spec(None)); assert r['verdict']=='UNRESOLVED'
    assert '没有实测' in r['unresolved'][0]


def test_all_measured_pass():
    r=validate_terminals(snap(),spec([0,0,0]));assert r['verdict']=='PASS'


def test_position_error_fails():
    data=snap();data['terminals'][0]['world_mm']=[50,0,0]
    assert validate_terminals(data,spec([0,0,0]))['verdict']=='FAIL'


def test_missing_terminal_fails():
    data=snap();data['terminals'].pop()
    assert validate_terminals(data,spec([0,0,0]))['verdict']=='FAIL'


def test_duplicate_terminal_fails():
    data=snap();data['terminals'].append(dict(data['terminals'][0]))
    assert validate_terminals(data,spec([0,0,0]))['verdict']=='FAIL'


def test_wrong_component_fails():
    data=snap();data['terminals'][0]['component_id']='BALLAST'
    assert validate_terminals(data,spec([0,0,0]))['verdict']=='FAIL'


def glb_bytes(with_meshes=True):
    content={'asset':{'version':'2.0'},'nodes':[{'name':'Housing'}],
             'meshes':[{'primitives':[{'attributes':{'POSITION':0}}]}] if with_meshes else []}
    raw=json.dumps(content,separators=(',',':')).encode();raw+=b' ' *((-len(raw))%4)
    return struct.pack('<4sII',b'glTF',2,20+len(raw))+struct.pack('<I4s',len(raw),b'JSON')+raw


def test_glb_valid(tmp_path):
    p=tmp_path/'m.glb';p.write_bytes(glb_bytes());assert inspect_glb(p)['mesh_count']==1


def test_glb_without_mesh_fails(tmp_path):
    p=tmp_path/'m.glb';p.write_bytes(glb_bytes(False))
    try:inspect_glb(p)
    except ValueError:return
    raise AssertionError('empty mesh must fail')


def test_bad_export_fails(tmp_path):
    (tmp_path/'model.glb').write_bytes(b'abc')
    assert check_artifacts(str(tmp_path))['verdict']=='FAIL'


def test_template_remains_unresolved():
    t=Path(__file__).resolve().parents[1]/'examples/terminal_spec.template.json'
    spec=json.loads(t.read_text('utf-8'))
    synthetic={'terminals':[{'terminal_id':x['id'],'component_id':c['id'],'world_mm':[i*10,0,0]}
                  for i,(c,x) in enumerate((c,x) for c in spec['components'] for x in c['expected_terminals'])]}
    assert validate_terminals(synthetic,spec)['verdict']=='UNRESOLVED'
