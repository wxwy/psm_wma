"""Fail-closed static primitives for the R09-B2 P4 interpreter contract.

This module deliberately contains no project imports, environment mutation, or
child-process launch.  It analyses already-materialized copy-only payloads.
"""

from __future__ import annotations

import ast
import hashlib
import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


PYTHON_NATIVE_APIS = {
    "ctypes.CDLL": "ctypes",
    "ctypes.PyDLL": "ctypes",
    "ctypes.cdll.LoadLibrary": "ctypes",
    "ctypes.pydll.LoadLibrary": "ctypes",
    "torch.ops.load_library": "torch_ops",
    "torch.utils.cpp_extension.load": "torch_cpp_extension",
    "torch.utils.cpp_extension.load_inline": "torch_cpp_extension",
}
FORBIDDEN_DYNAMIC_NAMES = {
    "__import__", "eval", "exec", "getattr", "globals", "locals",
}
FORBIDDEN_DYNAMIC_FQNS = FORBIDDEN_DYNAMIC_NAMES | {f"builtins.{name}" for name in FORBIDDEN_DYNAMIC_NAMES}
ELF_DYNAMIC_LOADER_SYMBOLS = {"dlopen", "dlmopen"}
ELF_FORBIDDEN_LOADER_SYMBOLS = {"dlsym"}


