# meta/roadmap/0.0/0.0.0_tools/facts.sh -- re-derives `0.0.0.md` §1, block 0b. Sourced after `../tools/env.sh`, so
# `$REPO`, `$A`, `$NPKC`, `$NPKRT`, `$NPK_TREE`, `$PIN` and the helpers are set. Writes only under `$A/facts`, and
# removes it. Reads the compiler's tree with `git show` alone.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T0=$REPO/meta/roadmap/0.0/0.0.0_tools
TL=$REPO/meta/roadmap/0.0/tools

# §1.1 -- the tree it starts from
echo "§1.1 tests/probe holds: $(git -C "$REPO" ls-files tests/probe | tr '\n' ' ')"
echo "§1.1 decisions: $(grep -c '^### PA-' "$REPO/meta/DECISIONS.md") headings, the highest by value PA-$(grep -o '^### PA-[0-9]*' "$REPO/meta/DECISIONS.md" | cut -d- -f2 | sort -n | tail -1)"

# §1.2 -- the compiler's own text that the patches cite, read at the pin
echo "§1.2 at $PIN, TYPE_REFERENCE.md §9.3: $(git -C "$NPK_TREE" show $PIN:meta/specs/TYPE_REFERENCE.md | grep -m1 -oE '; Enum values are plain i32 constants')"
echo "§1.2 at $PIN, TYPE_REFERENCE.md §9.2: $(git -C "$NPK_TREE" show $PIN:meta/specs/TYPE_REFERENCE.md | grep -m1 -oE 'by `string_bytes`$')"
echo "§1.2 at $PIN, MEMORY_REFERENCE.md §5: $(git -C "$NPK_TREE" show $PIN:meta/specs/MEMORY_REFERENCE.md | grep -m1 -oE 'as `StackExhausted` \(4118\)')"
echo "§1.2 at $PIN, MEMORY_REFERENCE.md §5's main stack: $(git -C "$NPK_TREE" show $PIN:meta/specs/MEMORY_REFERENCE.md | grep -m1 -oE '\| usable \| — \| 8 MiB \| 2 MiB \| 1 MiB \|')"
echo "§1.2 at $PIN, DECISIONS.md: $(git -C "$NPK_TREE" show $PIN:meta/specs/DECISIONS.md | grep -m1 -oE '^## D-305 — [^—]{0,60}') | $(git -C "$NPK_TREE" show $PIN:meta/specs/DECISIONS.md | grep -m1 -oE '^## D-351 — [^,]{0,60}')"
echo "§1.2 at $PIN, the prelude's StaleHandle: $(git -C "$NPK_TREE" show $PIN:src/prelude/prelude.npk | grep -m1 -oE 'pub error:StaleHandle = 4106i32;')"

# §1.3 -- the literal envelope
printf 'mod:lit;\n\nfixed uint64:BIG = 18446744073709551615u64;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$F/lit.npk"
echo "§1.3 $(codes "$F/lit.npk")"

# §1.4 -- what a consumer of each module shape owes: NITPICK-REACH-003, the compiler as the oracle
mkdir -p "$F/bill"
printf '%s\n' 'mod:arith_shape;' '' 'pub func:mul_add = uint64?(uint64:acc, uint64:base, uint64:digit, uint64:bound)' \
  '        never fails {' '    if (base == 0u64)   { pass NIL; }' '    if (digit > bound)  { pass NIL; }' \
  '    uint64:room = (bound - digit) / base;' '    if (acc > room)     { pass NIL; }' \
  '    pass (acc * base + digit);' '};' > "$F/bill/arith_shape.npk"
printf '%s\n' 'mod:class_shape;' '' 'pub func:is_digit = bool(uint8:b) never fails {' \
  '    pass b >= 48u8 && b <= 57u8;' '};' > "$F/bill/class_shape.npk"
printf '%s\n' 'mod:cursor_shape;' '' 'pub struct:Cursor = { fixed uint8[]:src; int64:pos; };' '' \
  'pub func:cur_peek = uint8?(Cursor->:c) never fails {' '    if (c.pos < 0i64 || c.pos >= c.src.len) { pass NIL; }' \
  '    pass c.src[c.pos];' '};' > "$F/bill/cursor_shape.npk"
