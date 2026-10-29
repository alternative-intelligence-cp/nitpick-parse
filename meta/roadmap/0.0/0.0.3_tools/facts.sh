# meta/roadmap/0.0/0.0.3_tools/facts.sh -- re-derives `0.0.3.md` §1, block 0b. Sourced after `../tools/env.sh`.
# Writes only under `$A/facts`, and removes it. Reads the compiler's tree with `git show` alone. Prints no path above
# the repository.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T3=$REPO/meta/roadmap/0.0/0.0.3_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 0c 0d 0e 1 2 3; do python3 -B "$TL/apply.py" "$d" 0.0.3 $s > /dev/null; done
cut_paths() { sed -e "s|$d/||g" -e "s|$F/||g" -e "s|$REPO/||g"; }

# §1.1 -- the tree it starts from: cycle 0.0.2's record
echo "§1.1 harness holds: $(git -C "$REPO" ls-files harness | sed 's|^harness/||' | tr '\n' ' ')"
echo "§1.1 nitpick.toml's [[test]] entries: $(grep -A1 '^\[\[test\]\]' "$REPO/nitpick.toml" | grep -oE '"[a-z-]+"' | tr '\n' ' ')"
echo "§1.1 harness/baseline/PENDING.txt's lines: $(grep -c $'\t' "$REPO/harness/baseline/PENDING.txt")"

# §1.2 -- the compiler's own parse and check tools are sources at the pin, which a run would have to build
for t in tools/parse_check.npk tools/check.npk; do
  echo "§1.2 the compiler's $t at the pin: $(git -C "$NPK_TREE" cat-file -e "$PIN:$t" 2>/dev/null && echo "a source, $(git -C "$NPK_TREE" show "$PIN:$t" | wc -l) lines" || echo absent)"
done

# §1.3 -- probe 08h and its control: the reseat through a callee refused, as the same reseat done directly is (at
# `7e91730` the callee's was accepted, DEF-252; the pin carries landing 116's fix)
codes "$d/tests/probe/refused/probe08h_view_reseated.npk" | sed 's/^/§1.3 /'
codes "$d/tests/probe/refused/probe08g_holder_outlives_view.npk" | sed 's/^/§1.3 /'

# §1.4 -- an error identity is a module and a name (the ecosystem audit's EC3), measured
mkdir -p "$F/ec3"
printf '%s\n' 'mod:lay;' '' 'error:EPrivate;' 'pub error:EUnraised;' '' 'pub func:lay_go = NIL(int64:n) {' '    if (n > 3i64) { fail EPrivate; }' '    pass NIL;' '};' > "$F/ec3/lay.npk"
printf '%s\n' 'mod:root;' '' 'use "./lay.npk".*;' '' 'func:main = int32(cstring[]:_~argv) {' '    Result<NIL>:r = lay_go(5i64);' '    if (r.is_error) { exit 1i32; }' '    exit 0i32;' '};' > "$F/ec3/root.npk"
echo "§1.4 a root importing a module whose reachable fail raises a private error owes: $(cd "$F/ec3" && "$NPKC" root.npk -o /dev/null 2>&1 | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//'); and EUnraised, public and never raised: $(cd "$F/ec3" && "$NPKC" root.npk -o /dev/null 2>&1 | grep -c EUnraised) mention(s)"
printf '%s\n' 'mod:coded;' '' 'error:ECoded = 7i32;' > "$F/ec3/coded.npk"
codes "$F/ec3/coded.npk" | sed 's/^/§1.4 a user error with its own code: /'

# §1.5 -- the shapes, the names and the rulings, over the `.npk` files the patches add or change
python3 -B "$TL/shapes.py" $(grep -ohE '^\+\+\+ b/.*\.npk$' "$T3"/step*.patch | sed "s|^+++ b/|$d/|" | sort -u) | cut_paths | sed 's/^/§1.5 /'
git -C "$NPK_TREE" show "$PIN:src/frontend/keywords.npk" > "$F/keywords.npk"
( cd "$d" && python3 -B "$TL/names.py" --count "$F/keywords.npk" $(git ls-files '*.npk') ) | sed 's/^/§1.5 names, the patched tree: /'
( cd "$d" && python3 -B "$TL/rulings.py" --sites $(git ls-files '*.npk') ) | sed -E 's/(fixed, initialised: [0-9]+) .*/\1/' | sed 's/^/§1.5 rulings, the patched tree: /'

# §1.6 -- the placeholders, and §1.7 -- every pointer the patches' added lines write
echo "§1.6 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T3"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.6 decisions.txt numbers them: $(python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in ('PD-140', 'PD-141', 'PD-142') if k in t) or 'NONE')" "$TL")"
python3 -B "$TL/pointers.py" "$d" "$T3" | sed 's/^§1\.8 /§1.7 /'

