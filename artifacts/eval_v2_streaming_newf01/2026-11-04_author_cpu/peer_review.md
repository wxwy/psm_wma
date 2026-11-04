# Required independent read-only NEW-F01 review

Reviewer: `/root/review_requirements` (another agent, per Root AGENTS.md).
Formal Root: `551b03621507dde52303f54290d4fea89d66e8da`.
Unchanged Child: `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e`.

Source review found no new reachable HIGH/MED in this narrow delta. Completion
excludes only its own reservation, charges all other pending promises, checks
RSS and each owned GPU, and commits the version/pending transition under the
same short lock. Measurement stays outside the lock, optimistic retries are
bounded, and exception cleanup checks the original reservation object's identity.
Config/Manifest/M-B/Runtime/Child are unchanged. This is measured accounting at
admission/completion, not a hardware memory hard limit or H100 performance proof.

Reviewer independently read the original failed new-green JUnit and stderr:
33 PASS/2 FAIL, external adjacent os_fixture.py missing, Server exit2 before the
budget target; that failed evidence is retained. No assertion or production
change was used to repair this recorder invocation mistake.

Reviewer independently checked os-green raw JUnit, process/error/cleanup records:
off/required 2 unique PASS, both Slots active, distinct Episode and Slot IDs,
BLOCKED_RESOURCE startup RSS, zero result.json/valid Core, partial/unqualified
results, pending0/activeJobs0, one Server + two Sim owned processes with matching
closed receipts, no remaining PIDs, proof hashes valid. Outsider excluded from
ownership and alive at the assertion. SIGTERM/BrokenPipe cleanup diagnostics
remain preserved; this is safe failure containment, not graceful error-free exit.

os-green is pre-freeze working-delta evidence with production bytes identical to
the Formal Pair. The untracked test is fingerprinted under its absolute path
in source_before/after.json; this corrects the reviewer's initial relative-key
lookup miss. The later clean Formal Pair run is separately archived in
formal-targeted, 35/35 PASS, source unchanged. Reviewer did not execute tests,
modify/commit files, or claim GPT/DS acceptance.
