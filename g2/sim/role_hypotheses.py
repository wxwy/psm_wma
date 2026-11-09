"""Derive reviewable role proposals from original instance emission evidence.

Runs beside private inventories on their server. It never executes generators,
edits source assets, assigns production roles, or certifies whole-house input.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from g2.io import ContractError, canonical, digest, new_output, read_json, verified_file, write_json
from .prescan import source_binding
from .role_review import analyze
from .source_geometry import xml_payload


def _numbers(text, default):
    values = np.asarray([float(v) for v in text.split()] if text is not None else default)
    if not np.isfinite(values).all():
        raise ContractError("nonfinite original primitive attributes")
    return values


def _close(a, b):
    return np.shape(a) == np.shape(b) and np.allclose(a, b, rtol=1e-8, atol=1e-10)


def _primitive(row):
    """Original type/size/pose must reproduce the compiled local primitive."""
    evidence = row["role_evidence"]
    if evidence["status"] != "SOURCE_BOUND" or len(evidence["source_geom_nodes"]) != 1:
        return False
    a = evidence["source_geom_nodes"][0]["attributes"]
    kind = row["geometry_type"]
    if kind not in ("box", "cylinder") or a.get("type") != kind:
        return False
    try:
        size = _numbers(a.get("size"), [])
        position = _numbers(a.get("pos"), [0., 0., 0.])
        quaternion = _numbers(a.get("quat"), [1., 0., 0., 0.])
        if len(size) != (3 if kind == "box" else 2) or np.any(size <= 0) or len(quaternion) != 4:
            return False
        norm = np.linalg.norm(quaternion)
        if norm == 0:
            return False
        p = evidence["compiled_properties"]
        return (_close(size, row["geom_size"][:len(size)]) and _close(position, p["local_position"])
                and (_close(quaternion / norm, p["local_quaternion"])
                     or _close(-quaternion / norm, p["local_quaternion"])))
    except (ValueError, TypeError, ContractError):
        return False


def _owner(row, fixtures):
    node = row["role_evidence"]["source_geom_nodes"]
    if len(node) != 1:
        return None
    original = set(node[0]["body_ancestors"])
    for body in row["body_ancestry"]:  # nearest genuine official root first
        name = body["body_name"]
        matches = [(key, value) for key, value in fixtures.items() if isinstance(value, dict)
                   and isinstance(value.get("cls"), str) and value["cls"].strip()
                   and name in (key, key + "_main") and name in original]
        if len(matches) == 1:
            key, value = matches[0]
            return {"instance": key, "category": value["cls"], "body": name,
                    "pointer": "/fixtures/" + key.replace("~", "~0").replace("/", "~1")}
        if matches:
            return None
    return None


def _attributes(row):
    return row["role_evidence"]["source_geom_nodes"][0]["attributes"]


def _local(row):
    return row["role_evidence"]["compiled_properties"]["local_position"]


def _same_orientation(left, right):
    if any(k in left or k in right for k in ('euler', 'axisangle', 'xyaxes', 'zaxis')):
        return False
    a = _numbers(left.get('quat'), [1., 0., 0., 0.]); b = _numbers(right.get('quat'), [1., 0., 0., 0.])
    if a.shape != (4,) or b.shape != (4,) or not np.linalg.norm(a) or not np.linalg.norm(b):
        return False
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    return _close(a, b) or _close(a, -b)


def _template_attributes(root, target):
    """Resolve main / inherited default geom class and body childclass."""
    classes = {'main': {}}
    def defaults(node, inherited, top=False):
        key = node.get('class', 'main' if top else '')
        # MuJoCo allows multiple top-level main blocks, which merge in order;
        # nested main and renaming the top-level default are invalid.
        if (top and key != 'main') or (not top and (not key or key == 'main' or key in classes)):
            raise ContractError('ambiguous template default class')
        attrs = dict(inherited)
        geoms = node.findall('geom')
        if len(geoms) > 1:
            raise ContractError('ambiguous template default geom')
        if geoms: attrs.update(geoms[0].attrib)
        classes[key] = attrs
        for child in node.findall('default'): defaults(child, attrs)
    for node in root.findall('default'): defaults(node, classes['main'], top=True)
    result = None
    def walk(node, inherited):
        nonlocal result
        if node.tag in ('default', 'asset'):
            return
        current = node.get('childclass', inherited) if node.tag in ('body', 'worldbody') else inherited
        if node is target:
            key = node.get('class', current)
            if key not in classes:
                raise ContractError('unknown template geom default class')
            result = dict(classes[key], **node.attrib)
        for child in node: walk(child, current)
    walk(root, 'main')
    if result is None:
        raise ContractError('template geom is outside the live tree')
    return result


def _body_facts(sources):
    """Expand real body context; an included root is never a body ancestor."""
    parsed, facts = {}, {}
    for record in sources:
        if record.get('source_kind') == 'mjcf_xml':
            if digest(record['path']) != record['sha256']:
                raise ContractError('original body source changed')
            parsed[record['logical_id']] = record, ET.fromstring(xml_payload(Path(record['path'])))
    def children(logical, node, path, chain, excluded, includes):
        counts = {}
        for child in node:
            i = counts.get(child.tag, 0); counts[child.tag] = i + 1
            walk(logical, child, path + '/' + child.tag + '[' + str(i) + ']', chain, excluded, includes)
    def walk(logical, node, path, chain, excluded, includes):
        record, _ = parsed[logical]
        excluded = excluded or node.tag in ('asset', 'default')
        if node.tag == 'include':
            targets = {r['logical_id'] for r in record.get('includes', []) if r['reference'] == node.get('file')}
            if len(targets) != 1:
                raise ContractError('body include context unresolved')
            target = targets.pop()
            if target not in parsed or target in [logical, *includes]:
                raise ContractError('body include context invalid')
            root = parsed[target][1]
            children(target, root, '/' + root.tag, chain, excluded, [*includes, logical])
        if node.tag == 'body' and node.get('name') and not excluded:
            chain = [*chain, node.get('name')]
            facts.setdefault(tuple(chain), []).append({'attributes': dict(node.attrib), 'body_ancestors': chain,
                'source_logical_id': logical, 'source_sha256': record['sha256'], 'xml_path': path,
                'including_source_ids': includes})
        children(logical, node, path, chain, excluded, includes)
    if 'root.xml' not in parsed:
        raise ContractError('original root body source missing')
    root = parsed['root.xml'][1]
    walk('root.xml', root, '/' + root.tag, [], False, [])
    return facts


def _alignment_template(row, owner, rows, inventory, reference):
    """Prove a registered nested panel/handle's actual bbox-to-mesh scaling."""
    if not any(kind in owner['category'] for kind in ('Cabinet', 'Drawer')):
        return None
    name = row['geom_name']
    for door in ('door', 'left_door', 'right_door'):
        panel = owner['instance'] + '_' + door
        for prefix, kind in ((panel, 'panel'), (panel + '_handle', 'handle')):
            if name != prefix + '_reg_main':
                continue
            ancestry = row['body_ancestry']
            if not ancestry or ancestry[0]['body_name'] != prefix + '_main' or len(ancestry) < 2:
                continue
            allowed = {panel + '_main'} if kind == 'handle' else {
                owner['body'], owner['instance'] + '_hingedoor', owner['instance'] + '_hingeleftdoor',
                owner['instance'] + '_hingerightdoor', owner['instance'] + '_inner_box'}
            if ancestry[1]['body_name'] not in allowed:
                continue
            originals = {s['logical_id']: s for s in inventory['sources']}
            for mesh in rows:
                if (mesh['geometry_type'] != 'mesh' or mesh['body_ancestry'] != ancestry or mesh['group'] != 1
                    or mesh['contype'] or mesh['conaffinity'] or mesh['material_id'] < 0 or mesh['effective_rgba'][3] <= 0
                    or mesh['role_evidence']['status'] != 'SOURCE_BOUND'):
                    continue
                node = mesh['role_evidence']['source_geom_nodes'][0]
                source = originals[node['source_logical_id']]
                root = ET.fromstring(xml_payload(Path(source['path'])))
                definitions = [m for m in root.findall('./asset/mesh') if m.get('name') == node['attributes'].get('mesh')]
                if len(definitions) != 1 or not definitions[0].get('file'):
                    continue
                definition = definitions[0]; file = Path(definition.get('file'))
                compiler = root.find('compiler')
                meshdir = (compiler.get('meshdir') or compiler.get('assetdir') or '') if compiler is not None else ''
                candidates = {file.resolve(), (Path(source['path']).parent / file).resolve(),
                              (Path(source['path']).parent / meshdir / file).resolve()}
                assets = [s for s in inventory['sources'] if s.get('source_kind') == 'asset' and Path(s['path']).resolve() in candidates]
                if len(assets) != 1 or digest(assets[0]['path']) != assets[0]['sha256']:
                    continue
                actual_file = Path(assets[0]['path']).resolve()
                for model in reference.get('registered_alignment_models', {}).get(kind, []):
                    directory = Path(model).parent
                    suffix = str(directory).replace('\\', '/') + '/'
                    full = str(actual_file).replace('\\', '/')
                    if suffix not in full:
                        continue
                    template_file = Path(full[:full.index(suffix)]) / model
                    if not template_file.is_file():
                        continue
                    payload = xml_payload(template_file)
                    template_sha = hashlib.sha256(payload).hexdigest()
                    template = ET.fromstring(payload)
                    live = template.findall('./worldbody/body/body[@name="object"]')
                    if len(live) != 1:
                        continue
                    helpers = [g for g in live[0].iter('geom') if g.get('name') == 'reg_main']
                    if len(helpers) != 1 or helpers[0].get('type', 'sphere') != 'box':
                        continue
                    helper = _template_attributes(template, helpers[0])
                    if not _same_orientation(helper, _attributes(row)):
                        continue
                    original_size = _numbers(helper.get('size'), [])
                    if (len(original_size) != 3 or np.any(original_size <= 0)
                        or _numbers(helper.get('rgba'), [0., 0., 0., 1.])[-1] != 0):
                        continue
                    scale = np.asarray(row['geom_size']) / original_size
                    if not _close(_local(row), _numbers(helper.get('pos'), [0., 0., 0.]) * scale):
                        continue
                    # The actual asset must be a model-declared mesh, with the
                    # same scale transformation used for its reg_main bbox.
                    comp = template.find('compiler')
                    directory_hint = (comp.get('meshdir') or comp.get('assetdir') or '') if comp is not None else ''
                    for original in template.findall('./asset/mesh'):
                        if not original.get('file'):
                            continue
                        target = (template_file.parent / directory_hint / original.get('file')).resolve()
                        if target != actual_file:
                            continue
                        expected_scale = _numbers(original.get('scale'), [1., 1., 1.]) * scale
                        if not _close(_numbers(definition.get('scale'), [1., 1., 1.]), expected_scale):
                            continue
                        geoms = [g for g in live[0].iter('geom') if g.get('mesh') == original.get('name')]
                        # MuJoCo can recenter compiled mesh frames. Compare
                        # original emitted poses, while retaining the compiled
                        # mesh signature as its independent identity evidence.
                        matching = [g for g in geoms if _same_orientation(_template_attributes(template, g), node['attributes'])
                            and _close(_numbers(node['attributes'].get('pos'), [0., 0., 0.]),
                                       _numbers(_template_attributes(template, g).get('pos'), [0., 0., 0.]) * scale)]
                        if len(matching) != 1:
                            continue
                        return {'nested_factory_instance': prefix, 'factory_parent_body': ancestry[1]['body_name'],
                            'registered_model': model, 'model_xml_sha256': template_sha,
                            'original_mesh_source_sha256': assets[0]['sha256'], 'visible_mesh_geom_id': mesh['geom_id'],
                            'actual_bbox_and_asset_scale_agree': scale.tolist(),
                            'constructor': 'Cabinet._add_door / CabinetPanel._add_handle -> VisualMeshPanel/Handle reg_main scaling'}
    return None