class ProvenanceError(ValueError):
    """Static provenance cannot be established under the frozen grammar."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _span_sha256(source: bytes, node: ast.AST) -> str:
    lines = source.splitlines(keepends=True)
    start, end = getattr(node, "lineno", 0), getattr(node, "end_lineno", 0)
    if not start or not end or start > end:
        raise ProvenanceError("native-load AST node lacks a complete source span")
    return hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest()


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def _literal_path(node: ast.AST) -> str:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str) or not node.value:
        raise ProvenanceError("native-load target must be a non-empty string literal")
    return node.value


def _imports(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname is None:
                    aliases[alias.name.split(".", 1)[0]] = alias.name.split(".", 1)[0]
                else:
                    aliases[alias.asname] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module is None or any(alias.name == "*" for alias in node.names):
                raise ProvenanceError("star/relative import is not allowed in native-load analysed source")
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _resolve_fqn(node: ast.AST, aliases: Mapping[str, str]) -> str | None:
    dotted = _dotted_name(node)
    if dotted is None:
        return None
    head, *tail = dotted.split(".")
    return ".".join((aliases.get(head, head), *tail))


def _assert_no_alias_rebinding(tree: ast.Module, aliases: Mapping[str, str]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                if isinstance(target, ast.Name) and target.id in aliases:
                    raise ProvenanceError(f"native-load import alias is rebound: {target.id}")


def _assert_no_native_callable_forwarding(tree: ast.Module, aliases: Mapping[str, str]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        fqn = _resolve_fqn(node.value, aliases)
        if fqn in PYTHON_NATIVE_APIS:
            raise ProvenanceError("native-load callable may not be forwarded through an alias/container")


def _assert_no_forbidden_dynamic_aliases(tree: ast.Module, aliases: Mapping[str, str]) -> None:
    if set(aliases.values()) & FORBIDDEN_DYNAMIC_FQNS:
        raise ProvenanceError("forbidden dynamic constructor is imported through an alias")
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _resolve_fqn(node.value, aliases) in FORBIDDEN_DYNAMIC_FQNS:
            raise ProvenanceError("forbidden dynamic constructor is reassigned")


def analyse_python_native_loads(source_path: Path, staging_root: Path) -> list[dict[str, str]]:
    """Return complete direct native-load records or raise on an unsafe form."""
    source_path, staging_root = source_path.resolve(), staging_root.resolve()
    if not source_path.is_relative_to(staging_root) or source_path.suffix != ".py" or not source_path.is_file():
        raise ProvenanceError("analysed Python source is not an approved staged .py payload")
    source = source_path.read_bytes()
    try:
        tree = ast.parse(source, filename=str(source_path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise ProvenanceError(f"cannot parse staged Python source: {source_path}") from exc
    aliases = _imports(tree)
    _assert_no_alias_rebinding(tree, aliases)
    _assert_no_native_callable_forwarding(tree, aliases)
    _assert_no_forbidden_dynamic_aliases(tree, aliases)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    rows: list[dict[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        parent = parents.get(node)
        if any(isinstance(parent, ast.FunctionDef) for parent in _ancestor_nodes(parent, parents)):
            continue
        fqn = _resolve_fqn(node.func, aliases)
        direct = _dotted_name(node.func)
        if fqn in FORBIDDEN_DYNAMIC_FQNS:
            raise ProvenanceError(f"dynamic Python construction is forbidden: {fqn}")
        if fqn not in PYTHON_NATIVE_APIS:
            if direct and (direct.startswith("ctypes.") or direct.startswith("torch.ops.") or direct.startswith("torch.utils.cpp_extension.")):
                raise ProvenanceError(f"unknown native-load API: {fqn}")
            continue
        if fqn.startswith("torch.utils.cpp_extension"):
            if not node.args:
                raise ProvenanceError("cpp_extension native-load call has no literal name")
            target = _literal_path(node.args[0])
        else:
            if not node.args:
                raise ProvenanceError("native-load call has no target")
            target = _literal_path(node.args[0])
        rows.append({
            "source_relative_path": source_path.relative_to(staging_root).as_posix(),
            "source_span_sha256": _span_sha256(source, node),
            "resolved_fqn": fqn,
            "mechanism": PYTHON_NATIVE_APIS[fqn],
            "target_rule": "literal",
            "canonical_target": target,
            "sha256": hashlib.sha256(target.encode()).hexdigest(),
        })
    return sorted(rows, key=lambda row: tuple(row.values()))


def _ancestor_nodes(node: ast.AST | None, parents: Mapping[ast.AST, ast.AST]) -> Iterable[ast.AST]:
    while node is not None:
        yield node
        node = parents.get(node)


def analyse_all_staged_python(staging_root: Path, approved_payloads: Iterable[str]) -> list[dict[str, str]]:
    """Analyse every approved Python payload; missing/excluded files fail closed."""
    root = staging_root.resolve()
    payloads = sorted(set(approved_payloads))
    discovered = sorted(path.relative_to(root).as_posix() for path in root.rglob("*.py") if path.is_file())
    if payloads != discovered:
        raise ProvenanceError("approved staged Python manifest does not exactly cover all .py payloads")
    rows: list[dict[str, str]] = []
    for relative in payloads:
        rows.extend(analyse_python_native_loads(root / relative, root))
    return sorted(rows, key=lambda row: tuple(row.values()))


def analyse_wrapper_contract(staging_root: Path, approved_payloads: Iterable[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Summarise one-parameter native wrappers and their literal invocations.

    This deliberately separate pass lets unused generic definitions exist while
    requiring every actual use to have a frozen concrete target.
    """
    root = staging_root.resolve()
    payloads = sorted(set(approved_payloads))
    trees: dict[str, tuple[bytes, ast.Module]] = {}
    for relative in payloads:
        path = root / relative
        source = path.read_bytes()
        try:
            trees[relative] = (source, ast.parse(source, filename=str(path)))
        except (SyntaxError, UnicodeDecodeError) as exc:
            raise ProvenanceError("cannot parse wrapper-contract source") from exc
    wrappers: dict[str, tuple[str, bytes, ast.FunctionDef, int, str]] = {}
    for relative, (source, tree) in trees.items():
        aliases = _imports(tree)
        module = relative[:-3].replace("/", ".")
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.decorator_list or node.args.vararg or node.args.kwarg or node.args.kwonlyargs or node.args.defaults or len(node.args.args) != 1:
                continue
            calls = [item.value for item in node.body if isinstance(item, ast.Expr) and isinstance(item.value, ast.Call)]
            if len(calls) != 1 or len(node.body) != 1:
                continue
            call = calls[0]
            callee = _resolve_fqn(call.func, aliases)
            if isinstance(call.func, ast.Name) and callee == call.func.id:
                callee = f"{module}.{callee}"
            if callee is None or len(call.args) != 1:
                continue
            if not isinstance(call.args[0], ast.Name):
                continue
            names = [arg.arg for arg in node.args.args]
            if call.args[0].id not in names:
                continue
            fqn = f"{module}.{node.name}"
            wrappers[fqn] = (relative, source, node, names.index(call.args[0].id), callee)
    def expand(name: str, seen: set[str]) -> tuple[str, str]:
        if name in seen:
            raise ProvenanceError("wrapper call graph contains a cycle")
        if name in PYTHON_NATIVE_APIS:
            return name, "direct_native"
        if name not in wrappers:
            raise ProvenanceError("wrapper calls an unadmitted native-load target")
        return (*expand(wrappers[name][4], seen | {name}),)
    definitions = [{"wrapper_fqn": name, "defining_source_relative_path": relative, "definition_span_sha256": _span_sha256(source, node), "parameter_index": str(index), "callee_fqn": callee, "effect_kind": expand(name, set())[1]} for name, (relative, source, node, index, callee) in wrappers.items()]
    invocations: list[dict[str, str]] = []
    for relative, (source, tree) in trees.items():
        aliases, module = _imports(tree), relative[:-3].replace("/", ".")
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            parent = parents.get(node)
            inside_definition = False
            while parent is not None:
                if isinstance(parent, ast.FunctionDef):
                    inside_definition = True; break
                parent = parents.get(parent)
            if not isinstance(node, ast.Call) or inside_definition:
                continue
            name = _resolve_fqn(node.func, aliases)
            if isinstance(node.func, ast.Name) and name == node.func.id:
                name = f"{module}.{name}"
            if name not in wrappers:
                continue
            if len(node.args) != 1:
                raise ProvenanceError("wrapper invocation arity differs from frozen definition")
            target = _literal_path(node.args[0]); final, _ = expand(name, set())
            invocations.append({"invocation_source_relative_path": relative, "invocation_span_sha256": _span_sha256(source, node), "wrapper_chain": name, "final_fqn": final, "target_rule": "literal", "canonical_target": target, "sha256": hashlib.sha256(target.encode()).hexdigest()})
    return sorted(definitions, key=lambda row: tuple(row.values())), sorted(invocations, key=lambda row: tuple(row.values()))


