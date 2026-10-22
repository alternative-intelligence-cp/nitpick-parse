# meta/roadmap/0.0/0.0.2_tools/facts.sh -- re-derives `0.0.2.md` §1, block 0b. Sourced after `../tools/env.sh`.
# Writes only under `$A/facts`, and removes it. Reads the compiler's tree with `git show` alone. Prints no path above
# the repository: every scratch path is cut to its name.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T2=$REPO/meta/roadmap/0.0/0.0.2_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2 3 4; do python3 -B "$TL/apply.py" "$d" 0.0.2 $s > /dev/null; done
cut_paths() { sed -e "s|$d/||g" -e "s|$F/||g" -e "s|$REPO/||g"; }

# §1.1 -- the tree it starts from: cycle 0.0.1's record
echo "§1.1 harness holds: $(git -C "$REPO" ls-files harness | tr '\n' ' ')"
echo "§1.1 the stub says: $(cd "$REPO" && python3 -B harness/run.py)"
echo "§1.1 nitpick.toml's [[test]] entries: $(grep -c '^\[\[test\]\]' "$REPO/nitpick.toml"); ci.yml's steps: $(python3 -B -c '
import yaml, sys
print(len(yaml.safe_load(open(sys.argv[1]))["jobs"]["build"]["steps"]))' "$REPO/.github/workflows/ci.yml")"

# §1.2 -- the manifest's schema is the compiler's `schema_allows` at the pin, table for table, key for key
git -C "$NPK_TREE" show "$PIN:npkg/manifest.npk" > "$F/manifest.npk"
python3 -B - "$F/manifest.npk" "$d/harness" <<'PY'
import re, sys
sys.path.insert(0, sys.argv[2])
import manifest
body = open(sys.argv[1], encoding="utf-8").read()
fn = body[body.index("func:schema_allows"):]
fn = fn[:fn.index("\n};")]
theirs, any_key, sec = {}, set(), None
for line in fn.split("\n"):
    m = re.search(r'text_eq\(section, "([^"]+)"\)\) \{ pass true; \}', line)
    if m:
        any_key.add(m.group(1)); continue
    m = re.search(r'text_eq\(section, "([^"]+)"\)', line)
    if m:
        sec = m.group(1); theirs[sec] = set(); continue
    m = re.search(r'text_eq\(key, "([^"]+)"\)', line)
    if m:
        theirs[sec].add(m.group(1))
same = theirs == manifest.SCHEMA and any_key == manifest.ANY_KEY
print("§1.2 schema_allows at the pin: %d tables with keys (%s) and %s with any key; harness/manifest.py: %s"
      % (len(theirs), " ".join(sorted(theirs)), " ".join(sorted(any_key)), "the same" if same else "DIFFERENT"))
PY

# §1.3 -- the stage names: BUILD_REFERENCE.md §7.1's table at the pin, and this library's two
git -C "$NPK_TREE" show "$PIN:meta/specs/BUILD_REFERENCE.md" > "$F/br.md"
python3 -B - "$F/br.md" "$d/harness" <<'PY'
import re, sys
sys.path.insert(0, sys.argv[2])
import manifest
t = open(sys.argv[1], encoding="utf-8").read()
sec = t[t.index("### 7.1 Test targets"):t.index("### 7.2")] if "### 7.2" in t else t[t.index("### 7.1 Test targets"):]
names = set(re.findall(r"^\| `([a-z]+)`", sec, re.M))
ours = manifest.KNOWN_STAGES - names
print("§1.3 the stages §7.1's table names: %d (%s); the harness adds %s"
      % (len(names), " ".join(sorted(names)), " ".join(sorted(ours))))
PY

# §1.4 -- the two scans' controls, by llvm-nm, and the harness's ELF reader beside it
for p in floor syscaller; do
  ( cd "$d/harness/baseline" && "$NPKC" $p.npk -o "$F/$p.ll" ) && llc -O0 -filetype=obj -relocation-model=static "$F/$p.ll" -o "$F/$p.o"
  llvm-nm --undefined-only "$F/$p.o" | awk '{print $2}' | sort > "$F/$p.nm"
