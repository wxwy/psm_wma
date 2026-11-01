"""Real EGL selection/attestation logic with CPU driver and sysfs doubles."""

import copy
import ctypes

import pytest
from cosmos_framework.evaluation.robocasa_v2.wire import receive, send
from cosmos_framework.simulation.robocasa import render_devices as module

from tools.v3.eval_v2_production_tests import worker_test


@pytest.fixture(autouse=True)
def restore_render_environment(monkeypatch):
    for key, value in {
        "MUJOCO_GL": "osmesa",
        "PYOPENGL_PLATFORM": "osmesa",
        "CUDA_VISIBLE_DEVICES": "",
        "MUJOCO_EGL_DEVICE_ID": "stale-before-configure",
    }.items():
        monkeypatch.setenv(key, value)


def plan():
    return {
        "backend": "egl",
        "server_gpu_id": 4,
        "render_gpu_id": 6,
        "expected_device": {
            "gpu_id": 6,
            "uuid": "GPU-six",
            "pci_bus_id": "0000:66:00.0",
        },
    }


class Driver:
    def __init__(self):
        self.rows = [
            {
                "egl_device_index": 0,
                "handle": 6006,
                "pci_bus_id": "0000:66:00.0",
                "device_node": "/dev/dri/renderD6",
            },
            {
                "egl_device_index": 1,
                "handle": 4004,
                "pci_bus_id": "0000:44:00.0",
                "device_node": "/dev/dri/renderD4",
            },
        ]
        self.current_handle = 6006
        self.queries = []

    def inventory(self):
        self.queries.append("inventory")
        return copy.deepcopy(self.rows)

    def current(self):
        self.queries.append("current_context")
        return next(
            copy.deepcopy(v) for v in self.rows if v["handle"] == self.current_handle
        )


def test_permuted_egl_enumeration_is_resolved_by_pci_not_gpu_number():
    driver = Driver()
    proof = module.configure(plan(), api=driver)
    assert proof["egl_device_index"] == 0 and proof["render_gpu_id"] == 6
    assert module.os.environ["MUJOCO_EGL_DEVICE_ID"] == "0"
    assert module.os.environ["CUDA_VISIBLE_DEVICES"] == ""
    assert (
        proof["physical_identity_verified"] is True
        and proof["context_verified"] is False
    )
    assert module.verify_current(proof, api=driver)["context_verified"] is True
    assert driver.queries == [
        "inventory",
        "current_context",
        "inventory",
    ]  # No context-creation API.


@pytest.mark.parametrize("failure", ["missing", "ambiguous", "unidentifiable"])
def test_missing_or_ambiguous_physical_identity_never_falls_back_to_an_ordinal(failure):
    driver = Driver()
    if failure == "missing":
        driver.rows = driver.rows[1:]
    if failure == "ambiguous":
        driver.rows.append({**driver.rows[0], "egl_device_index": 2, "handle": 6666})
    if failure == "unidentifiable":
        driver.rows[0]["pci_bus_id"] = None
    with pytest.raises(RuntimeError, match="one provable EGL device"):
        module.configure(plan(), api=driver)
    assert "MUJOCO_EGL_DEVICE_ID" not in module.os.environ


def test_actual_current_context_on_the_server_gpu_is_rejected():
    driver = Driver()
    proof = module.configure(plan(), api=driver)
    driver.current_handle = 4004
    with pytest.raises(RuntimeError, match="different physical GPU"):
        module.verify_current(proof, api=driver)


@pytest.mark.parametrize(
    "field,value",
    [
        ("physical_identity_verified", False),
        ("physical_identity_verified", "true"),
        ("egl_device_index", True),
        ("context_verified", False),
    ],
)
def test_root_handshake_rejects_unproven_or_malformed_device_flags(field, value):
    proof = module.verify_current(module.configure(plan(), api=Driver()), api=Driver())
    proof[field] = value
    with pytest.raises(ValueError, match="unproven"):
        module.validate_proof(proof, plan(), context=True)


def test_wrong_role_or_uuid_cannot_be_reported_as_the_assigned_render_device():
    proof = module.configure(plan(), api=Driver())
    proof["render_gpu_id"] = 4
    with pytest.raises(ValueError, match="assigned roles"):
        module.validate_proof(proof, plan())
    proof = module.configure(plan(), api=Driver())
    proof["actual_device"]["uuid"] = "GPU-wrong"
    with pytest.raises(ValueError, match="unproven"):
        module.validate_proof(proof, plan())