def analyse_python_contract(staging_root: Path, approved_payloads: Iterable[str]) -> dict[str, list[dict[str, str]]]:
    """Derive the complete direct-and-wrapper runtime native-load contract."""
    root = staging_root.resolve()
    payloads = sorted(set(approved_payloads))
    direct: list[dict[str, str]] = []
    for relative in payloads:
        direct.extend(analyse_python_native_loads(root / relative, root))
    definitions, invocations = analyse_wrapper_contract(root, payloads)
    allowlist = sorted([*direct, *invocations], key=lambda row: tuple(row.values()))
    return {"direct_python": sorted(direct, key=lambda row: tuple(row.values())), "wrapper_definitions": definitions, "wrapper_invocations": invocations, "native_runtime_allowlist": allowlist}


def verify_native_load_contract(contract: Mapping[str, Any]) -> bool:
    """Recompute all candidate sets; the request may not author its own allowlist."""
    required = {"staging_root", "python_payloads", "closure_objects", "elf_loader_records", "direct_python", "wrapper_definitions", "wrapper_invocations", "native_runtime_allowlist"}
    if set(contract) != required or not isinstance(contract["staging_root"], str) or not isinstance(contract["python_payloads"], list):
        return False
    try:
        python = analyse_python_contract(Path(contract["staging_root"]), contract["python_payloads"])
        elf = analyse_elf_loader_symbols(contract["closure_objects"], contract["elf_loader_records"])
    except (OSError, ProvenanceError, TypeError):
        return False
    expected_allowlist = [*python["native_runtime_allowlist"], *elf]
    return (exact_allowlist(python["direct_python"], contract["direct_python"])
            and exact_allowlist(python["wrapper_definitions"], contract["wrapper_definitions"])
            and exact_allowlist(python["wrapper_invocations"], contract["wrapper_invocations"])
            and exact_allowlist(expected_allowlist, contract["native_runtime_allowlist"]))