def generate(inventories, catalog, output, *, generator_roots):
    """Generate per-component hypotheses and a separate, unapproved map proposal."""
    paths = [Path(p).resolve(strict=True) for p in inventories]
    captured = [p.read_bytes() for p in paths]
    first_input = read_json(paths[0])
    reference = read_json(catalog)
    protected = [*paths, catalog, *generator_roots.values()]
    protected.extend(Path(s['path']).resolve(strict=True).parent for s in first_input['sources'])
    protected.extend(r['path'] for r in first_input.get('input_files', {}).values())
    for source in first_input['sources']:
        full = str(Path(source['path']).resolve()).replace('\\', '/')
        for models in reference.get('registered_alignment_models', {}).values():
            for model in models:
                suffix = str(Path(model).parent).replace('\\', '/') + '/'
                if suffix in full:
                    protected.append(Path(full[:full.index(suffix)]) / Path(model).parent)
    out = new_output(output, protected)
    # Existing verifier protects original source trees before creating outputs.
    baseline = analyze(paths, catalog, out / "original_inventory_analysis")
    if captured != [p.read_bytes() for p in paths]:
        raise ContractError("inventory changed while matching source instances")
    first = read_json(paths[0]); rows = first["geom_audit"]
    for record in reference["sources"].values():
        if record["root"] not in generator_roots:
            raise ContractError("matching generator roots required")
        verified_file(generator_roots[record["root"]], record)
    fixtures = (first["source_identity"].get("ep_meta") or {}).get("fixtures", {})
    if not isinstance(fixtures, dict):
        raise ContractError("official fixture dictionary required")
    unknown = {r["geom_id"]: r for r in rows if r["role"] == "UNCLASSIFIED"}
    owners = {r["geom_id"]: _owner(r, fixtures) for r in rows}
    by_name = {r["geom_name"]: r for r in rows}
    proposals, conflicts = {}, set()

    def propose(row, role, rule, facts):
        g = row["geom_id"]
        if g not in unknown or g in conflicts:
            return
        if g in proposals:
            if proposals[g]["role"] != role:
                del proposals[g]; conflicts.add(g)
            return
        owner = owners[g]
        node = row["role_evidence"]["source_geom_nodes"][0]
        facts = dict(facts, official_fixture=owner, source_geom_node_sha256=node["source_geom_node_sha256"],
                     compiled_signature_sha256=row["role_evidence"]["compiled_signature_sha256"])
        serialized = canonical(facts).decode()
        proposals[g] = {"geom_id": g, "role": role, "rule_id": rule,
            "compiled_signature_sha256": row["role_evidence"]["compiled_signature_sha256"],
            "source_geom_node_sha256": node["source_geom_node_sha256"], "source_attributes": node["attributes"],
            "classification_reason": "Original instance emission matches " + rule + "; independent review pending",
            "emission_trace": serialized, "condition_evidence": {
                condition: serialized for condition in reference["rules"][rule]["conditions"]}, "instance_checks": facts}

    # Counter material + complete factory chunk decomposition, not a suffix vote.
    for visual in rows:
        owner = owners[visual["geom_id"]]
        if (not owner or "Counter" not in owner["category"] or not _primitive(visual)
            or visual["geometry_type"] != "box" or visual["group"] != 1
            or visual["contype"] != 0 or visual["conaffinity"] != 0):
            continue
        a = _attributes(visual); name = visual["geom_name"]
        quaternion = visual['role_evidence']['compiled_properties']['local_quaternion']
        if (a.get("material") != owner["instance"] + "_counter_top" or not name.endswith("_visual")
            or visual["material_id"] < 0 or visual["effective_rgba"][3] <= 0
            or not (_close(quaternion, [1., 0., 0., 0.]) or _close(quaternion, [-1., 0., 0., 0.]))):
            continue
        base = name[:-7]; position = np.asarray(_local(visual)); half = np.asarray(visual["geom_size"])
        width = 2 * half[0]; count = math.ceil(width / .5)
        if count > len(rows):
            continue
        chunks, widths = [], [.5] * count
        widths[-1] = width - sum(widths[:-1])
        for i, length in enumerate(widths):
            part = by_name.get(base + "_" + str(i))
            expected = position + [-half[0] + sum(widths[:i]) + length / 2, 0, 0]
            if (part is None or not _primitive(part) or owners[part["geom_id"]] != owner
                or part["body_ancestry"] != visual["body_ancestry"]
                or part["group"] != 0 or part["contype"] != 1 or part["conaffinity"] != 1
                or part["material_id"] != -1 or "material" in _attributes(part)
                or not _close(part["geom_size"], [length / 2, half[1], half[2]])
                or not _close(_local(part), expected)
                or not _close(part["role_evidence"]["compiled_properties"]["local_quaternion"],
                              visual["role_evidence"]["compiled_properties"]["local_quaternion"])):
                break
            chunks.append(part)
        if len(chunks) != count:
            continue
        opening = not base.endswith("_top")
        facts = {"complete_half_metre_factory_chunks": [p["geom_id"] for p in chunks],
                 "original_full_surface_size": half.tolist(), "original_full_surface_position": position.tolist(),
                 "source_material": a["material"], "source_geometry_and_body_verified": True}
        propose(visual, "visual", "counter_opening_visual" if opening else "counter_contiguous_visual", facts)
        for part in chunks:
            propose(part, "collision", "counter_opening_contact_chunks" if opening else "counter_contiguous_contact_chunks", facts)

    for row in unknown.values():
        g = row["geom_id"]; owner = owners[g]
        if not owner or not _primitive(row):
            continue
        a = _attributes(row)
        physics = row["contype"] == 1 and row["conaffinity"] == 1
        # Active physics, original no-material marker, solver parameters,
        # official instance ancestry and original/compiled primitive all agree.
        visible_sibling = any(owners[q["geom_id"]] == owner and q["group"] == 1 and q["contype"] == 0
                              and q["conaffinity"] == 0 and q["material_id"] >= 0 and q["effective_rgba"][3] > 0 for q in rows)
        if (row["group"] == 0 and physics and row["material_id"] == -1 and "material" not in a
            and _close(row["compiled_rgba"][:3], [.5, 0., 0.]) and {"solref", "solimp"} <= set(a)
            and visible_sibling):
            propose(row, "collision", "fixture_contact_registry_primitive", {
                "official_constructor_registry": "MujocoObject._get_object_properties -> sort_elements -> contact_geoms",
                "active_contact_bits": [1, 1], "no_surface_material": True, "original_collision_rgb_marker": True,
                "solver_parameters_in_original_node": True, "visual_material_representation_under_same_fixture": True,
                "original_primitive_size_pose_matches_compiled": True})
        noncontact = row["contype"] == 0 and row["conaffinity"] == 0
        # Only a real official Fixture's naming_prefix is proven here. A
        # conveniently named ordinary child body is not a Fixture instance.
        region_prefixes = [owner['instance']] if row['geom_name'].startswith(owner['instance'] + '_reg_') else []
        if (row["group"] == 1 and noncontact and row["effective_rgba"][3] == 0
            and row["material_id"] == -1 and region_prefixes):
            propose(row, "auxiliary", "fixture_region_nonphysical", {
                "original_fixture_region_namespace": max(region_prefixes, key=len),
                "source_registration": "Fixture.__init__ consumes this prefixed reg_ geom into _regions",
                "original_primitive_size_pose_matches_compiled": True,
                "transparent_and_noncontact_in_compiled_model": True})
        if (row['group'] == 1 and noncontact and row['effective_rgba'][3] == 0 and row['material_id'] == -1
            and not region_prefixes and row['geometry_type'] == 'box'):
            alignment = _alignment_template(row, owner, rows, first, reference)
            if alignment:
                propose(row, 'auxiliary', 'nested_registered_mesh_alignment_helper', alignment)
        # A transparent authored visual is retained as visual, never hidden as
        # auxiliary merely because its colour/semantic purpose is unavailable.
        if (row["group"] == 1 and noncontact and row["effective_rgba"][3] == 0 and not region_prefixes
            and any(kind in owner["category"] for kind in ("Accessory", "Stool"))):
            propose(row, "visual", "accessory_transparent_visual_registry", {
                "official_constructor": "Accessory/WallAccessory -> Fixture -> MujocoXMLObject visual registry",
                "original_primitive_size_pose_matches_compiled": True, "source_visual_registry_and_noncontact": True,
                "transparency_does_not_justify_auxiliary_exclusion": True, "semantic_subpurpose": "NOT_INFERRED"})

    # Window background factory uses a thin box, shared material, a specific
    # composed body rotation and the actual original window region dimensions.
    body_facts = _body_facts(first['sources'])
    for row in unknown.values():
        owner = owners[row["geom_id"]]
        if (not owner or "Window" not in owner["category"] or not _primitive(row)
            or row["geometry_type"] != "box" or row["group"] != 1 or row["contype"] or row["conaffinity"]):
            continue
        a = _attributes(row); node = row["role_evidence"]["source_geom_nodes"][0]
        body_name = owner["instance"] + "_window_background_main"
        if body_name not in node["body_ancestors"] or not a.get("material", "").endswith("window_mat"):
            continue
        bodies = body_facts.get(tuple(node['body_ancestors']), [])
        region = by_name.get(owner["instance"] + "_reg_main")
        if (len(bodies) != 1 or region is None or len(node['body_ancestors']) < 2
            or node['body_ancestors'][-1] != body_name or node['body_ancestors'][-2] != owner['body']
            or row['body_ancestry'][0]['body_name'] != body_name or row['body_ancestry'][1]['body_name'] != owner['body']):
            continue
        half = np.asarray(region["geom_size"]); position = np.asarray(_local(region))
        expected_position = position + [0, (half[1] - .001) * .95, 0]
        quaternion = _numbers(bodies[0]['attributes'].get("quat"), [1., 0., 0., 0.])
        target = np.asarray([.7071055, .7071081, 0., 0.])
        if (_close(row["geom_size"], [half[0] * .95, half[2] * .95, .0005])
            and _close(_numbers(bodies[0]['attributes'].get("pos"), [0., 0., 0.]), expected_position)
            and _close(quaternion / np.linalg.norm(quaternion), target / np.linalg.norm(target))
            and row["material"].get("texuniform") is True and row["material"].get("texrepeat") == [1., 1.]
            and row["material"].get("texture_bindings")):
            propose(row, "visual", "window_background_visual", {"original_window_region": region["geom_id"],
                "box_size_body_pose_matches_add_background": True, "actual_bound_texture_and_material": row["material"],
                "official_composed_body": body_name, 'original_composed_body_evidence': bodies[0]})

    entries = [proposals[g] for g in sorted(proposals)]
    hypotheses = out / "hypotheses.json"
    write_json(hypotheses, {"schema": "g2_role_hypotheses_v1", "entries": entries})
    reviewed = analyze(paths, catalog, out / "candidate_evidence_analysis", decisions=hypotheses,
                       generator_roots=generator_roots)
    bound = {r["geom_id"] for r in reviewed["geom_analysis"] if r["review_state"] == "EVIDENCE_BOUND_CANDIDATE_PENDING_GPT"}
    metadata = copy.deepcopy(first["source_identity"]["metadata"])
    for entry in entries:
        if entry["geom_id"] not in bound:
            continue
        row = unknown[entry["geom_id"]]; owner = owners[entry["geom_id"]]
        spec = {"role": entry["role"], "source_kind": "ep_meta", "geom_name": row["geom_name"],
            "source_instance_name": owner["instance"], "source_body_name": owner["body"],
            "ep_meta_pointer": owner["pointer"], "source_category_field": "cls", "source_category": owner["category"],
            "classification_reason": entry["classification_reason"], "role_evidence": {
                "compiled_signature_sha256": entry["compiled_signature_sha256"],
                "source_geom_node_sha256": entry["source_geom_node_sha256"], "asserted_role": entry["role"]}}
        source_binding(spec, row["geom_name"], first["source_identity"]["ep_meta"],
                       body_names=[b["body_name"] for b in row["body_ancestry"] if b["body_id"] != 0])
        metadata["geoms"][row["geom_name"]] = spec
    write_json(out / "proposed_roles.json", metadata)
    unresolved = [{"geom_id": g, "compiled_signature_sha256": row["role_evidence"]["compiled_signature_sha256"],
        "reason": "CONFLICTING_SOURCE_RULES" if g in conflicts else "NO_VERIFIED_INSTANCE_EMISSION_MATCH"}
        for g, row in unknown.items() if g not in bound]
    write_json(out / "unresolved.json", unresolved)
    summary = {"schema": "g2_source_role_proposal_v1", "status": "AUTHOR_PROPOSED_PENDING_GPT",
        "input_unknown_count": len(unknown), "evidence_bound_proposal_count": len(bound),
        "remaining_without_proposal": len(unresolved), "proposed_role_counts": dict(Counter(e["role"] for e in entries if e["geom_id"] in bound)),
        "proposed_rule_counts": dict(Counter(e["rule_id"] for e in entries if e["geom_id"] in bound)),
        "inventory_unknown_count_unchanged": baseline["remaining_unclassified_count"],
        "frames": baseline["frames"], "model_source_sha256": baseline["model_source_sha256"],
        "catalog_sha256": digest(catalog), "implementation_sha256": digest(Path(__file__)),
        "files": {p.name: digest(p) for p in (hypotheses, out / "proposed_roles.json", out / "unresolved.json")},
        "production_roles_changed": False, "point_cloud_created": False, "full_scene_source_certified": False,
        "training_ready": False, "independent_review": "PENDING_GPT"}
    write_json(out / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="append", required=True)
    parser.add_argument("--catalog", required=True); parser.add_argument("--output", required=True)
    parser.add_argument("--generator-root", action="append", default=[])
    args = parser.parse_args(); roots = {}
    for item in args.generator_root:
        name, sep, path = item.partition("=")
        if not name or not sep or not path or name in roots:
            parser.error("generator-root must be unique NAME=PATH")
        roots[name] = path
    result = generate(args.inventory, args.catalog, args.output, generator_roots=roots)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