done
echo "§1.4 llvm-nm: the floor's object has $(wc -l < "$F/floor.nm") undefined symbols ($(tr '\n' ' ' < "$F/floor.nm" | sed 's/ $//')); the syscaller's $(wc -l < "$F/syscaller.nm"); the difference: $(comm -3 "$F/floor.nm" "$F/syscaller.nm" | tr -d '\t' | tr '\n' ' ')"
python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1])
import elf
ok = all(elf.Obj(sys.argv[2] + '/%s.o' % p).undefined() == open(sys.argv[2] + '/%s.nm' % p).read().split() for p in ('floor', 'syscaller'))
print('§1.4 harness/elf.py reads the same two sets: %s' % ('yes' if ok else 'NO'))
" "$d/harness" "$F"

# §1.5 -- the runtime classed whole: every global symbol of the pinned runtime object -- all a module's call can
# resolve to -- one row of runtime_symbols.tsv, and irscan.py's DENIED and FLOOR the table's two halves (llvm-nm,
# independently of the harness's ELF reader)
llvm-nm --defined-only --extern-only "$NPKRT" | awk '{print $3}' | sort -u > "$F/rt.nm"
python3 -B -c "
import sys, collections; sys.path.insert(0, sys.argv[1])
import irscan
g = set(open(sys.argv[2]).read().split())
rows = [l.rstrip('\n').split('\t') for l in open(sys.argv[3], encoding='utf-8') if l.strip() and not l.startswith('#')]
names = [r[0] for r in rows]
whole = len(names) == len(set(names)) and set(names) == g
print('§1.5 the runtime object\'s global symbols, by llvm-nm: %d -- every one a row of runtime_symbols.tsv, and no row anything else: %s' % (len(g), 'yes' if whole else 'NO'))
for half in ('deny', 'floor'):
    c = collections.Counter(r[1].split(': ', 1)[1] for r in rows if r[1].startswith(half + ': '))
    print('§1.5 %s: %s -- %d' % ('denied, by facet' if half == 'deny' else 'the floor', ', '.join('%s %d' % kv for kv in sorted(c.items())), sum(c.values())))
deny = {r[0] for r in rows if r[1].startswith('deny: ')}
floor = {r[0] for r in rows if r[1].startswith('floor: ')}
print('§1.5 irscan.DENIED and irscan.FLOOR are the table\'s two halves: %s' % ('yes' if irscan.DENIED == deny and irscan.FLOOR == floor else 'NO'))
" "$d/harness" "$F/rt.nm" "$T2/runtime_symbols.tsv"

# §1.6 -- one module per root: an imported module's function is DEFINED in the root's emission; and an extern
mkdir -p "$F/sep"
printf '%s\n' 'mod:helper;' '' 'pub func:helper_twice = int32(int32:x) never fails {' '    pass x * 2i32;' '};' > "$F/sep/helper.npk"
printf '%s\n' 'mod:root;' '' 'use "./helper.npk".*;' '' 'func:main = int32(cstring[]:_~argv) {' '    exit (raw helper_twice(21i32));' '};' '' \
  'func:failsafe = int32(Error:e) {' '    pick (e) {' '        (HeapBadRequest)    { exit 91i32; },' '        (HeapOom)           { exit 92i32; },' \
  '        (IntOverflow)       { exit 93i32; },' '        (Unreachable)       { exit 95i32; },' '        (WildLeak)          { exit 96i32; },' \
  '        (StackExhausted)    { exit 106i32; },' '        (MachineFault)      { exit 107i32; },' '        (*)                 { exit 99i32; }' '    }' '    exit 9i32;' '};' > "$F/sep/root.npk"
( cd "$F/sep" && "$NPKC" root.npk -o root.ll ) && llc -O0 -filetype=obj -relocation-model=static "$F/sep/root.ll" -o "$F/sep/root.o" \
  && ld.lld -static "$F/sep/root.o" "$NPKRT" -o "$F/sep/root"
"$F/sep/root"; rc=$?
echo "§1.6 a root importing a module: its emission DEFINES the imported function $(grep -c '^define .*@"npk\.helper\.helper_twice"' "$F/sep/root.ll") time(s); linked as one object and npkrt.o, it exits $rc"
printf '%s\n' 'mod:ext;' '' 'extern:"c" = {' '    func:getpid = int32();' '};' '' 'func:main = int32(cstring[]:_~argv) {' '    exit 0i32;' '};' > "$F/sep/ext.npk"
codes "$F/sep/ext.npk" | sed 's/^/§1.6 /'

