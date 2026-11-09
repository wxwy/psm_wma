"""Own emitted instances; matching code is not private-scene acceptance."""
from pathlib import Path

import numpy as np
import pytest

from g2.io import ContractError, digest, read_json, write_json
from g2.sim.asset_inventory import inventory
from g2.sim.role_hypotheses import generate
from g2.sim.source_geometry import load_model, model_source_hash


def rebuild(case, text=None):
    if text is not None:
        case['xml'].write_text(text)
    _, sources = load_model(case['xml'])
    write_json(case['metadata'], {'schema': 'g2_sim_prescan_v1', 'scene_id': 'TEST_ONLY_ROLE_EMISSION', 'geoms': {},
        'state_source': {'model_source_sha256': model_source_hash(sources), 'states_sha256': digest(case['states'])}})
    case['paths'] = []
    index = len(list(case['root'].glob('audit*')))
    for frame in (0, 200):
        out = case['root'] / ('audit%d_%d' % (index, frame))
        inventory(case['xml'], out, metadata=case['metadata'], ep_meta=case['ep_meta'], states=case['states'], frame=frame)
        case['paths'].append(out / 'inventory.json')


@pytest.fixture
def emitted(tmp_path):
    source = tmp_path / 'own_source'; source.mkdir()
    xml = source / 'model.xml'
    xml.write_text('''<mujoco><asset><material name="counter_counter_top" rgba=".3 .6 .9 1"/>
      <texture name="background" type="2d" builtin="checker" width="4" height="4" rgb1="1 0 0" rgb2="0 1 0"/>
      <material name="window_mat" texture="background" texuniform="true" texrepeat="1 1"/></asset><worldbody>
      <body name="counter_main"><joint type="slide" axis="1 0 0"/>
        <geom name="counter_top_visual" type="box" size=".5 .3 .015" pos="0 0 .485" group="1" material="counter_counter_top" mass="1e-8" contype="0" conaffinity="0"/>
        <geom name="counter_top_0" type="box" size=".25 .3 .015" pos="-.25 0 .485" group="0" rgba=".2 .3 .4 .5" density="10"/>
        <geom name="counter_top_1" type="box" size=".25 .3 .015" pos=".25 0 .485" group="0" rgba=".2 .3 .4 .5" density="10"/>
        <geom name="counter_reg_main" type="box" size=".5 .3 .5" group="1" rgba="0 1 0 0" mass="1e-8" contype="0" conaffinity="0"/>
        <geom name="counter_handle_collision" type="cylinder" size=".01 .1" pos="0 .4 0" group="0" rgba=".5 0 0 .5" solref=".02 1" solimp=".9 .95 .001 .5 2"/>
      </body><body name="accessory_main">
        <geom name="accessory_authored_visual" type="cylinder" size=".01 .01" group="1" rgba=".1 .2 .3 0" mass="1e-8" contype="0" conaffinity="0"/>
      </body><body name="window_main">
        <geom name="window_reg_main" type="box" size=".4 .1 .5" group="1" rgba="0 1 0 0" mass="1e-8" contype="0" conaffinity="0"/>
        <body name="window_window_background_main" pos="0 .09405 0" quat=".7071055 .7071081 0 0">
          <geom name="window_window_background_g0_vis" type="box" size=".38 .475 .0005" group="1" material="window_mat" mass="1e-8" contype="0" conaffinity="0"/>
        </body></body></worldbody></mujoco>''')
    states = source / 'states.npz'; qpos = np.zeros((201, 1)); qpos[200] = .12
    np.savez(states, qpos=qpos, time=np.arange(201) * .02)
    metadata = source / 'metadata.json'; ep_meta = source / 'ep_meta.json'
    write_json(ep_meta, {'fixtures': {k: {'cls': v} for k, v in [('counter', 'Counter'), ('accessory', 'Accessory'), ('window', 'Window')]}})
    generator = tmp_path / 'own_generator'; generator.mkdir()
    code = generator / 'constructor.py'; code.write_text('# TEST_ONLY explicit instance emission contract\n')
    reference = read_json(Path(__file__).resolve().parents[2] / 'docs/build/G2_F1_D_generator_role_catalog_2026-11-09.json')
    reference['sources'] = {'own': {'path': code.name, 'bytes': code.stat().st_size, 'sha256': digest(code),
        'root': 'own', 'repository': 'TEST_ONLY', 'commit': 'TEST_ONLY'}}
    for rule in reference['rules'].values():
        rule['generator_spans'] = [{'source_id': 'own', 'start_line': 1, 'end_line': 1, 'excerpt_sha256': digest(code)}]
    catalog = tmp_path / 'catalog.json'; write_json(catalog, reference)
    case = {'root': tmp_path, 'xml': xml, 'metadata': metadata, 'ep_meta': ep_meta, 'states': states,
            'catalog': catalog, 'roots': {'own': generator}}
    rebuild(case)
    return case


