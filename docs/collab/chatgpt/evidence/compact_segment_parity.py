import os, sys, time, json, random
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
os.environ.setdefault('COSMOS_DEVICE', 'cpu')
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
os.environ['LD_LIBRARY_PATH'] = ''
SRC = '/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework'
sys.path.insert(0, SRC)

import torch
THREADS = int(os.environ.get('EXP_THREADS', '8'))
torch.set_num_threads(THREADS)
print('torch', torch.__version__, 'threads', torch.get_num_threads(), flush=True)

from dataclasses import asdict, is_dataclass

INDEX = '/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1'
CACHE = '/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window'
SOURCE = '/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic'
EDGE = '/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID'
T = 16
DIGEST = 'compact_parity_v1'

from cosmos_framework.data.generator.action.datasets.robocasa_verified_index import VerifiedExactWindowIndex
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_cache import RoboCasaExactWindowCacheCatalog
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_policy import CorrectedRoboCasaPolicyContract
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_source import RoboCasaExactWindowSourceReader
from cosmos_framework.data.generator.action.datasets.robocasa_exact_window_cached_sft import RoboCasaExactWindowCachedDataset
from cosmos_framework.data.generator.action.datasets.action_sft_dataset import ActionSFTDataset
from cosmos_framework.data.generator.action.utils.transforms import ActionTransformPipeline
from cosmos_framework.data.generator.action.utils.cached_pixel_geometry import (
    CachedGeometryResize, is_pixel_shape_proxy,
)
from cosmos_framework.model.generator.mot.local_memory_segment import SegmentIdentity
from cosmos_framework.model.generator.mot.robocasa_exact_window_local import (
    ExactWindowLocalCatalog, ExactWindowRankPlanner, ExactWindowSegmentProducer,
    ExactWindowSegmentRequest,
)
from cosmos_framework.trainer.matched_no_ttt import MatchedNoTTTWindow
from cosmos_framework.trainer.no_ttt_cpu_loader import NoTTTCpuLoader
from cosmos_framework.utils.no_ttt_loader_profile import LoaderProfile
from cosmos_framework.trainer.local_memory_grouped import collate_grouped_native_batch


class _StubModel:
    class _Cfg:
        local_memory_enabled = False
    config = _Cfg()
    net = type('_Net', (), {})()

    def named_parameters(self):
        return iter(())


def snap_rng():
    return (random.getstate(), torch.random.get_rng_state().clone())


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)


def rng_eq(a, b):
    return a[0] == b[0] and bool(torch.equal(a[1], b[1]))


def restore_rng(state):
    random.setstate(state[0])
    torch.random.set_rng_state(state[1])


def deep_eq(a, b):
    if isinstance(a, torch.Tensor) or isinstance(b, torch.Tensor):
        return (
            isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor)
            and a.shape == b.shape and bool(torch.equal(a, b))
        )
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(deep_eq(a[k], b[k]) for k in a)
    if is_dataclass(a) and is_dataclass(b) and type(a) is type(b):
        return deep_eq(asdict(a), asdict(b))
    return type(a) is type(b) and a == b


def _short(v, limit=120):
    if isinstance(v, torch.Tensor):
        return f'tensor(shape={tuple(v.shape)},dtype={v.dtype},head={v.flatten()[:8].tolist()})'
    if isinstance(v, str):
        return f'str({v[:limit]!r})'
    if isinstance(v, (list, tuple)):
        items = [_short(x) for x in v[:3]]
        return f'{type(v).__name__}(len={len(v)},head={items})'
    return f'{type(v).__name__}({v!r})'


def build_raw():
    return RoboCasaExactWindowCachedDataset(cat, source_reader, contract)


def build_sft(raw):
    transform = ActionTransformPipeline(
        tokenizer_config=TOK_CFG,
        cfg_dropout_rate=0.1,
        max_action_dim=contract.max_action_dim,
        append_viewpoint_info=True,
        append_duration_fps_timestamps=True,
        append_resolution_info=True,
        append_idle_frames=True,
        format_prompt_as_json=True,
    )
    if raw.compact_cached_video:
        transform.video_resize = CachedGeometryResize(transform.video_resize, tuple(raw._canvas_geometry))
    return ActionSFTDataset(raw, transform, resolution=None)