# §1.8 -- the floor program's own scan at the pin, which step 0e holds to `run.py`'s two lists: its object's undefined
# symbols by `llvm-nm`, apart from the harness's ELF reader, and its -O0 IR's call edges to the runtime by LLVM's own
# call graph, apart from the harness's IR reader -- an edge from a function the IR defines to one it only declares,
# `.<digits>` read as `.N` as `irscan.edges` reads it
( cd "$d/harness/baseline" && "$NPKC" floor.npk -o "$F/floor.ll" ) && llc -O0 -filetype=obj -relocation-model=static "$F/floor.ll" -o "$F/floor.o"
llvm-nm --undefined-only "$F/floor.o" | awk '{print $2}' | sort > "$F/floor.nm"
opt -passes=print-callgraph -disable-output "$F/floor.ll" 2> "$F/floor.cg"
python3 -B - "$d/harness" "$F" <<'PY'
import re, sys
sys.path.insert(0, sys.argv[1])
import irscan, run
ll = open(sys.argv[2] + "/floor.ll", encoding="utf-8").read()
und = set(open(sys.argv[2] + "/floor.nm", encoding="utf-8").read().split())
defined = {m.group(1) or m.group(2) for m in re.finditer(r'^define\b[^@]*@(?:"([^"]+)"|([-\w.$]+))\(', ll, re.M)}
edges, cur = set(), None
for line in open(sys.argv[2] + "/floor.cg", encoding="utf-8"):
    if line.startswith("Call graph node"):
        m = re.match(r"Call graph node for function: '([^']+)'", line)
        cur = m.group(1) if m and m.group(1) in defined else None
        continue
    m = re.match(r"  CS<[^>]*> calls function '([^']+)'", line)
    if m and cur and m.group(1) not in defined and not m.group(1).startswith("llvm."):
        edges.add((re.sub(r"\.\d+$", ".N", cur), m.group(1)))
show = lambda es: ", ".join("%s -> %s" % e for e in sorted(es))
print("§1.8 the floor's undefined symbols, by llvm-nm: %d -- %s; run.py's FLOOR_UNDEFINED the same: %s"
      % (len(und), " ".join(sorted(und)), "yes" if und == run.FLOOR_UNDEFINED else "NO"))
print("§1.8 the floor's call edges to the runtime, by LLVM's call graph: %d -- %s; irscan.edges the same: %s; "
      "run.py's FLOOR_EDGES the same: %s" % (len(edges), show(edges), "yes" if irscan.edges(ll) == edges else "NO",
                                            "yes" if run.FLOOR_EDGES == edges else "NO"))
PY

# §1.9 -- the stages: what the compiler's manifest reader accepts at the pin, what `BUILD_REFERENCE.md` §7.1's table
# lists, and the patched reader's set
git -C "$NPK_TREE" show "$PIN:npkg/manifest.npk" | awk '/^func:stage_known/ {p = 1} p; p && /^};/ {p = 0}' \
  | grep -oE 'text_eq\(s, "[a-z]+"\)' | sed -E 's/.*"([a-z]+)".*/\1/' | sort > "$F/stages.known"
git -C "$NPK_TREE" show "$PIN:meta/specs/BUILD_REFERENCE.md" | awk '/^### 7\.1 / {p = 1; next} /^### / {p = 0} p' \
  | grep -oE '^\| `[a-z]+`' | grep -oE '[a-z]+' | sort > "$F/stages.table"
echo "§1.9 npkg/manifest.npk's stage_known at the pin: $(wc -l < "$F/stages.known") -- $(tr '\n' ' ' < "$F/stages.known" | sed 's/ $//')"
echo "§1.9 BUILD_REFERENCE.md §7.1's table at the pin: $(wc -l < "$F/stages.table") stage(s); stage_known's not in it: $(comm -23 "$F/stages.known" "$F/stages.table" | tr '\n' ' ' | sed 's/ $//')"
python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import manifest
known = set(open(sys.argv[2], encoding='utf-8').read().split())
print('§1.9 the patched harness/manifest.py knows every one: %s; and beyond them: %s' % ('yes' if known <= manifest.KNOWN_STAGES else 'NO', ' '.join(sorted(manifest.KNOWN_STAGES - known))))" "$d/harness" "$F/stages.known"

# §1.10 -- the markers: the names the compiler's test reader matches with `text_starts_with(body, ...)`, at the pin
# and at the two before it, and how the patched reader classes them
for c in 7e91730 c9baa9e "$PIN"; do
  git -C "$NPK_TREE" show "$c:npkg/expect.npk" | grep -oE 'text_starts_with\(body, "[^"]+"\)' | sed -E 's/.*"([^"]+)".*/\1/' | sort > "$F/markers.$c"
done
echo "§1.10 npkg/expect.npk's markers at the pin: $(wc -l < "$F/markers.$PIN") -- $(tr '\n' ' ' < "$F/markers.$PIN" | sed 's/ $//')"
echo "§1.10 without a colon: $(grep -v ':$' "$F/markers.$PIN" | tr '\n' ' ' | sed 's/ $//'); the same names at 7e91730 and c9baa9e: $(cmp -s "$F/markers.7e91730" "$F/markers.$PIN" && cmp -s "$F/markers.c9baa9e" "$F/markers.$PIN" && echo yes || echo NO)"
python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import expect
names = open(sys.argv[2], encoding='utf-8').read().split()
j = [n for n in names if n in expect.MARKERS_JUDGED]; r = [n for n in names if n in expect.MARKERS_REFUSED]
print('§1.10 the patched harness/expect.py judges %d of them and refuses %d; neither: %s' % (len(j), len(r), ' '.join(n for n in names if n not in j + r) or 'none'))" "$d/harness" "$F/markers.$PIN"

rm -rf "${F:?}"
