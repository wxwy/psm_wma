"""F15 native G2 C++ buildNativeSpatialGroups semantic-exact Python port.

This is not a new object classifier. It is a direct semantic port of
nav_sg/mapping_8_3/mapping/src/map_input/spatial_snapshot.cpp,
and is checked against both preexisting independent native snapshots.
"""
from collections import deque
import copy
import math

SOURCE = "nav_sg::buildNativeSpatialGroups NATIVE_BBOX_OBJECT_ROOT_CONNECTIONS_V2"

def gap(a,b):
    return math.sqrt(sum(max(float(a["bbox_min"][i])-float(b["bbox_max"][i]),
                             float(b["bbox_min"][i])-float(a["bbox_max"][i]),0.)**2
                         for i in range(3)))

def compute(entities,room_uids,connection_distance=.30,known=True):
    assert 0 < connection_distance <= 1
    byid={e["id"]:e for e in entities}
    assert len(byid)==len(entities)
    objects=[e for e in entities if e["kind"]=="object"]
    roots=[e for e in entities if e["kind"]!="object"]
    # Original C++ traverses SceneGraphObject instances in ascending native
    # integer cluster ID; string sorting only applies to std::map outputs.
    order=lambda e:int(e["id"].split("_")[-1])
    objects.sort(key=order)
    roots.sort(key=order)
    n=len(objects)
    ids=[e["id"] for e in objects]
    idx={e["id"]:i for i,e in enumerate(objects)}
    allowed=[
       bool(e["connection_relay_allowed"]) and
       e["kind"]=="object" and
       e["source_category_id"] not in ("robot","auxiliary") and
       e["label"]!="robot"
       for e in objects
    ]
    adj=[[] for _ in range(n)]
    parent=list(range(n))
    def find(i):
        while parent[i]!=i:
            i=parent[i]
        return i
    for i in range(n):
        if not allowed[i] or objects[i]["room_uid"]<0:continue
        for j in range(i+1,n):
            if allowed[j] and objects[j]["room_uid"]==objects[i]["room_uid"] and gap(objects[i],objects[j])<connection_distance:
                parent[find(j)]=find(i)
                adj[i].append(j)
                adj[j].append(i)
    for el in adj:el.sort(key=lambda i:order(objects[i]))
    components_unsorted={}
    for i,e in enumerate(objects):
        if allowed[i] and e["room_uid"]>=0:
            components_unsorted.setdefault(find(i),set()).add(e["id"])
    known_has_floor=any(r["kind"]=="floor" for r in roots)
    walls_known=all(r.get("triangles") for r in roots if r["kind"]=="wall")
    complete=known and known_has_floor and walls_known
    affiliations={key:set() for key in ids}
    paths={key:{} for key in ids}
    direct_gaps={key:{} for key in ids}
    for root in roots:
        rootid=root["id"]
        observed=(known or bool(root.get("native_structure",False))) and (root["kind"]=="floor" or bool(root.get("triangles")))
        previous=[-2]*n
        seeds=[]
        for i,obj in enumerate(objects):
            d=gap(obj,root)
            direct_gaps[obj["id"]][rootid]=d
            if observed and allowed[i] and obj["room_uid"]>=0 and d<connection_distance:
                seeds.append(i)
        seeds.sort(key=lambda i:order(objects[i]))
        queue=deque()
        for seed in seeds:
            previous[seed]=-1
            queue.append(seed)
        while queue:
            i=queue.popleft()
            for other in adj[i]:
                if previous[other]==-2:
                    previous[other]=i;queue.append(other)
        for i,obj in enumerate(objects):
            if previous[i]==-2:continue
            nodes=[]
            distances=[]
            step=i
            while True:
                nodes.append(ids[step])
                if previous[step]==-1:
                    distances.append(gap(objects[step],root))
                    break
                distances.append(gap(objects[step],objects[previous[step]]))
                step=previous[step]
            nodes.append(rootid)
            assert len(nodes)==len(distances)+1
            paths[obj["id"]][rootid]={"root_id":rootid,
                                      "kind":"DIRECT" if len(nodes)==2 else "INDIRECT_OBJECT_CHAIN",
                                      "nodes":nodes,"distances_m":distances}
            affiliations[obj["id"]].add(rootid)
    components=[]
    component_for={}
    island_for={}
    floor={}
    wall={}
    for member_set in components_unsorted.values():
        members=sorted(member_set)
        anchor=min(members)
        rep=byid[anchor]
        componentid=f"component_{rep['room_uid']}_{anchor}"
        components.append({"id":componentid,"members":members})
        repaff=affiliations[anchor]
        has_floor=any(byid[x]["kind"]=="floor" for x in repaff)
        has_wall=any(byid[x]["kind"]=="wall" for x in repaff)
        for oid in members:
            component_for[oid]=componentid
            floor[oid]="YES" if has_floor else ("NO" if complete else "UNKNOWN")
            wall[oid]="YES" if has_wall else ("NO" if known and walls_known else "UNKNOWN")
            if has_floor and wall[oid]=="NO":
                island_for[oid]=f"island_{rep['room_uid']}_{anchor}"
    components.sort(key=lambda c:c["id"])
    rejected_structural=[]
    for i,a in enumerate(roots):
        for b in roots[i+1:]:
            dg=gap(a,b)
            if dg<connection_distance:
                rejected_structural.append({"source":a["id"],"target":b["id"],
                                            "distance_m":dg,"reason":"STRUCTURAL_ROOT_RELAY_FORBIDDEN"})
    objects_out=[]
    for obj in sorted(objects,key=lambda x:x["id"]):
        oid=obj["id"]
        ps=[paths[oid][k] for k in sorted(paths[oid])]
        failures=[{"root_id":r,"direct_bbox_gap_m":direct_gaps[oid][r],
                   "reason":"NON_OBJECT_OR_ROBOT_RELAY_FORBIDDEN" if not allowed[idx[oid]]
                            else "NO_PATH_IN_DECLARED_OBJECT_GRAPH" if known else "UNKNOWN_INCOMPLETE_OBSERVATIONS"}
                  for r in sorted(direct_gaps[oid]) if r not in paths[oid]]
        objects_out.append({"entity_id":oid,"relay_allowed":allowed[idx[oid]],
            "component_id":component_for.get(oid),
            "floor_state":floor.get(oid,"UNKNOWN"),
            "any_wall_state":wall.get(oid,"UNKNOWN"),
            "paths":ps,"rejected_or_unobserved_root_paths":failures})
    packet=dict(metric="WORLD_AABB_3D_EUCLIDEAN",comparison="STRICT_LESS_THAN",
      threshold_m=connection_distance,roots_are_endpoints_only=True,
      closed_world_within_declared_snapshot=known,
      negative_scope="DECLARED_NATIVE_ENTITIES_ONLY_UNSEEN_RELAYS_NOT_CERTIFIED",
      components=components,objects=objects_out,
      rejected_structural_relays=rejected_structural[:10000],
      rejected_structural_relay_count=len(rejected_structural),
      rejected_structural_examples_complete=len(rejected_structural)<=10000)
    result_entities=copy.deepcopy(entities)
    for e in result_entities:
        if e["kind"]=="object":
            eid=e["id"]
            o=next(x for x in objects_out if x["entity_id"]==eid)
            e["root_affiliations"]=sorted(affiliations[eid])
            e["floor_member"]=o["floor_state"]=="YES"
            e["upper_member"]=o["floor_state"]=="NO"
            e["island_id"]=island_for.get(eid)
        else:
            e["root_affiliations"]=[]
            # roots have no Island ID, Floor/UP membership is set by C++.
            e["floor_member"]=e["kind"]=="floor"
            e["upper_member"]=False
    return packet,result_entities,complete