printf '%s\n' 'mod:arena_shape;' '' 'pub struct:Node = { int64:v; };' '' 'pub func:count_one = int64() never fails {' \
  '    arena<Node>:ar = arena_make(4i64);' '    Handle<Node>:h = ar.alloc();' \
  '    Result<NIL>:p = ar.put(h, Node{ v: 1i64 });' '    ar.destroy();' '    if (p.is_error) { pass 0i64; }' \
  '    pass 1i64;' '};' > "$F/bill/arena_shape.npk"
for m in arith_shape class_shape cursor_shape arena_shape; do echo "§1.4 $(bill "$F/bill/$m.npk")"; done

# §1.5 -- where a recursion of probe 10b's shape traps: the four edges PD-133's text states, built from the
# probe as step 4 adds it (the patches applied to a throwaway clone of HEAD, which §1.6 and §1.8 read too)
d=$A/facts/tree; rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
for s in 1 2 3 4 5; do python3 -B "$TL/apply.py" "$d" 0.0.0 $s > /dev/null; done
for n in 65534 65535 131062 131063; do
  sed "s/fixed int64:LEVELS = 1048576i64;/fixed int64:LEVELS = ${n}i64;/; s/mod:probe10b_native_recursion_traps;/mod:depth_$n;/" \
    "$d/tests/probe/probe10b_native_recursion_traps.npk" > "$F/depth_$n.npk"
  ( cd "$F" && "$NPKC" depth_$n.npk -o depth_$n.ll ) > /dev/null 2>&1
  llc -O0 -filetype=obj -relocation-model=static "$F/depth_$n.ll" -o "$F/d0.o" && ld.lld -static "$F/d0.o" "$NPKRT" -o "$F/d0"
  opt -O2 -S "$F/depth_$n.ll" -o "$F/d2.ll" && llc -O2 -filetype=obj -relocation-model=static "$F/d2.ll" -o "$F/d2.o" \
    && ld.lld -static "$F/d2.o" "$NPKRT" -o "$F/d2"
  "$F/d0" > /dev/null 2>&1; r0=$?; "$F/d2" > /dev/null 2>&1; r2=$?
  echo "§1.5 $n levels: -O0 $r0, -O2 $r2"
done

# §1.6 -- the shapes the landing list names, over every `.npk` the patches add, comments and strings blanked;
# the scanner first proved on its planted and clean controls
echo "§1.6 the planted control:"; python3 -B "$TL/shapes.py" "$TL/shapes_planted.txt" | tail -n +2
echo "§1.6 the clean control:"; python3 -B "$TL/shapes.py" "$TL/shapes_clean.txt" | tail -n +2
mkdir -p "$F/added"
for s in 1 2 3 4 5; do
  grep -oE '^\+\+\+ b/.*\.npk$' "$T0/step$s.patch" | sed 's|^+++ b/||' >> "$F/added/list"
done
echo "§1.6 the $(wc -l < "$F/added/list") .npk file(s) the patches add:"
python3 -B "$TL/shapes.py" $(sed "s|^|$d/|" "$F/added/list") | tail -n +2
echo "§1.6 and where the plain views and the operands not spelled as an int32 literal are:"
python3 -B "$TL/shapes.py" --sites $(sed "s|^|$d/|" "$F/added/list") | sed "s|$d/||g" \
  | grep -E '^  (a plain|exit operand: `|exit operand: a cast)' | tr -s ' '


# §1.7 -- the placeholders: no file the patches touch holds one before they apply, and every one has a number
n=0; for f in $(grep -ohE '^\+\+\+ b/.*' "$T0"/step*.patch | sed 's|^+++ b/||' | sort -u); do
  [ -f "$REPO/$f" ] && grep -q '@@PD-' "$REPO/$f" && { echo "§1.7 holds a placeholder already: $f"; n=$((n+1)); }
done
echo "§1.7 files the patches touch that hold \`@@PD-\` as the tree stands: $n"
echo "§1.7 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T0"/step*.patch | sort -u | tr '\n' ' ')"
echo "§1.7 numbered by decisions.txt: $(python3 -B -c "
import sys; sys.path.insert(0, '$TL'); import apply
t = apply.numbers(); print(' '.join('%s=base+%d' % (k, int(t[k].split('-')[1]) - apply.base_number()) for k in sorted(t) if k <= 'PD-134'))")"

# §1.8 -- every rule and section the added lines cite exists in the tree the patches leave
python3 -B "$TL/pointers.py" "$d" "$T0" | sed "s|$d/||g"
rm -rf "${d:?}" "${F:?}"
