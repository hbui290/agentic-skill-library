"""Self-check for the update pipeline (stdlib only, synthetic fixtures).

Run: python3 scripts/test_pipeline.py  -> prints PASS/FAIL per case, exit 1 on any FAIL.
Never touches the real library: every case works in its own temp dir.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_skills as U
import build_librarian_index as B

RESULTS = []

def case(name):
    def deco(fn):
        RESULTS.append((name, fn))
        return fn
    return deco

def mkskill(base, *rel_files):
    for rf in rel_files:
        p = os.path.join(base, rf)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("content of " + rf)

# --- F#4: dir_hash must survive dangling symlinks -------------------------
@case("dir_hash tolerates dangling symlink")
def _(tmp):
    d = os.path.join(tmp, "s"); mkskill(d, "s/SKILL.md")
    os.symlink(os.path.join(tmp, "nonexistent"), os.path.join(d, "s", "dead-link"))
    U.dir_hash(os.path.join(d, "s"))  # must not raise

# --- F#11: dir_hash path/content delimiter --------------------------------
@case("dir_hash separates path from content")
def _(tmp):
    a = os.path.join(tmp, "a"); os.makedirs(a)
    with open(os.path.join(a, "ab"), "w") as f: f.write("c")
    b = os.path.join(tmp, "b"); os.makedirs(b)
    with open(os.path.join(b, "a"), "w") as f: f.write("bc")
    assert U.dir_hash(a) != U.dir_hash(b), "hash collision between {ab:c} and {a:bc}"

# --- F#5: declared layout dir missing -> no root fallback ------------------
@case("collect_source_skills: missing skills/ dir yields nothing")
def _(tmp):
    repo = os.path.join(tmp, "repo")
    mkskill(repo, "docs/guide.md", "tests/test_x.py")
    got = U.collect_source_skills(repo, "skills-subdir")
    assert got == [], f"fell back to repo root: {[n for n, _ in got]}"

# --- F#6: container-of-containers recurses to real leafs -------------------
@case("collect_source_skills: nested containers reach leaf skills")
def _(tmp):
    repo = os.path.join(tmp, "repo")
    mkskill(repo,
            "skills/plain/SKILL.md",
            "skills/toolkit/alpha/SKILL.md",
            "skills/toolkit/beta/SKILL.md",
            "skills/mega/group/deep/SKILL.md")
    names = sorted(n for n, _ in U.collect_source_skills(repo, "skills-subdir"))
    assert names == ["alpha", "beta", "deep", "plain"], names

# --- F#2: install_skill must not raise on existing destination -------------
@case("install_skill skips existing destination")
def _(tmp):
    old = U.skills_dir
    try:
        U.skills_dir = tmp
        src = os.path.join(tmp, "_src"); mkskill(src, "_src/SKILL.md")
        assert U.install_skill("clean-code", src) is not None
        assert U.install_skill("clean-code", src) is None  # second time: skip, no raise
    finally:
        U.skills_dir = old

# --- F#1: replace_skill_dir is atomic-ish ----------------------------------
@case("replace_skill_dir keeps old version when copy fails")
def _(tmp):
    dest = os.path.join(tmp, "skill"); mkskill(dest, "skill/SKILL.md")
    good = os.path.join(tmp, "good"); mkskill(good, "good/SKILL.md")
    with open(os.path.join(good, "good", "SKILL.md"), "w") as f: f.write("v2")
    U.replace_skill_dir(os.path.join(good, "good"), os.path.join(dest, "skill"))
    assert open(os.path.join(dest, "skill", "SKILL.md")).read() == "v2"
    bad = os.path.join(tmp, "bad", "b"); os.makedirs(bad)
    os.symlink("/nonexistent-target-xyz", os.path.join(bad, "dead"))
    try:
        U.replace_skill_dir(bad, os.path.join(dest, "skill"))
    except Exception:
        pass  # failure allowed — but old content must survive
    assert open(os.path.join(dest, "skill", "SKILL.md")).read() == "v2", "old version lost"

# --- F#3: run_cmd takes argv list, no shell interpretation ------------------
@case("run_cmd uses argv list without shell")
def _(tmp):
    ok, out = U.run_cmd(["echo", "hi; touch " + os.path.join(tmp, "pwned")])
    assert ok and "hi; touch" in out
    assert not os.path.exists(os.path.join(tmp, "pwned")), "shell interpreted the argument!"

# --- DRY: shared flat_name rule --------------------------------------------
@case("flat_name_map slugs duplicate basenames")
def _(tmp):
    m = U.flat_name_map(["a/x/skill1", "b/y/skill1", "c/z/skill2"])
    assert m["a/x/skill1"] == "a-x-skill1" and m["b/y/skill1"] == "b-y-skill1"
    assert m["c/z/skill2"] == "skill2"

# --- F#7: namespaced entry must not inherit another skill's metadata --------
@case("make_entry: no metadata bleed into namespaced skill")
def _(tmp):
    mkskill(tmp, "eng/misc/foo__srcB/SKILL.md")
    with open(os.path.join(tmp, "eng/misc/foo__srcB/SKILL.md"), "w") as f:
        f.write('---\nname: foo__srcB\ndescription: "own desc"\n---\n')
    upstream = {"foo": {"description": "FOO UPSTREAM", "category": "cat-foo",
                        "risk": "dangerous", "source": "community", "date_added": "2020-01-01"}}
    e = B.make_entry("eng/misc/foo__srcB", tmp, upstream,
                     {"foo__srcB": {"owner": "srcB", "also": []}}, {}, {}, {}, {"foo__srcB": 1})
    assert e["description"] == "own desc"
    assert e["risk"] != "dangerous" and e["category_fine"] != "cat-foo", e

# --- F#9: dangling canonical is nulled --------------------------------------
@case("make_entry: dangling canonical -> null")
def _(tmp):
    mkskill(tmp, "eng/misc/real/SKILL.md")
    with open(os.path.join(tmp, "eng/misc/real/SKILL.md"), "w") as f:
        f.write('---\nname: real\ndescription: "d"\n---\n')
    e = B.make_entry("eng/misc/real", tmp, {}, {}, {}, {"real": "ghost-skill"}, {}, {"real": 1},
                     valid_names={"real"})
    assert e["canonical"] is None

# --- F#12: missing SKILL.md gets a synthetic searchable description ----------
@case("make_entry: synthetic description when SKILL.md missing")
def _(tmp):
    mkskill(tmp, "eng/misc/SPDD/1-research.md", "eng/misc/SPDD/2-spec.md")
    e = B.make_entry("eng/misc/SPDD", tmp, {}, {}, {}, {}, {}, {"SPDD": 1})
    assert "1-research.md" in e["description"], e["description"]


def main():
    failed = 0
    for name, fn in RESULTS:
        tmp = tempfile.mkdtemp()
        try:
            fn(tmp)
            print(f"PASS  {name}")
        except Exception as ex:
            failed += 1
            print(f"FAIL  {name} — {type(ex).__name__}: {ex}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{len(RESULTS) - failed}/{len(RESULTS)} passed")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