# §1.7 -- repro: the conformance consumer from two copies, with the manifest and without (inside the repository)
for w in with without; do
  for c in a bb/deeper; do
    k="$F/rp-$w/$c"; mkdir -p "$k/tests"; cp -r "$d/src" "$k/"; cp -r "$d/tests/conformance" "$k/tests/"
    [ "$w" = with ] && cp "$d/nitpick.toml" "$k/"
    ( cd "$k/tests/conformance" && "$NPKC" import.npk -o "$F/rp-$w-$(echo $c | tr / _).ll" )
  done
  echo "§1.7 the consumer from two copies $w the manifest: $(cmp -s "$F/rp-$w-a.ll" "$F/rp-$w-bb_deeper.ll" && echo 'byte-identical' || echo 'two different modules')"
done

# §1.8 -- probe 06 at both legs: what LLVM says of its module, and the undefined value it names if it names one (at
# `7e91730` each tool named one, DEF-253; the pin carries landing 118's fix)
( cd "$d/tests/probe" && "$NPKC" probe06_trait_bound.npk -o "$F/p6.ll" ); echo "§1.8 probe 06: npkc $?"
llc -O0 -filetype=obj -relocation-model=static "$F/p6.ll" -o "$F/p6.o" 2> "$F/p6.llc"; echo "§1.8 llc $? -- $(grep -m1 -oE "use of undefined value '[^']+'" "$F/p6.llc" || echo 'no undefined value named')"
opt -O2 -S "$F/p6.ll" -o "$F/p6.2.ll" 2> "$F/p6.opt"; echo "§1.8 opt $? -- $(grep -m1 -oE "use of undefined value '[^']+'" "$F/p6.opt" || echo 'no undefined value named')"

# §1.9 -- the markers: every file of the suites the patched manifest declares, read by the patched reader
python3 -B - "$d" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import expect, manifest
m = manifest.read(os.path.join(sys.argv[1], "nitpick.toml"))
for t in m.tests:
    files = []
    for rel in manifest.paths_of(t):
        top = os.path.join(sys.argv[1], rel)
        files += sorted(os.path.join(top, f) for f in os.listdir(top) if f.endswith(".npk"))
    es = [expect.read(f) for f in files]
    bad = [e.path for e in es if not e.readable]
    print("§1.9 %s (%s): %d file(s), %d unreadable; expect-exit %s; capped %d; pending %s" % (
        t["name"], t["stage"], len(es), len(bad), " ".join(str(e.exit) for e in es),
        sum(1 for e in es if e.mem_cap_mib), ", ".join("%s %s" % (e.pending[0], os.path.basename(e.path)) for e in es if e.pending) or "none"))
PY

# §1.10 -- the shapes, over the .npk files the patches add or change, and the controls the scanner gained
python3 -B "$TL/shapes.py" $(grep -ohE '^\+\+\+ b/.*\.npk$' "$T2"/step*.patch | sed "s|^+++ b/|$d/|" | sort -u) | cut_paths | sed 's/^/§1.10 /'
echo "§1.10 the later planted control: $(python3 -B "$TL/shapes.py" "$TL/shapes_planted_later.txt" | tail -n +2 | tr -s ' ' | tr '\n' ';')"

# §1.11 -- landing 113's rule on names (F55, DEF-235): every declared name in every `.npk` of the patched tree, held to
# the pin's keyword table; the scanner proved on its planted and clean controls
git -C "$NPK_TREE" show "$PIN:src/frontend/keywords.npk" > "$F/keywords.npk"
echo "§1.11 planted control: $(python3 -B "$TL/names.py" --count "$F/keywords.npk" "$TL/names_planted.txt" | head -1 | sed 's/^1 file(s), //')"
echo "§1.11 clean control: $(python3 -B "$TL/names.py" --count "$F/keywords.npk" "$TL/names_clean.txt" | head -1 | sed 's/^1 file(s), //')"
( cd "$d" && python3 -B "$TL/names.py" --count "$F/keywords.npk" $(git ls-files '*.npk') ) | sed 's/^/§1.11 the patched tree: /'