def analyse_elf_loader_symbols(objects: Iterable[Mapping[str, Any]], records: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Validate verifier-supplied ELF symbol/callsite records for the full closure.

    The caller supplies records extracted by the root-owned ELF parser.  This
    pure schema gate deliberately rejects `dlsym` and every unpaired loader
    symbol before any child can start.
    """
    object_rows = list(objects)
    object_paths = {row.get("canonical_path") for row in object_rows if isinstance(row.get("canonical_path"), str)}
    if len(object_paths) != len(object_rows):
        raise ProvenanceError("native closure contains duplicate or malformed objects")
    expected: list[dict[str, str]] = []
    seen_records: set[tuple[str, str]] = set()
    for row in object_rows:
        path, symbols = row.get("canonical_path"), row.get("undefined_symbols")
        if not isinstance(path, str) or not isinstance(symbols, list) or not all(isinstance(symbol, str) for symbol in symbols):
            raise ProvenanceError("ELF object lacks a frozen undefined-symbol list")
        if ELF_FORBIDDEN_LOADER_SYMBOLS & set(symbols):
            raise ProvenanceError("ELF dlsym/function-pointer loader path is forbidden")
        for symbol in sorted(ELF_DYNAMIC_LOADER_SYMBOLS & set(symbols)):
            matching = [record for record in records if record.get("component_path") == path and record.get("symbol") == symbol]
            if len(matching) != 1:
                raise ProvenanceError("ELF loader symbol has no unique frozen literal target")
            record = matching[0]
            if (not isinstance(record.get("target"), str) or not record["target"]
                    or record.get("target_rule") not in {"literal", "origin_literal"}
                    or not isinstance(record.get("target_sha256"), str)):
                raise ProvenanceError("ELF loader record is not a frozen literal target")
            key = (path, symbol)
            if key in seen_records:
                raise ProvenanceError("duplicate ELF loader record")
            seen_records.add(key)
            expected.append({"component_path": path, "symbol": symbol, "target_rule": record["target_rule"], "canonical_target": record["target"], "sha256": record["target_sha256"]})
    if any((record.get("component_path"), record.get("symbol")) not in seen_records for record in records):
        raise ProvenanceError("ELF loader record is not backed by a closure object symbol")
    return expected


def exact_allowlist(expected: Iterable[Mapping[str, Any]], supplied: object) -> bool:
    """Require canonical JSON-equivalent expected/supplied native load sets."""
    if not isinstance(supplied, list):
        return False
    canonical = lambda rows: sorted(json_dumps(row) for row in rows)
    return canonical(expected) == canonical(supplied)


def json_dumps(value: Mapping[str, Any]) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def lexical_interpreter(path: Path) -> dict[str, str]:
    """Bind the executable launcher without replacing it by its resolved target."""
    lexical = Path(os.path.abspath(path))
    if not lexical.is_file():
        raise ProvenanceError("lexical interpreter launcher is missing")
    resolved = lexical.resolve()
    if not resolved.is_file():
        raise ProvenanceError("lexical interpreter target is missing")
    return {"path": str(lexical), "sha256": sha256_file(lexical), "realpath": str(resolved), "realpath_sha256": sha256_file(resolved)}