def propose(case):
    out = case['root'] / 'proposal'
    report = generate(case['paths'], case['catalog'], out, generator_roots=case['roots'])
    return report, read_json(out / 'proposed_roles.json'), read_json(out / 'hypotheses.json')


def test_all_source_branches_produce_evidence_bound_proposals(emitted):
    before = {p: digest(p) for p in [emitted['xml'], emitted['metadata'], emitted['ep_meta'], *emitted['paths']]}
    report, roles, hypotheses = propose(emitted)
    assert report['input_unknown_count'] == report['evidence_bound_proposal_count'] == 8
    assert report['remaining_without_proposal'] == 0
    assert report['proposed_role_counts'] == {'collision': 3, 'visual': 3, 'auxiliary': 2}
    assert report['inventory_unknown_count_unchanged'] == 8
    assert report['production_roles_changed'] is report['point_cloud_created'] is False
    assert report['training_ready'] is report['full_scene_source_certified'] is False
    assert report['independent_review'] == 'PENDING_GPT'
    assert roles['geoms']['accessory_authored_visual']['role'] == 'visual'
    assert len(hypotheses['entries']) == 8
    assert all(e['instance_checks']['official_fixture']['body'] for e in hypotheses['entries'])
    assert before == {p: digest(p) for p in before}


@pytest.mark.parametrize('fault', ['bad_chunk_size', 'bad_chunk_position', 'contact_marker_changed',
    'contact_material', 'contact_disabled', 'region_not_registered', 'region_visible', 'region_contact',
    'background_size', 'background_rotation', 'background_texture_uniform'])
def test_name_group_or_appearance_without_instance_facts_remains_unresolved(emitted, fault):
    text = emitted['xml'].read_text()
    expected = 'counter_handle_collision'
    if fault == 'bad_chunk_size':
        text = text.replace('size=".25 .3 .015"', 'size=".24 .3 .015"', 1); expected = 'counter_top_visual'
    elif fault == 'bad_chunk_position':
        text = text.replace('pos="-.25 0 .485"', 'pos="-.2 0 .485"'); expected = 'counter_top_visual'
    elif fault == 'contact_marker_changed': text = text.replace('rgba=".5 0 0 .5"', 'rgba="0 1 0 .5"')
    elif fault == 'contact_material': text = text.replace('rgba=".5 0 0 .5"', 'rgba=".5 0 0 .5" material="counter_counter_top"')
    elif fault == 'contact_disabled': text = text.replace('name="counter_handle_collision"', 'name="counter_handle_collision" contype="0" conaffinity="0"')
    elif fault == 'region_not_registered':
        text = text.replace('counter_reg_main', 'counter_hidden_other'); expected = 'counter_hidden_other'
    elif fault == 'region_visible':
        text = text.replace('rgba="0 1 0 0"', 'rgba="0 1 0 .4"', 1); expected = 'counter_reg_main'
    elif fault == 'region_contact':
        text = text.replace('name="counter_reg_main"', 'name="counter_reg_main" contype="1"')
        # Remove the now duplicate attribute on that own test line.
        text = '\n'.join(line.replace('contype="0"', '') if 'counter_reg_main' in line else line for line in text.splitlines())
        expected = 'counter_reg_main'
    elif fault == 'background_size':
        text = text.replace('size=".38 .475 .0005"', 'size=".39 .475 .0005"'); expected = 'window_window_background_g0_vis'
    elif fault == 'background_rotation':
        text = text.replace('quat=".7071055 .7071081 0 0"', 'quat="1 0 0 0"'); expected = 'window_window_background_g0_vis'
    else:
        text = text.replace('texuniform="true"', 'texuniform="false"'); expected = 'window_window_background_g0_vis'
    rebuild(emitted, text)
    report, roles, hypotheses = propose(emitted)
    assert expected not in roles['geoms']
    assert report['remaining_without_proposal'] >= 1
    assert report['production_roles_changed'] is False


def test_generator_version_drift_refuses_proposals(emitted):
    (emitted['roots']['own'] / 'constructor.py').write_text('# changed source contract\n')
    with pytest.raises(ContractError): propose(emitted)
    assert not (emitted['root'] / 'proposal/proposed_roles.json').exists()