# §1.12 -- landing 113's rule on attributes (F55's DERIVE-007 and DERIVE-004): each attribute's name, and what follows it
python3 -B - "$d" <<'PY'
import os, re, subprocess, sys
root = sys.argv[1]
files = subprocess.run(["git", "-C", root, "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
names, on = {}, {}
for f in files:
    lines = open(os.path.join(root, f), encoding="utf-8").read().split("\n")
    for k, line in enumerate(lines):
        m = re.match(r"\s*#\[\s*(\w+)", line)
        if not m:
            continue
        names[m.group(1)] = names.get(m.group(1), 0) + 1
        nxt = next((x.strip() for x in lines[k + 1:] if x.strip() and not x.strip().startswith("//")), "")
        kind = re.match(r"(?:pub\s+)?(struct|enum|impl|trait|func)\b", nxt)
        on[kind.group(1) if kind else "a binding or other"] = on.get(kind.group(1) if kind else "a binding or other", 0) + 1
print("§1.12 attributes in the patched tree: %s; each on %s" % (
    ", ".join("%s %d" % kv for kv in sorted(names.items())) or "none", ", ".join("%s %d" % kv for kv in sorted(on.items())) or "nothing"))
PY

# §1.12, continued -- landing 114's DEF-250 and the rulings in landing 112's commit (D-353 … D-359), by `rulings.py`
echo "§1.12 the rulings' planted control: $(python3 -B "$TL/rulings.py" "$TL/rulings_planted.txt" | tail -n +2 | sed 's/^ *//' | tr '\n' ';')"
echo "§1.12 the rulings' clean control: $(python3 -B "$TL/rulings.py" "$TL/rulings_clean.txt" | tail -n +2 | sed 's/^ *//' | tr '\n' ';')"
( cd "$d" && python3 -B "$TL/rulings.py" --sites $(git ls-files '*.npk') ) | sed -E 's/(fixed, initialised: [0-9]+) .*/\1/' | sed 's/^/§1.12 the patched tree: /'

# §1.13 -- the placeholders, and §1.14 -- every pointer the patches' added lines write
echo "§1.13 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T2"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.13 decisions.txt numbers them: $(python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in ('PD-138', 'PD-139') if k in t) or 'NEITHER')" "$TL")"
# §1.13, continued -- the run's date (`../tools/apply.py`): the lines each patch adds with the placeholder, and no file
# the patches touch holding it already, which would make a context line stop matching once replaced
echo "§1.13 added lines carrying @@DATE@@, by step:$(for p in "$T2"/step*.patch; do printf ' %s %s' "$(basename "$p" .patch)" "$(grep -E '^\+[^+]' "$p" | grep -c '@@DATE@@')"; done)"
held=$(grep -h '^+++ b/' "$T2"/step*.patch | sed 's|^+++ b/||' | sort -u | while read -r f; do [ -f "$REPO/$f" ] && grep -q '@@DATE@@' "$REPO/$f" && echo "$f"; done | tr '\n' ' ')
echo "§1.13 files the patches touch that hold @@DATE@@ as the tree stands: ${held:-none}"
python3 -B "$TL/pointers.py" "$d" "$T2" | sed 's/^§1\.8 /§1.14 /'

# §1.15 -- the workflow, read as GitHub reads it, and its harness step's logic run against two logs
python3 -B -c "
import re, sys, yaml
t = open(sys.argv[1], encoding='utf-8').read()
d = yaml.safe_load(t)
steps = d['jobs']['build']['steps']
hexq = [k for k, v in re.findall(r'^\s*([A-Z0-9_]+): \"([^\"]*)\"', t, re.M) if re.fullmatch(r'[0-9a-f]{7,64}', v)]
print('§1.15 the workflow parses; %d steps; runs-on %s; quoted hex values: %s' % (len(steps), d['jobs']['build']['runs-on'], ', '.join(hexq)))
open(sys.argv[2], 'w').write(next(s['run'] for s in steps if s.get('name') == 'Run the harness'))
" "$d/.github/workflows/ci.yml" "$F/step.sh"
echo "§1.15 uses: $(grep -cE '^ +uses: ' "$d/.github/workflows/ci.yml") line(s), a quoted owner/name@ and a full 40-hex sha: $(grep -cE '^ +uses: "[a-z-]+/[a-z-]+@[0-9a-f]{40}" # v[0-9]+$' "$d/.github/workflows/ci.yml")"
bash -n "$F/step.sh" && echo "§1.15 the harness step's script: bash -n accepts it"
for k in green short; do
  mkdir -p "$F/ci-$k/harness"
  [ "$k" = green ] && printf 'print("harness: GREEN -- a stand-in")\n' > "$F/ci-$k/harness/run.py"
  [ "$k" = short ] && printf 'print("ok    a runner that stopped short")\n' > "$F/ci-$k/harness/run.py"
  ( cd "$F/ci-$k" && RUNNER_TEMP="$F/ci-$k" bash "$F/step.sh" > "$F/ci-$k.out" 2>&1 ); rc=$?
  echo "§1.15 the step over a runner that prints $( [ $k = green ] && echo 'the green summary last' || echo 'no summary' ): exit $rc -- $(tail -n 1 "$F/ci-$k.out" | cut_paths)"
done

# §1.16 -- what step 4 writes of a `stack` name, re-measured at the pin: cycle 0.0.1's step 6's six shapes, built on
# probe 10's container and frame types and its failsafe, and the control with the local named `frames`
mkdir -p "$F/stack"
python3 -B - "$F/stack" "$REPO/tests/probe/probe10_explicit_stack.npk" <<'PY'
import os, sys
d, src = sys.argv[1], open(sys.argv[2], encoding="utf-8").read().split("\n")
prelude, failsafe = "\n".join(src[16:56]), "\n".join(src[104:119])
fr = "Frame{ kind: EventKind.StartSeq, count: 0u32, span: Span{ lo: 0u32, hi: 0u32 } }"
main = lambda body, k="0i64": ("func:main = int32(cstring[]:_~argv) {\n" + body +
                               "    if (k != %s) { exit 1i32; }\n    exit 0i32;\n};" % k)
shapes = [
    ("s1", "func:use_it = int64() never fails {\n    Vec<Frame>:stack = raw vec_init::<Frame>(16i64);\n"
           "    int64:n = stack.count;\n    drop vec_free(@stack);\n    pass n;\n};\n\n" + main("    int64:k = raw use_it();\n")),
    ("s2", main("    Vec<Frame>:stack = raw vec_init::<Frame>(16i64);\n    int64:k = stack.count;\n    drop vec_free(@stack);\n")),
    ("s3", "func:fill = int64() never fails {\n    Vec<Frame>:stack = raw vec_init::<Frame>(16i64);\n"
           "    for (int64:i in 0i64...4i64) {\n        drop vec_push(@stack, %s);\n    }\n"
           "    int64:n = stack.count;\n    drop vec_free(@stack);\n    pass n;\n};\n\n" % fr + main("    int64:k = raw fill();\n", "4i64")),
    ("s4", main("    int64:stack = 3i64;\n    int64:k = stack + 1i64;\n", "4i64")),
    ("s5", "func:depth_of = int64(int64:stack) never fails {\n    pass stack;\n};\n\n" + main("    int64:k = raw depth_of(3i64);\n", "3i64")),
    ("s6", "func:count_of = int64(Vec<Frame>->:stack) never fails {\n    pass stack.count;\n};\n\n"
           + main("    Vec<Frame>:frames = raw vec_init::<Frame>(16i64);\n    int64:k = raw count_of(@frames);\n    drop vec_free(@frames);\n")),
    ("control", main("    Vec<Frame>:frames = raw vec_init::<Frame>(16i64);\n    int64:k = frames.count;\n    drop vec_free(@frames);\n")),
]
for name, body in shapes:
    with open(os.path.join(d, "%s.npk" % name), "w", encoding="utf-8") as fh:
        fh.write("mod:%s;\n\n%s\n\n%s\n\n%s\n" % (name, prelude, body, failsafe))
PY
for s in s1:"a Vec<Frame> local in a helper" s2:"a Vec<Frame> local in main" s3:"a Vec<Frame> local before a braced loop" \
         s4:"an int64 local in main" s5:"a by-value parameter" s6:"a ->: parameter" control:"the control, the local named frames"; do
  echo "§1.16 stack, ${s#*:}: $(codes "$F/stack/${s%%:*}.npk" | sed 's/^[^:]*: //')"
done
echo "§1.16 messages naming a brace or \"never closed\": $(cd "$F/stack" && for f in s1 s2 s3 s4 s5 s6; do "$NPKC" $f.npk -o /dev/null 2>&1; done | grep -ciE 'brace|never closed')"
echo "§1.16 a parameter's message: $(cd "$F/stack" && "$NPKC" s5.npk -o /dev/null 2>&1 | grep -m1 -oE '`stack` is a keyword and cannot name a binding, a parameter')"

rm -rf "${F:?}"
