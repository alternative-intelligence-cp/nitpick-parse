# meta/roadmap/0.0/0.0.4_tools/facts.sh -- re-derives `0.0.4.md` §1's items 1 ... 10, block 0b; item 11 is a record,
# which no block re-derives. Sourced after `../tools/env.sh`.
# Writes under `$A/facts`, and removes it; `run4` and `bill` (`../tools/env.sh`) write `$A/run4` and `$A/reach`, the
# second removed. Reads the compiler's tree with `git show` alone. Prints no path above the repository.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T4=$REPO/meta/roadmap/0.0/0.0.4_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in $(python3 -B -c 'import sys; sys.path.insert(0, sys.argv[1]); import apply
print(" ".join(st for sub, st, _ in apply.plan_order() if sub == "0.0.4"))' "$TL"); do
  python3 -B "$TL/apply.py" "$d" 0.0.4 "$s" > /dev/null
done
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
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in ('PD-143', 'PD-144', 'PD-145') if k in t) or 'NONE')" "$TL")"
python3 -B "$TL/pointers.py" "$d" "$T4" | sed 's/^§1\.8 /§1.7 /'

# §1.8 -- `*=` and `+=` at the pin (item C): the emission of `a = a * b;` and of `a = a + b;`, the module's name
# masked, and the same trap, `IntOverflow` (93), at both legs
mkdir -p "$F/c"
fs93=$(printf '%s' "$floor" | sed 's/(OutOfBounds)       { exit 94i32; },/(IntOverflow)       { exit 93i32; },/')
for row in 'mulc|a *= b;|2i64' 'mulp|a = a * b;|2i64' 'addc|a += b;|4611686018427387904i64' 'addp|a = a + b;|4611686018427387904i64'; do
  IFS='|' read -r n st bv <<< "$row"
  { printf 'mod:%s;\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:a = 4611686018427387904i64;\n    int64:b = %s;\n    %s\n' "$n" "$bv" "$st"
    printf '    if (a == 7i64) { exit 3i32; }\n    exit 0i32;\n};\n\n'; printf '%s\n' "$fs93" | tr '|' '\n'; } > "$F/c/$n.npk"
  ( cd "$F/c" && "$NPKC" "$n.npk" -o "$n.ll" ) && sed "s/$n/M/g" "$F/c/$n.ll" > "$F/c/$n.norm"
done
for op in mul add; do
  case $op in mul) c='a *= b;'; pl='a = a * b;' ;; add) c='a += b;'; pl='a = a + b;' ;; esac
  cmp -s "$F/c/${op}c.norm" "$F/c/${op}p.norm" && same=byte-identical || same=DIFFERENT
  echo "§1.8 \`$c\` (${op}c) against \`$pl\` (${op}p): the emission $same, the module's name masked ($(wc -l < "$F/c/${op}c.norm") lines); $(run4 "$F/c/${op}c.npk" "$F/c/${op}p.npk" | tr '\n' ';' | sed 's/;$//; s/;/; /g')"
done

# §1.9 -- an error identity is its DECLARING module and its name (PA-117; item F's count in `SAFETY.md` §8), as
# `NITPICK-REACH-003` names what a root that declares no `failsafe` owes
mkdir -p "$F/e"
printf 'mod:pa;\n\npub error:EParseState;\n\npub func:pa_go = NIL() {\n    fail EParseState;\n};\n' > "$F/e/pa.npk"
printf 'mod:pb;\n\npub error:EParseState;\n\npub func:pb_go = NIL() {\n    fail EParseState;\n};\n' > "$F/e/pb.npk"
printf 'mod:pc;\n\npub error:EParseState;\n\npub func:pc_id = int64(int64:x) {\n    pass x;\n};\n' > "$F/e/pc.npk"
printf 'mod:pd;\n\nuse "./pc.npk".*;\n\npub func:pd_go = NIL() {\n    fail EParseState;\n};\n' > "$F/e/pd.npk"
owes() {
  local n=$1 f; shift
  { printf 'mod:%s;\n\n' "$n"; for f in "$@"; do printf 'use "./%s".*;\n' "$f"; done
    printf '\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n'; } > "$F/e/$n.npk"
  ( cd "$F/e" && "$NPKC" "$n.npk" -o /dev/null 2>&1 ) | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//'
}
echo "§1.9 a root importing pa and pb, each declaring and raising its own EParseState, owes $(owes r_two pa.npk pb.npk)"
echo "§1.9 a root importing pd, which raises the EParseState it imports from pc, owes $(owes r_one pd.npk)"

# §1.10 -- a `buffer` at the pin (PD-144's re-measurement note): the compiler's landing 128 built D-341
mkdir -p "$F/b"
buf() {
  { printf 'mod:%s;\n\nfunc:main = int32(cstring[]:_~argv) {\n    buffer:b = buffer_new(4i64);\n' "$1"
    printf '%s\n' "$2" | tr '|' '\n'; printf '    exit 0i32;\n};\n\n'; printf '%s\n' "$floor" | tr '|' '\n'; } > "$F/b/$1.npk"
}
buf buf_index '    int64:i = 9i64;|    uint8:x = b[i];'
buf buf_range '    uint8[]:v = b[0i64...2i64];|    uint8:x = v[1i64];'
buf buf_ptr_index '    uint8:y = b.ptr[9i64];'
buf buf_range_regrown '    uint8[]:v = b[0i64...2i64];|    b = buffer_new(16i64);|    uint8:x = v[0i64];'
buf buf_wild_regrown '    uint8[]:w = #wild_slice<uint8>(b.ptr, 4i64);|    b = buffer_new(16i64);|    uint8:z = w[0i64];'
run4 "$F/b/buf_index.npk" "$F/b/buf_range.npk" "$F/b/buf_ptr_index.npk" | sed 's/^/§1.10 /'
codes "$F/b/buf_range_regrown.npk" "$F/b/buf_wild_regrown.npk" | sed 's/^/§1.10 /'

rm -rf "${F:?}"