def test_transparent_child_body_is_not_a_registered_fixture_region(emitted):
    text = emitted['xml'].read_text().replace('<body name="accessory_main">', '''<body name="accessory_main">
      <body name="accessory_liquid"><geom name="accessory_liquid_reg_surface" type="cylinder"
       size=".01 .02" group="1" rgba="0 0 1 0" mass="1e-8" contype="0" conaffinity="0"/></body>''')
    rebuild(emitted, text)
    _, roles, _ = propose(emitted)
    assert roles['geoms']['accessory_liquid_reg_surface']['role'] == 'visual'


def test_existing_output_is_never_overwritten(emitted):
    out = emitted['root'] / 'proposal'; out.mkdir()
    original = out / 'proposed_roles.json'; original.write_text('KEEP ORIGINAL\n')
    with pytest.raises(ContractError, match='new'):
        propose(emitted)
    assert original.read_text() == 'KEEP ORIGINAL\n'
    assert not (out / 'original_inventory_analysis').exists()


def test_output_inside_generator_tree_is_refused_before_any_write(emitted):
    out = emitted['roots']['own'] / 'analysis'
    with pytest.raises(ContractError, match='overlaps'):
        generate(emitted['paths'], emitted['catalog'], out, generator_roots=emitted['roots'])
    assert not out.exists()


def test_rotating_all_counter_parts_does_not_prove_factory_coverage(emitted):
    text = emitted['xml'].read_text()
    for name in ('counter_top_visual', 'counter_top_0', 'counter_top_1'):
        text = text.replace('name="' + name + '"', 'name="' + name + '" quat=".7071067811865476 0 0 .7071067811865476"')
    rebuild(emitted, text)
    _, roles, _ = propose(emitted)
    assert not {'counter_top_visual', 'counter_top_0', 'counter_top_1'} & set(roles['geoms'])


@pytest.mark.parametrize('bad_parent', [False, True])
def test_window_real_include_parent_overrides_ignored_wrapper(emitted, bad_parent):
    text = emitted['xml'].read_text()
    start = text.index('<geom name="window_window_background_g0_vis"')
    end = text.index('/>', start) + 2
    geom = text[start:end]
    fragment = emitted['xml'].parent / 'background.inc'
    fragment.write_text('<body name="window_window_background_main" pos="0 .09405 0" '
        'quat=".7071055 .7071081 0 0">' + geom + '</body>')
    text = text[:start] + '<include file="background.inc"/>' + text[end:]
    if bad_parent:
        text = text.replace('pos="0 .09405 0" quat=".7071055 .7071081 0 0"', 'pos="0 0 0" quat="1 0 0 0"')
    rebuild(emitted, text)
    _, roles, hypotheses = propose(emitted)
    assert ('window_window_background_g0_vis' in roles['geoms']) is not bad_parent
    if not bad_parent:
        entry = next(e for e in hypotheses['entries'] if e['rule_id'] == 'window_background_visual')
        assert entry['instance_checks']['original_composed_body_evidence']['source_logical_id'] == 'root.xml'


@pytest.mark.parametrize('fault', [None, 'wrong_scale', 'unregistered_model', 'other_instance',
                                  'non_live_bbox', 'non_live_mesh', 'rotated_template_helper',
                                  'transparent_default', 'opaque_default', 'transparent_childclass'])
