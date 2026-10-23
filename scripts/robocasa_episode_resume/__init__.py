"""Episode reuse with bounded plans; no model or simulator imports.

At most 100,000 Episodes/records per invocation and logical slots 0..99,999
are accepted before any range is materialized. A recovery document is limited
to 64 MiB. These resource bounds never relax original evidence validation.
"""

MAX_EPISODES = 100_000
MAX_RECOVERY_BYTES = 64 * 1024 * 1024


def bounded_episode_index(value, field="logical_episode_index"):
    if type(value) is not int or not 0 <= value < MAX_EPISODES:
        raise ValueError(f"{field} must be an integer in [0, {MAX_EPISODES})")
    return value


def bounded_episode_count(value, field="episodes"):
    if type(value) is not int or not 0 < value <= MAX_EPISODES:
        raise ValueError(f"{field} must be an integer in [1, {MAX_EPISODES}]")
    return value


def bounded_records(values, field="records"):
    output = []
    for value in values:
        if len(output) >= MAX_EPISODES:
            raise ValueError(f"{field} exceeds the {MAX_EPISODES}-record resource limit")
        output.append(value)
    return output
