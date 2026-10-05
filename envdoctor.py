#!/usr/bin/env python3
"""envdoctor: diagnose .env files against .env.example (missing / extra / empty / leaked secrets)."""
import argparse, json, re, subprocess, sys

__version__ = "0.1.0"

LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*(.*)$")
SECRET_KEY = re.compile(r"(SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE|API_?KEY|ACCESS_?KEY|CREDENTIAL)", re.I)
SECRET_VALUE = re.compile(r"^(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{30,})")
PLACEHOLDER = re.compile(r"^(|changeme|change_me|your[-_ ].*|xxx+|\*+|<.*>|\$\{.*\}|todo|example|secret|password|dummy|placeholder)$", re.I)


def parse(text):
    """Return ({key: value}, [(lineno, raw)] of unparsable lines). Handles export, quotes, inline comments."""
    env, bad = {}, []
    for n, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = LINE.match(raw)
        if not m:
            bad.append((n, raw))
            continue
        key, val = m.group(1), m.group(2).strip()
        if val and val[0] in "\"'" and val.count(val[0]) >= 2:
            val = val[1:val.index(val[0], 1)]
        else:
            val = re.split(r"\s+#", val, 1)[0].strip()
        env[key] = val
    return env, bad


def looks_like_secret(key, value):
    if PLACEHOLDER.match(value):
        return False
    return bool(SECRET_VALUE.match(value)) or (bool(SECRET_KEY.search(key)) and len(value) >= 16)


def diagnose(env, example, example_bad=(), env_bad=()):
    """Return a list of findings: {level: error|warn, code, key, message}."""
    f = []
    add = lambda lvl, code, key, msg: f.append({"level": lvl, "code": code, "key": key, "message": msg})
    for k in example:
        if k not in env:
            add("error", "missing", k, f"{k} is in .env.example but missing from .env")
    for k in env:
        if k not in example:
            add("warn", "extra", k, f"{k} is in .env but not documented in .env.example")
    for k, v in env.items():
        if k in example and v == "" and example[k] != "":
            add("warn", "empty", k, f"{k} is empty in .env (example has a default)")
    for k, v in example.items():
        if looks_like_secret(k, v):
            add("error", "leaked-secret", k, f"{k} in .env.example looks like a real secret; use a placeholder")
    for n, raw in list(example_bad) + list(env_bad):
        add("warn", "syntax", None, f"line {n}: cannot parse {raw.strip()[:40]!r}")
    return f


def is_ignored(path):
    r = subprocess.run(["git", "check-ignore", "-q", path], capture_output=True)
    return r.returncode == 0 if r.returncode in (0, 1) else None  # None: not a git repo


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--env", default=".env")
    p.add_argument("--example", default=".env.example")
    p.add_argument("--strict", action="store_true", help="treat warnings as errors")
    p.add_argument("--json", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    a = p.parse_args(argv)
    try:
        example, eb = parse(open(a.example, encoding="utf-8").read())
        env, nb = parse(open(a.env, encoding="utf-8").read())
    except OSError as e:
        print(f"envdoctor: {e}", file=sys.stderr)
        return 2
    findings = diagnose(env, example, eb, nb)
    if is_ignored(a.env) is False:
        findings.append({"level": "error", "code": "not-ignored", "key": None,
                         "message": f"{a.env} is not in .gitignore - it could be committed"})
    if a.json:
        print(json.dumps(findings, indent=2))
    else:
        for x in findings:
            print(f"{'✗' if x['level'] == 'error' else '!'} {x['message']}")
        if not findings:
            print("✓ .env looks healthy")
    bad = any(x["level"] == "error" or a.strict for x in findings)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