def test_osmesa_never_loads_an_egl_or_cuda_driver(monkeypatch):
    monkeypatch.setattr(
        module, "EGLDevices", lambda: pytest.fail("OSMesa cannot load EGL")
    )
    cfg = {
        "backend": "osmesa",
        "server_gpu_id": 4,
        "render_gpu_id": None,
        "expected_device": None,
    }
    proof = module.configure(cfg)
    assert module.validate_proof(proof, cfg) == proof
    assert (
        module.os.environ["MUJOCO_GL"]
        == module.os.environ["PYOPENGL_PLATFORM"]
        == "osmesa"
    )
    assert module.os.environ["CUDA_VISIBLE_DEVICES"] == ""
    assert "MUJOCO_EGL_DEVICE_ID" not in module.os.environ


@pytest.mark.parametrize("pci", ["00000000:AF:00.0", "0000:af:00.0"])
def test_pci_domain_and_case_are_normalized(pci):
    assert module.normalize_pci(pci) == "0000:af:00.0"


@pytest.mark.parametrize("pci", [None, "GPU-6", "0000:af:00", "10000000:00:00.0"])
def test_malformed_pci_identity_is_rejected(pci):
    with pytest.raises(ValueError):
        module.normalize_pci(pci)


class Function:
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *args):
        return self.callback(*args)


def test_real_ctypes_inventory_and_current_display_parser_with_fake_functions(
    monkeypatch,
):
    class Library:
        eglGetProcAddress = Function(lambda *a: 0)
        eglGetCurrentDisplay = Function(lambda: 111)
        eglGetCurrentContext = Function(lambda: 222)
        eglGetError = Function(lambda: 0x3000)

    handles = [6006, 4004, 9999]

    def query_devices(capacity, devices, count):
        ctypes.cast(count, ctypes.POINTER(ctypes.c_int))[0] = len(handles)
        if capacity:
            for i, h in enumerate(handles):
                devices[i] = h
        return 1

    def query_string(device, attribute):
        return {6006: b"/dev/dri/renderD6", 4004: b"/dev/dri/renderD4"}.get(device)

    def query_display(display, attribute, result):
        assert display == 111 and attribute == 0x322C
        ctypes.cast(result, ctypes.POINTER(ctypes.c_ssize_t))[0] = 6006
        return 1

    calls = {
        b"eglQueryDevicesEXT": query_devices,
        b"eglQueryDeviceStringEXT": query_string,
        b"eglQueryDisplayAttribEXT": query_display,
    }
    monkeypatch.setattr(module.ctypes, "CDLL", lambda name: Library())
    monkeypatch.setattr(
        module.EGLDevices, "_function", lambda self, name, *a: calls[name]
    )
    original = module.Path.resolve

    def resolve(path, *a, **kw):
        mapping = {
            "/sys/class/drm/renderD6/device": "0000:66:00.0",
            "/sys/class/drm/renderD4/device": "0000:44:00.0",
        }
        if str(path) in mapping:
            return module.Path("/synthetic/sysfs") / mapping[str(path)]
        return original(path, *a, **kw)

    monkeypatch.setattr(module.Path, "resolve", resolve)
    driver = module.EGLDevices()
    inventory = driver.inventory()
    assert inventory[0]["pci_bus_id"] == "0000:66:00.0"
    assert inventory[2]["pci_bus_id"] is None
    proof = module.configure(plan(), api=driver)
    assert module.verify_current(proof, api=driver)["context_verified"] is True


@pytest.mark.parametrize("wrong_context", [False, True])
def test_production_worker_attests_device_then_context_before_policy(
    tmp_path, monkeypatch, wrong_context
):
    configuration = worker_test.cfg(tmp_path)
    configuration["rendering"] = plan()
    driver = Driver()
    if wrong_context:
        driver.current_handle = 4004
    monkeypatch.setattr(module, "EGLDevices", lambda: driver)
    channel, thread, errors, env = worker_test.run_worker(configuration, monkeypatch)
    try:
        ready = receive(channel)
        assert ready["kind"] == "READY"
        assert ready["rendering"]["render_gpu_id"] == 6
        assert ready["rendering"]["egl_device_index"] == 0
        send(
            channel,
            {
                "nonce": "cpu",
                "request_id": "start",
                "op": "start_episode",
                "attempt": configuration["_test_attempt"],
                "grant": configuration["_test_grant"],
            },
        )
        assert receive(channel)["state"] == "ENV_READY"
        send(channel, {"nonce": "cpu", "request_id": "initialize", "op": "initialize"})
        reply = receive(channel)
        if wrong_context:
            assert (
                reply["kind"] == "FATAL" and "different physical GPU" in reply["error"]
            )
        else:
            assert reply["rendering"]["context_verified"] is True
            assert reply["initial_success"] is True
            send(channel, {"nonce": "cpu", "request_id": "close", "op": "close"})
            assert receive(channel)["closed"] is True
        assert env.resets == 1 and not env.actions
    finally:
        channel.close()
        thread.join(2)
    assert not thread.is_alive()
    assert bool(errors) is wrong_context
