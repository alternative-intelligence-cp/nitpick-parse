# meta/roadmap/0.0/0.0.3_tools/facts.sh -- re-derives `0.0.3.md` §1, block 0b. Sourced after `../tools/env.sh`.
# Writes only under `$A/facts`, and removes it. Reads the compiler's tree with `git show` alone. Prints no path above
# the repository.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T3=$REPO/meta/roadmap/0.0/0.0.3_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2 3; do python3 -B "$TL/apply.py" "$d" 0.0.3 $s > /dev/null; done
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

rm -rf "${F:?}"