def main():
    global cat, source_reader, contract, TOK_CFG
    t0 = time.perf_counter()
    vi = VerifiedExactWindowIndex.open(INDEX, cache_root=CACHE, source_root=SOURCE, verify_files=False)
    cat = RoboCasaExactWindowCacheCatalog(CACHE, verified_index=vi)
    contract = CorrectedRoboCasaPolicyContract.from_cache_catalog(cat)
    source_reader = RoboCasaExactWindowSourceReader(cat, SOURCE, verified_index=vi)
    print('catalog+contract+source_reader', round(time.perf_counter() - t0, 2), 's', flush=True)

    TOK_CFG = {
        '_target_': 'cosmos_framework.data.generator.processors.build_processor_lazy',
        'repository': None, 'revision': None, 'tokenizer_type': EDGE,
    }

    os.environ['PSM_V3_COMPACT_CACHED_VIDEO'] = '0'
    raw0 = build_raw()
    sft0 = build_sft(raw0)
    os.environ['PSM_V3_COMPACT_CACHED_VIDEO'] = '1'
    raw1 = build_raw()
    sft1 = build_sft(raw1)
    print('built compact0=', raw0.compact_cached_video, 'compact1=', raw1.compact_cached_video, flush=True)

    cat0 = ExactWindowLocalCatalog(sft0, ttt_tbptt_steps=T)
    cat1 = ExactWindowLocalCatalog(sft1, ttt_tbptt_steps=T)
    producer0 = ExactWindowSegmentProducer(cat0, config_digest=DIGEST)
    producer1 = ExactWindowSegmentProducer(cat1, config_digest=DIGEST)
    print('catalogs+producers ok; episodes', len(cat0.episodes), flush=True)

    results = {'threads': THREADS, 'task1': {}, 'task2': {}}

    # ================= Task 1: real terminal partial segment =================
    partial = [ep for ep in cat0.episodes if (ep.window_count % T) != 0]
    print('terminal-partial episodes:', len(partial), flush=True)
    picked = partial[:3]
    for ep0 in picked:
        uid = ep0.uid
        ep1 = cat1.by_uid[uid]
        cursor = ep0.segment_count - 1
        valid_count = ep0.window_count - cursor * T
        assert 1 <= valid_count < T
        assert ep0 == ep1

        def mk_request(ep):
            identity = SegmentIdentity(
                slot_id=0, episode_id=ep.uid, category=ep.task_class, cursor=cursor,
                segment_id=0, source_digest=ep.source_digest, training_stream_end=True,
            )
            return ExactWindowSegmentRequest(ep, identity, binding_epoch=0, valid_count=valid_count)

        request0 = mk_request(ep0)
        request1 = mk_request(ep1)
        set_seed(2000 + ep0.window_count % 1000)
        b0 = snap_rng()
        seg0 = producer0.produce(request0)
        a0 = snap_rng()
        set_seed(2000 + ep0.window_count % 1000)
        b1 = snap_rng()
        seg1 = producer1.produce(request1)
        a1 = snap_rng()
        tensor_keys = [
            'consumer_visual_summary', 'consumer_valid', 'consumer_step',
            'evidence_visual_summary_prev', 'evidence_executed_action_prev',
            'evidence_valid', 'evidence_source_step', 'slot_id',
        ]
        t_eq = {k: bool(torch.equal(getattr(seg0, k), getattr(seg1, k))) for k in tensor_keys}
        meta_eq = (
            seg0.episode_id == seg1.episode_id and seg0.category == seg1.category
            and seg0.segment_provenance == seg1.segment_provenance
        )
        per_consumer = {}
        for index in range(valid_count):
            p0, p1 = seg0.consumer_payload[0][index], seg1.consumer_payload[0][index]
            keys = sorted(set(p0) | set(p1))
            row = {}
            for k in keys:
                if k not in p0 or k not in p1:
                    row[k] = 'missing'
                    continue
                if k == 'video':
                    v0, v1 = p0[k], p1[k]
                    row['video'] = (
                        tuple(v0.shape) == tuple(v1.shape)
                        and bool(torch.count_nonzero(v0) == 0) and bool(torch.count_nonzero(v1) == 0)
                    )
                    row['video_proxy0'] = is_pixel_shape_proxy(v0)
                    row['video_proxy1'] = is_pixel_shape_proxy(v1)
                else:
                    row[k] = deep_eq(p0[k], p1[k])
            per_consumer[str(index)] = row
        all_payload_eq = all(
            v is True for row in per_consumer.values()
            for k, v in row.items() if k not in ('video_proxy0', 'video_proxy1')
        )
        entry = {
            'episode_uid': ep0.uid,
            'window_count': ep0.window_count,
            'segment_count': ep0.segment_count,
            'cursor': cursor,
            'valid_count': valid_count,
            'training_stream_end': True,
            'tensor_fields_eq': t_eq,
            'meta_eq': meta_eq,
            'payload_eq_all_consumers': all_payload_eq,
            'per_consumer': per_consumer,
            'rng_before_eq': rng_eq(b0, b1),
            'rng_after_eq': rng_eq(a0, a1),
            'video_shape': tuple(seg0.consumer_payload[0][0]['video'].shape),
        }
        results['task1'][ep0.uid] = entry
        print(
            f'T1 {ep0.uid} wc={ep0.window_count} seg={ep0.segment_count} cursor={cursor} '
            f'valid={valid_count} tensor={all(t_eq.values())} payload={all_payload_eq} '
            f'rng_after={entry["rng_after_eq"]}', flush=True
        )

    # ================= Task 2: full No-TTT CPU data path =================
    planner0 = ExactWindowRankPlanner(cat0, rank=0, world_size=4, b_stream=8, active_ga=4, seed=0)
    planner1 = ExactWindowRankPlanner(cat1, rank=0, world_size=4, b_stream=8, active_ga=4, seed=0)

    window0 = MatchedNoTTTWindow(_StubModel(), planner0)
    window1 = MatchedNoTTTWindow(_StubModel(), planner1)
    window0.begin()
    window1.begin()
    plan0, plan1 = window0.plan, window1.plan
    plan_eq = plan0 == plan1
    print('frozen plan equality:', plan_eq, 'members', len(plan0.members), 'counts', plan0.member_counts, flush=True)
    results['task2']['frozen_plan_eq'] = bool(plan_eq)
    results['task2']['member_counts'] = list(plan0.member_counts)
    results['task2']['profile'] = 'workers=1 prefetch=1 persistent=True timeout=120'

    profile = LoaderProfile(workers=1, prefetch_factor=1, persistent_workers=True, timeout_s=120.0)
    loader0 = NoTTTCpuLoader(producer0, profile)
    loader1 = NoTTTCpuLoader(producer1, profile)
    loader0.begin(plan0)
    loader1.begin(plan1)

    set_seed(777)
    before0 = snap_rng()
    set_seed(777)
    before1 = snap_rng()

    members = {}
    text_diag = {}
    for member in range(4):
        mem_state = snap_rng()
        segs0 = tuple(loader0.materialize(r) for r in plan0.members[member])
        payloads0, pos0 = window0.pack(segs0)
        batch0 = collate_grouped_native_batch(payloads0)
        state_after0 = snap_rng()
        restore_rng(mem_state)
        segs1 = tuple(loader1.materialize(r) for r in plan1.members[member])
        payloads1, pos1 = window1.pack(segs1)
        batch1 = collate_grouped_native_batch(payloads1)
        state_after1 = snap_rng()
        pos_eq = tuple(pos0) == tuple(pos1)
        rng_consumed_eq = rng_eq(state_after0, state_after1)
        key_agg = {}
        diff_samples = {'ai_caption': [], 'text_token_ids': []}
        for i, (p0, p1) in enumerate(zip(payloads0, payloads1, strict=True)):
            for k in set(p0) | set(p1):
                if k == 'video':
                    v0, v1 = p0.get(k), p1.get(k)
                    eq = (
                        v0 is not None and v1 is not None
                        and tuple(v0.shape) == tuple(v1.shape)
                        and bool(torch.count_nonzero(v0) == 0) and bool(torch.count_nonzero(v1) == 0)
                    )
                else:
                    eq = k in p0 and k in p1 and deep_eq(p0[k], p1[k])
                key_agg.setdefault(k, []).append(bool(eq))
                if member == 0 and k in diff_samples and not eq:
                    diff_samples[k].append((i, _short(p0.get(k)), _short(p1.get(k))))
        payloads_eq = {k: all(v) for k, v in key_agg.items()}
        bkeys = sorted(set(batch0) | set(batch1))
        batch_eq = {}
        for k in bkeys:
            if k not in batch0 or k not in batch1:
                batch_eq[k] = 'missing'
                continue
            if k == 'video':
                batch_eq['video'] = bool(deep_eq(batch0[k], batch1[k]))
                s0 = [is_pixel_shape_proxy(v) for s in batch0[k] for v in (s if isinstance(s, list) else [s])]
                s1 = [is_pixel_shape_proxy(v) for s in batch1[k] for v in (s if isinstance(s, list) else [s])]
                batch_eq['video_proxy0'] = bool(all(s0))
                batch_eq['video_proxy1'] = bool(all(s1))
            else:
                batch_eq[k] = bool(deep_eq(batch0[k], batch1[k]))
        members[str(member)] = {
            'positions_eq': pos_eq,
            'rng_consumed_eq': rng_consumed_eq,
            'payload_count': len(payloads0),
            'payloads_eq': payloads_eq,
            'collated_batch_eq': batch_eq,
            'batch_all': all(v is True for k, v in batch_eq.items() if k not in ('video_proxy0', 'video_proxy1')),
            'batch_video_eq': batch_eq.get('video'),
            'batch_video_proxy0': batch_eq.get('video_proxy0'),
            'batch_video_proxy1': batch_eq.get('video_proxy1'),
            'batch_video_latent_count': len(batch0.get('video_latent', ())),
        }
        text_diag[str(member)] = {
            'ai_caption_diffs': diff_samples['ai_caption'][:3],
            'text_token_ids_diffs': diff_samples['text_token_ids'][:3],
        }
        print(
            f'T2 member {member}: pos={pos_eq} rng_consumed={rng_consumed_eq} n={len(payloads0)} '
            f'payload_all={all(payloads_eq.values())} '
            f'batch_all={all(v is True for k, v in batch_eq.items() if k not in ("video_proxy0", "video_proxy1"))} '
            f'video_proxy0={batch_eq.get("video_proxy0")} video_proxy1={batch_eq.get("video_proxy1")}',
            flush=True,
        )
        window0.member += 1
        window1.member += 1

    after0 = snap_rng()
    after1 = snap_rng()
    results['task2']['rng_before_eq'] = rng_eq(before0, before1)
    results['task2']['rng_after_eq'] = rng_eq(after0, after1)
    results['task2']['members'] = members
    results['task2']['text_diffs'] = text_diag

    window0.finish()
    window1.finish()
    metrics0 = loader0.finish()
    metrics1 = loader1.finish()
    loader0.close()
    loader1.close()
    results['task2']['loader_metrics0'] = {k: v for k, v in metrics0.items() if isinstance(v, (int, float, str))}
    results['task2']['loader_metrics1'] = {k: v for k, v in metrics1.items() if isinstance(v, (int, float, str))}

    with open('/tmp/compact_segment_parity_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print('\n=== DONE: /tmp/compact_segment_parity_results.json ===', flush=True)


if __name__ == '__main__':
    main()
