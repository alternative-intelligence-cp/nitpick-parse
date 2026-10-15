# meta/roadmap/0.0/0.0.4_tools/facts.sh -- re-derives `0.0.4.md` §1, block 0b. Sourced after `../tools/env.sh`.
# Writes only under `$A/facts`, and removes it. Reads the compiler's tree with `git show` alone. Prints no path above
# the repository.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T4=$REPO/meta/roadmap/0.0/0.0.4_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2 3 4; do python3 -B "$TL/apply.py" "$d" 0.0.4 $s > /dev/null; done
cut_paths() { sed -e "s|$d/||g" -e "s|$F/||g" -e "s|$REPO/||g"; }
floor='func:failsafe = int32(Error:e) {|    pick (e) {|        (HeapBadRequest)    { exit 91i32; },|        (HeapOom)           { exit 92i32; },|        (OutOfBounds)       { exit 94i32; },|        (Unreachable)       { exit 95i32; },|        (WildLeak)          { exit 96i32; },|        (StackExhausted)    { exit 106i32; },|        (MachineFault)      { exit 107i32; },|        (*)                 { exit 99i32; }|    }|    exit 9i32;|};'

# §1.1 -- the tree it starts from: cycle 0.0.3's record
echo "§1.1 src/core holds: $(git -C "$REPO" ls-files src/core | sed 's|^src/core/||' | tr '\n' ' ')"
echo "§1.1 tests/unit holds: $(git -C "$REPO" ls-files tests/unit | sed 's|^tests/unit/||' | tr '\n' ' ')"
echo "§1.1 nitpick.toml's [[test]] entries: $(grep -A1 '^\[\[test\]\]' "$REPO/nitpick.toml" | grep -oE '"[a-z-]+"' | tr '\n' ' ')"

# §1.2 -- an index through a `wild` block's pointer does not trap: the reason every accessor checks its own
mkdir -p "$F/w"
{ printf '%s\n' 'mod:wild_read;' '' 'func:main = int32(cstring[]:_~argv) {' '    wild int8->:m = alloc(32i64);' \
  '    wild int64->:p = (m =>! wild int64->);' '    int64:x = p[9i64];' '    dalloc(m);' '    if (x == 7i64) { exit 1i32; }' '    exit 0i32;' '};' ''; printf '%s\n' "$floor" | tr '|' '\n'; } > "$F/w/wild_read.npk"
run4 "$F/w/wild_read.npk" | sed -E 's/^wild_read: -O0 [01], -O2 [01]$/no trap at either leg (it exits 0 or 1, by what the memory held)/' | sed 's/^/§1.2 a read at index 9 of a 4-element wild block: /'

# §1.3 -- what a live clause costs every consumer (the early ecosystem audit's EK1), measured
for k in requires ensures limit; do
  case $k in
    requires) body='pub func:cf = int64(int64:x) never fails requires x > 0i64 {|    pass x;|};' ;;
    ensures)  body='pub func:cf = int64(int64:x) never fails ensures result > 0i64 {|    pass x;|};' ;;
    limit)    body='pub struct:Box = { limit<ListLen> int64:n; };|pub func:cf = int64(int64:x) never fails {|    Box:b = Box{ n: x };|    pass b.n;|};' ;;
  esac
  { printf 'mod:c_%s;\n\n' "$k"; printf '%s\n' "$body" | tr '|' '\n'; } > "$F/w/c_$k.npk"
  echo "§1.3 a live \`$k\`: a consumer owes $(bill "$F/w/c_$k.npk" | sed 's/^c_[a-z]*\.npk: //')"
done

# §1.4 -- what each module of `src/core/` costs a consumer
bill "$d/src/core/limits.npk" "$d/src/core/vec.npk" "$d/src/core/bytes.npk" | sed 's/^/§1.4 /'

# §1.5 -- the shapes, the names and the rulings, over the `.npk` files the patches add or change
python3 -B "$TL/shapes.py" $(grep -ohE '^\+\+\+ b/.*\.npk$' "$T4"/step*.patch | sed "s|^+++ b/|$d/|" | sort -u) | cut_paths | sed 's/^/§1.5 /'
git -C "$NPK_TREE" show "$PIN:src/frontend/keywords.npk" > "$F/keywords.npk"
( cd "$d" && python3 -B "$TL/names.py" --count "$F/keywords.npk" $(git ls-files '*.npk') ) | sed 's/^/§1.5 names, the patched tree: /'
( cd "$d" && python3 -B "$TL/rulings.py" --sites $(git ls-files '*.npk') ) | sed -E 's/(fixed, initialised: [0-9]+) .*/\1/' | sed 's/^/§1.5 rulings, the patched tree: /'

# §1.6 -- the placeholders, and §1.7 -- every pointer the patches' added lines write
echo "§1.6 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T4"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.6 decisions.txt numbers them: $(python3 -B -c "
import sys; sys.path.insert(0, sys.argv[1]); import apply
t = apply.numbers(); print(' '.join('%s=%s' % (k, t[k]) for k in ('PD-143', 'PD-144', 'PD-145') if k in t) or 'NONE')" "$TL")"
python3 -B "$TL/pointers.py" "$d" "$T4" | sed 's/^§1\.8 /§1.7 /'

rm -rf "${F:?}"