def test_nested_alignment_helper_requires_actual_model_and_scale(emitted, fault):
    from g2.sim.source_geometry import primitive_mesh
    assets = emitted['xml'].parent / 'fixtures/cabinets/cabinet_panels/CabinetDoorPanel001'
    if fault == 'unregistered_model': assets = assets.parent / 'UnregisteredDirectory'
    assets.mkdir(parents=True)
    vertices, faces = primitive_mesh('box', np.asarray([.2, .025, .25]))
    mesh = assets / 'mesh.obj'
    mesh.write_text(''.join('v %.17g %.17g %.17g\n' % tuple(v) for v in vertices)
        + ''.join('f %d %d %d\n' % tuple(f + 1) for f in faces))
    helper = '<geom name="reg_main" type="box" size=".2 .025 .25" rgba="0 1 0 0"/>'
    defaults = ''; body_attributes = ''
    if fault in ('transparent_default', 'opaque_default', 'transparent_childclass'):
        helper = helper.replace(' rgba="0 1 0 0"', '')
        rgba = '0 1 0 1' if fault == 'opaque_default' else '0 1 0 0'
        defaults = '<default><default class="bbox"><geom rgba="' + rgba + '"/></default></default>'
        if fault == 'transparent_childclass': body_attributes = ' childclass="bbox"'
        else: helper = helper.replace('type="box"', 'type="box" class="bbox"')
    if fault == 'rotated_template_helper': helper = helper.replace('type="box"', 'type="box" quat=".7071067811865476 0 0 .7071067811865476"')
    surface = '<geom name="surface" type="mesh" mesh="m"/>'
    live = ('' if fault == 'non_live_bbox' else helper) + ('' if fault == 'non_live_mesh' else surface)
    dead = helper if fault == 'non_live_bbox' else surface if fault == 'non_live_mesh' else ''
    (assets / 'model.xml').write_text('<mujoco>' + defaults + '<asset><mesh name="m" file="mesh.obj"/></asset><worldbody>'
        '<body name="outer"><body name="object"' + body_attributes + '>' + live + '</body></body><body name="unused">' + dead + '</body></worldbody></mujoco>')
    mesh_scale = '3 3 3' if fault == 'wrong_scale' else '2 2 2'
    text = emitted['xml'].read_text().replace('<asset>', '<asset><mesh name="panel_mesh" file="' + str(mesh) + '" scale="' + mesh_scale + '"/>')
    mesh_geom = '<geom name="cabinet_door_surface" type="mesh" mesh="panel_mesh" material="counter_counter_top" group="1" contype="0" conaffinity="0" mass="1e-8"/>'
    if fault == 'other_instance': mesh_geom = '<body name="neighbor">' + mesh_geom + '</body>'
    text = text.replace('</worldbody>', '''<body name="cabinet_main"><body name="cabinet_hingedoor"><body name="cabinet_door_main">
       <geom name="cabinet_door_reg_main" type="box" size=".4 .05 .5" rgba="0 1 0 0" group="1" contype="0" conaffinity="0" mass="1e-8"/>
       ''' + mesh_geom + '</body></body></body></worldbody>')
    ep = read_json(emitted['ep_meta']); ep['fixtures']['cabinet'] = {'cls': 'SingleCabinet'}; write_json(emitted['ep_meta'], ep)
    rebuild(emitted, text)
    _, roles, hypotheses = propose(emitted)
    if fault in (None, 'transparent_default', 'transparent_childclass'):
        assert roles['geoms']['cabinet_door_reg_main']['role'] == 'auxiliary'
        proof = next(e for e in hypotheses['entries'] if e['geom_id'] == len(read_json(emitted['paths'][0])['geom_audit']) - 2)
        assert proof['rule_id'] == 'nested_registered_mesh_alignment_helper'
    else:
        assert 'cabinet_door_reg_main' not in roles['geoms']


def test_window_unnamed_intermediate_body_is_not_a_factory_direct_child(emitted):
    text = emitted['xml'].read_text().replace('<body name="window_window_background_main"',
                                           '<body><body name="window_window_background_main"')
    text = text.replace('</body></body></worldbody>', '</body></body></body></worldbody>')
    rebuild(emitted, text)
    _, roles, _ = propose(emitted)
    assert 'window_window_background_g0_vis' not in roles['geoms']


@pytest.mark.parametrize('defaults', ['<default><default class="main"/></default>',
    '<default class="renamed"/>', '<default><default class="bbox"/><default class="bbox"/></default>'])
def test_invalid_template_default_definitions_are_not_role_evidence(defaults):
    import xml.etree.ElementTree as ET
    from g2.sim.role_hypotheses import _template_attributes
    root = ET.fromstring('<mujoco>' + defaults + '<worldbody><body><body name="object">'
        '<geom name="reg_main" type="box" size="1 1 1"/></body></body></worldbody></mujoco>')
    target = root.find('.//geom[@name="reg_main"]')
    with pytest.raises(ContractError): _template_attributes(root, target)


@pytest.mark.parametrize('explicit_main', [False, True])
def test_top_level_main_merge_matches_native_mujoco_semantics(explicit_main):
    import mujoco
    import xml.etree.ElementTree as ET
    from g2.sim.role_hypotheses import _template_attributes
    attribute = ' class="main"' if explicit_main else ''
    defaults = ('<default' + attribute + '><geom rgba="0 1 0 1" friction=".7 .1 .1"/></default>'
        '<default' + attribute + '><geom rgba="0 1 0 0"/></default>')
    text = '<mujoco>' + defaults + '<worldbody><body><body name="object">' \
        '<geom name="reg_main" type="box" size="1 1 1"/></body></body></worldbody></mujoco>'
    model = mujoco.MjModel.from_xml_string(text)
    root = ET.fromstring(text)
    attrs = _template_attributes(root, root.find('.//geom[@name="reg_main"]'))
    assert float(attrs['rgba'].split()[-1]) == float(model.geom_rgba[0,3]) == 0.
    assert float(attrs['friction'].split()[0]) == float(model.geom_friction[0,0]) == .7
