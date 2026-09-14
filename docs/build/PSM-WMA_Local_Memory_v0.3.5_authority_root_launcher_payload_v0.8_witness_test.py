"""CPU-only temporary witnesses; never imports or invokes payload main()."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("witness", HERE / "PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7_witness_core.py")
assert SPEC and SPEC.loader
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)
PAYLOAD_SPEC = importlib.util.spec_from_file_location("payload", HERE / "PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py")
assert PAYLOAD_SPEC and PAYLOAD_SPEC.loader
P = importlib.util.module_from_spec(PAYLOAD_SPEC)
PAYLOAD_SPEC.loader.exec_module(P)


class WitnessTest(unittest.TestCase):
    def test_native_git_commondir_witness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            admin = root / ".git"
            W.require_commondir_absent(admin)
            (admin / "commondir").write_text("../common\n")
            with self.assertRaises(W.WitnessFailure): W.require_commondir_absent(admin)

    def test_native_git_worktree_add_remove_witness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"; clean = root / "clean"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            (root / "x").write_text("x")
            subprocess.run(["/usr/bin/git", "-C", str(root), "add", "x"], check=True)
            env = {**os.environ, "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x", "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x"}
            subprocess.run(["/usr/bin/git", "-C", str(root), "commit", "-qm", "x"], check=True, env=env)
            old_root, old_clean, old_formal = P.ROOT, P.CLEAN, P.FORMAL
            try:
                P.ROOT, P.CLEAN = str(root), str(clean)
                P.FORMAL = subprocess.check_output(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                snapshot = P.route_snapshot()
                P.check_route(snapshot)
                subprocess.run([*P.PREFIX, "-C", P.ROOT, "worktree", "add", "--detach", P.CLEAN, P.FORMAL], check=True, env=P.ENV)
                P.check_route(snapshot)
                self.assertTrue(clean.is_dir())
                subprocess.run([*P.PREFIX, "-C", P.ROOT, "worktree", "remove", "--force", P.CLEAN], check=True, env=P.ENV)
                P.check_route(snapshot)
                self.assertFalse(clean.exists())
            finally:
                if "snapshot" in locals():
                    for fd in (snapshot[1], snapshot[3]):
                        if P.fd_is_open(fd): os.close(fd)
                P.ROOT, P.CLEAN, P.FORMAL = old_root, old_clean, old_formal
    def test_path_identity_and_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / "backing"; path.write_bytes(b"x"); path.chmod(0o600)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                W.verify_handoff_path(path, fd, fd)
                path.chmod(0o644)
                with self.assertRaises(W.WitnessFailure): W.verify_handoff_path(path, fd, fd)
            finally: os.close(fd)

    def test_payload_handoff_same_and_different_fd(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            old = P.CLEAN; P.CLEAN = raw
            try:
                if P.fd_is_open(3): os.close(3)
                P.handoff(b"same", ".same", 3, P.digest(b"same"))
                self.assertEqual(os.pread(3, 4, 0), b"same")
                if P.fd_is_open(4): os.close(4)
                P.handoff(b"other", ".other", 4, P.digest(b"other"))
                self.assertEqual(os.pread(4, 5, 0), b"other")
                os.close(3); os.close(4)
            finally: P.CLEAN = old

    def test_replacement_and_commondir(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / "backing"; path.write_bytes(b"x"); path.chmod(0o600)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                replacement = root / "replacement"; replacement.write_bytes(b"x"); replacement.chmod(0o600); os.replace(replacement, path)
                with self.assertRaises(W.WitnessFailure): W.verify_handoff_path(path, fd, fd)
            finally: os.close(fd)
            admin = root / ".git"; admin.mkdir(); W.require_commondir_absent(admin); (admin / "commondir").write_text("../common")
            with self.assertRaises(W.WitnessFailure): W.require_commondir_absent(admin)

    def test_add_failure_classifier(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            clean = Path(raw) / "clean"
            self.assertEqual(W.classify_add_failure(clean, False), "FAIL")
            clean.mkdir()
            self.assertEqual(W.classify_add_failure(clean, False), "ROLLBACK_INCOMPLETE")
            self.assertEqual(W.classify_add_failure(clean, True), "ROLLBACK_INCOMPLETE")

    def test_payload_capture_owned_missing_is_rollback_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            old = P.CLEAN; P.CLEAN = str(Path(raw) / "missing")
            try:
                with self.assertRaisesRegex(P.Stop, "ROLLBACK_INCOMPLETE"):
                    P.capture_owned()
            finally:
                P.CLEAN = old

    def test_payload_fixed_owner_abi_survives_low_fd_occupancy(self) -> None:
        pid = os.fork()
        if pid == 0:
            try:
                with tempfile.TemporaryDirectory() as raw:
                    for target in (*P.BACKING_FDS, P.GIT_TARGET_FD, P.PARENT_OWNER_FD, P.BOOTSTRAP_FD, P.CLEAN_OWNER_FD):
                        if P.fd_is_open(target): os.close(target)
                    for target in P.BACKING_FDS:
                        source = os.open("/dev/null", os.O_RDONLY | os.O_CLOEXEC)
                        if source != target:
                            os.dup2(source, target, inheritable=False); os.close(source)
                    parent = P.bind_owner(os.open(raw, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC), P.PARENT_OWNER_FD)
                    os.mkdir("leaf", 0o700, dir_fd=parent)
                    clean = P.bind_owner(os.open("leaf", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=parent), P.CLEAN_OWNER_FD)
                    seen = []
                    def consume(target):
                        seen.append((target, P.fd_is_open(P.GIT_TARGET_FD), P.fd_is_open(P.PARENT_OWNER_FD), P.fd_is_open(P.CLEAN_OWNER_FD)))
                    P.consume_leaf(clean, consume)
                    ok = (parent == 7 and clean == 9 and seen == [("/proc/self/fd/6/.", True, True, True)] and not P.fd_is_open(6))
                    os.close(clean); os.close(parent)
                    os._exit(0 if ok else 21)
            except BaseException:
                os._exit(22)
        _, status = os.waitpid(pid, 0)
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 0)

    def test_payload_post_add_validation_releases_fd6_per_git_child(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); old_root, old_clean, old_run, old_consume = P.ROOT, P.CLEAN, P.run, P.consume_leaf
            parent = clean = -1
            try:
                P.ROOT, P.CLEAN = str(root), str(root / "clean")
                for fd in (P.GIT_TARGET_FD, P.PARENT_OWNER_FD, P.BOOTSTRAP_FD, P.CLEAN_OWNER_FD):
                    if P.fd_is_open(fd): os.close(fd)
                parent = P.bind_owner(os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC), P.PARENT_OWNER_FD)
                os.mkdir("clean", 0o700, dir_fd=parent)
                clean = P.bind_owner(os.open("clean", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=parent), P.CLEAN_OWNER_FD)
                value = os.fstat(clean); owned = (value, clean, parent, "clean", os.fstat(parent))
                leases = []
                def observe(fd, action):
                    leases.append(("before", P.fd_is_open(P.GIT_TARGET_FD)))
                    result = old_consume(fd, action)
                    leases.append(("after", P.fd_is_open(P.GIT_TARGET_FD)))
                    return result
                def fake_run(_s, *argv, **_kwargs):
                    self.assertTrue(P.fd_is_open(P.GIT_TARGET_FD))
                    return (P.FORMAL + "\n").encode() if argv[0] == "rev-parse" else b""
                P.consume_leaf, P.run = observe, fake_run
                P.assert_worktree(None, owned)
                self.assertEqual(leases, [("before", False), ("after", False), ("before", False), ("after", False)])
            finally:
                P.consume_leaf, P.run = old_consume, old_run
                for fd in (clean, parent):
                    if fd >= 0 and P.fd_is_open(fd): os.close(fd)
                P.ROOT, P.CLEAN = old_root, old_clean

    def test_payload_preexec_failure_retains_owner_identity_for_cleanup(self) -> None:
        pid = os.fork()
        if pid == 0:
            try:
                with tempfile.TemporaryDirectory() as raw:
                    for fd in range(3, 10):
                        if P.fd_is_open(fd): os.close(fd)
                    for target in P.BACKING_FDS:
                        source = os.open("/dev/null", os.O_RDONLY | os.O_CLOEXEC)
                        if source != target:
                            os.dup2(source, target, inheritable=True); os.close(source)
                    parent = P.bind_owner(os.open(raw, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC), P.PARENT_OWNER_FD)
                    os.mkdir("clean", 0o700, dir_fd=parent)
                    clean = P.bind_owner(os.open("clean", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=parent), P.CLEAN_OWNER_FD)
                    owned = (os.fstat(clean), clean, parent, "clean", os.fstat(parent))
                    P.CLEAN = raw
                    for raw_bytes, name, target in ((b"a", ".a", 3), (b"b", ".b", 4), (b"c", ".c", 5)):
                        P.handoff(raw_bytes, name, target, P.digest(raw_bytes))
                    try: P.prepare_exec_fds()
                    except P.Stop: os._exit(34)
                    try: P.assert_owned_identity(owned)
                    except P.Stop: os._exit(35)
                    try: os.execve("/definitely/not/a/psm-executable", ["x"], {})
                    except FileNotFoundError: pass
                    else: os._exit(36)
                    try:
                        P.cleanup(None, owned, ())
                    except P.Stop as error:
                        ok = str(error) == "ROLLBACK_INCOMPLETE"
                    else:
                        ok = False
                    os._exit(0 if ok and not os.get_inheritable(7) and not os.get_inheritable(9) else 31)
            except BaseException:
                os._exit(32)
        _, status = os.waitpid(pid, 0)
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 0)

    def test_payload_close_to_keep_ignores_proc_enumeration_fd(self) -> None:
        pid = os.fork()
        if pid == 0:
            try:
                for target in (3, 4, 5):
                    fd = os.open("/dev/null", os.O_RDONLY)
                    if fd != target:
                        os.dup2(fd, target)
                        os.close(fd)
                extra = os.open("/dev/null", os.O_RDONLY)
                if extra in {3, 4, 5}:
                    os._exit(10)
                P.close_to_keep({3, 4, 5})
                os._exit(0 if P.durable_fds() == {3, 4, 5} else 11)
            except BaseException:
                os._exit(12)
        _, status = os.waitpid(pid, 0)
        self.assertTrue(os.WIFEXITED(status))
        self.assertEqual(os.WEXITSTATUS(status), 0)

    def test_payload_cleanup_is_non_destructive_for_owner_and_foreign_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"; clean = root / "clean"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            (root / "x").write_text("x")
            env = {**os.environ, "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x", "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x"}
            subprocess.run(["/usr/bin/git", "-C", str(root), "add", "x"], check=True)
            subprocess.run(["/usr/bin/git", "-C", str(root), "commit", "-qm", "x"], check=True, env=env)
            old_root, old_clean, old_formal = P.ROOT, P.CLEAN, P.FORMAL
            try:
                P.ROOT, P.CLEAN = str(root), str(clean)
                P.FORMAL = subprocess.check_output(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                snapshot = P.route_snapshot()
                paths = (P.CLEAN, P.CLEAN + "/.authority-root.index", str(root / "evidence"), str(root / "pending"))
                owned = P.add_and_capture(snapshot)
                self.assertEqual(owned[1:3], (P.CLEAN_OWNER_FD, P.PARENT_OWNER_FD))
                self.assertFalse(P.fd_is_open(P.GIT_TARGET_FD))
                with self.assertRaisesRegex(P.Stop, "ROLLBACK_INCOMPLETE"):
                    P.cleanup(snapshot, owned, paths)
                self.assertTrue(clean.is_dir())
                self.assertIn("worktree " + str(clean), P.run(snapshot, "worktree", "list", "--porcelain").decode().splitlines())
                displaced = Path(raw) / "displaced"
                os.rename(clean, displaced)
                clean.mkdir()
                (clean / "foreign-marker").write_text("B")
                with self.assertRaisesRegex(P.Stop, "ROLLBACK_INCOMPLETE"):
                    P.cleanup(snapshot, owned, paths)
                self.assertEqual((clean / "foreign-marker").read_text(), "B")
            finally:
                for fd in (P.CLEAN_OWNER_FD, P.PARENT_OWNER_FD):
                    if P.fd_is_open(fd): os.close(fd)
                for fd in (snapshot[1], snapshot[3]):
                    if P.fd_is_open(fd): os.close(fd)
                P.ROOT, P.CLEAN, P.FORMAL = old_root, old_clean, old_formal

    def test_leaf_remove_behavior_is_diagnostic_fixture_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"; clean = root / "clean"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            (root / "x").write_text("x")
            env = {**os.environ, "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x", "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x"}
            subprocess.run(["/usr/bin/git", "-C", str(root), "add", "x"], check=True)
            subprocess.run(["/usr/bin/git", "-C", str(root), "commit", "-qm", "x"], check=True, env=env)
            old_root, old_clean, old_formal = P.ROOT, P.CLEAN, P.FORMAL
            try:
                P.ROOT, P.CLEAN = str(root), str(clean)
                P.FORMAL = subprocess.check_output(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                snapshot = P.route_snapshot()
                owned = P.add_and_capture(snapshot)
                self.assertEqual(owned[1:3], (P.CLEAN_OWNER_FD, P.PARENT_OWNER_FD))
                self.assertFalse(P.fd_is_open(P.GIT_TARGET_FD))
                _, fd, _, _, _ = owned
                try: saved = os.dup(6)
                except OSError: saved = None
                try:
                    os.dup2(fd, 6); os.set_inheritable(6, True)
                    result = subprocess.run([*P.PREFIX, "-C", P.ROOT, "worktree", "remove", "--force", "/proc/self/fd/6/."], env=P.ENV, close_fds=True, pass_fds=(6,))
                finally:
                    if saved is None: os.close(6)
                    else: os.dup2(saved, 6); os.close(saved)
                self.assertIn(result.returncode, (0, 128))
                self.assertEqual(clean.exists(), result.returncode != 0)
            finally:
                for fd in (P.CLEAN_OWNER_FD, P.PARENT_OWNER_FD):
                    if P.fd_is_open(fd): os.close(fd)
                for fd in (snapshot[1], snapshot[3]):
                    if P.fd_is_open(fd): os.close(fd)
                P.ROOT, P.CLEAN, P.FORMAL = old_root, old_clean, old_formal

    def test_payload_add_nonzero_and_post_add_route_drift_are_rollback_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"; clean = root / "clean"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            (root / "x").write_text("x")
            env = {**os.environ, "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x", "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x"}
            subprocess.run(["/usr/bin/git", "-C", str(root), "add", "x"], check=True)
            subprocess.run(["/usr/bin/git", "-C", str(root), "commit", "-qm", "x"], check=True, env=env)
            old_root, old_clean, old_formal, old_run = P.ROOT, P.CLEAN, P.FORMAL, P.run
            try:
                P.ROOT, P.CLEAN = str(root), str(clean)
                P.FORMAL = subprocess.check_output(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
                snapshot = P.route_snapshot()
                clean.mkdir()
                (clean / "occupied").write_text("x")
                with self.assertRaisesRegex(P.Stop, "ROLLBACK_INCOMPLETE"):
                    P.add_and_capture(snapshot)
                self.assertEqual((clean / "occupied").read_text(), "x")
                (clean / "occupied").unlink()
                clean.rmdir()
                def add_then_drift(state, *argv, **kwargs):
                    result = old_run(state, *argv, **kwargs)
                    (root / ".git" / "commondir").write_text("../foreign\n")
                    P.check_route(state)
                    return result
                P.run = add_then_drift
                with self.assertRaisesRegex(P.Stop, "ROLLBACK_INCOMPLETE"):
                    P.add_and_capture(snapshot)
                commondir = root / ".git" / "commondir"
                if commondir.exists() or commondir.is_symlink():
                    commondir.unlink()
            finally:
                for fd in (P.CLEAN_OWNER_FD, P.PARENT_OWNER_FD):
                    if P.fd_is_open(fd): os.close(fd)
                for fd in (snapshot[1], snapshot[3]):
                    if P.fd_is_open(fd): os.close(fd)
                P.run = old_run
                P.ROOT, P.CLEAN, P.FORMAL = old_root, old_clean, old_formal

    def test_payload_add_then_git_valid_foreign_replacement_is_never_owned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "repo"
            clean = root / "clean"
            displaced = Path(raw) / "displaced"
            subprocess.run(["/usr/bin/git", "init", "-q", str(root)], check=True)
            (root / "x").write_text("x")
            env = {**os.environ, "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x", "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x"}
            subprocess.run(["/usr/bin/git", "-C", str(root), "add", "x"], check=True)
            subprocess.run(["/usr/bin/git", "-C", str(root), "commit", "-qm", "x"], check=True, env=env)
            old_root, old_clean, old_formal, old_run = P.ROOT, P.CLEAN, P.FORMAL, P.run
            try:
                P.ROOT, P.CLEAN = str(root), str(clean)
                P.FORMAL = subprocess.check_output(
                    ["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], text=True
                ).strip()
                snapshot = P.route_snapshot()

                def add_then_replace(state, *argv, **kwargs):
                    result = old_run(state, *argv, **kwargs)
                    if argv[:2] == ("worktree", "add"):
                        os.rename(clean, displaced)
                        shutil.copytree(displaced, clean)
                        self.assertEqual(
                            subprocess.check_output(
                                ["/usr/bin/git", "-C", str(clean), "rev-parse", "HEAD"], text=True
                            ).strip(),
                            P.FORMAL,
                        )
                    return result

                P.run = add_then_replace
                with self.assertRaisesRegex(P.Stop, "ROLLBACK_INCOMPLETE"):
                    P.add_and_capture(snapshot)
                self.assertTrue(clean.is_dir())
                self.assertTrue((clean / ".git").exists())
            finally:
                for fd in (P.CLEAN_OWNER_FD, P.PARENT_OWNER_FD):
                    if P.fd_is_open(fd): os.close(fd)
                for fd in (snapshot[1], snapshot[3]):
                    if P.fd_is_open(fd): os.close(fd)
                P.run = old_run
                P.ROOT, P.CLEAN, P.FORMAL = old_root, old_clean, old_formal

    def test_fd_and_cleanup_classifiers(self) -> None:
        W.require_exact_fd_set({3, 4, 5})
        with self.assertRaises(W.WitnessFailure): W.require_exact_fd_set({0, 3, 4, 5})
        self.assertEqual(W.classify_cleanup(True, True, False), "CLEANUP_PASS")
        self.assertEqual(W.classify_cleanup(False, True, False), "ROLLBACK_INCOMPLETE")
        self.assertEqual(W.classify_cleanup(True, False, False), "ROLLBACK_INCOMPLETE")
        self.assertEqual(W.classify_cleanup(True, True, True), "ROLLBACK_INCOMPLETE")


if __name__ == "__main__": unittest.main()
