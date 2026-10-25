# The LLVM 20.1.8 release asset CI installs — research digest

**As of 2026-10-23.** Question: what are the sha256 and the size of `LLVM-20.1.8-Linux-X64.tar.xz`, the asset of the
LLVM project's `llvmorg-20.1.8` release that `.github/workflows/ci.yml` installs, as the asset itself and the
release's own records give them, and can the asset be replaced under its name? Asked by cycle 0.0.1a's plan, the
adoption of compiler `2e1cb4a`, whose CI step pins the digest (the libraries' seat's ruling of 2026-10-22 on
`ci.yml`'s "an immutable asset").

## Answer

The asset is
`https://github.com/llvm/llvm-project/releases/download/llvmorg-20.1.8/LLVM-20.1.8-Linux-X64.tar.xz`,
**2 021 269 412 bytes, sha256 `1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6`**. Three readings
agree: the asset itself, streamed whole through a hash and a byte count and never written to disk; GitHub's record of
the asset; and the provenance the LLVM project's release workflow published for it. **The release is not
immutable**: GitHub's record of it reads `"immutable": false`, so an asset can be deleted and uploaded again under
the same name, and what pins the asset is its digest, not its name.

## Evidence

- `https://github.com/llvm/llvm-project/releases/download/llvmorg-20.1.8/LLVM-20.1.8-Linux-X64.tar.xz` — retrieved
  2026-10-23, 03:13:05 to 03:14:10 EDT, `curl -fsSL` piped into a single pass of Python's `hashlib.sha256` and a
  byte count, pipeline exit 0: `sha256: 1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6`,
  `bytes: 2021269412`.
- `https://api.github.com/repos/llvm/llvm-project/releases/tags/llvmorg-20.1.8` (`gh api`) — retrieved 2026-10-23
  03:13:10 EDT: release 231011227, `"immutable": false`, published 2025-07-09T03:20:57Z; its asset
  `LLVM-20.1.8-Linux-X64.tar.xz`, `"id": 271269785`, `"size": 2021269412`,
  `"digest": "sha256:1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6"`,
  `"created_at": "2025-07-09T05:32:33Z"`, `"updated_at": "2025-07-09T05:33:23Z"`, uploaded by `github-actions[bot]`.
- `https://github.com/llvm/llvm-project/releases/download/llvmorg-20.1.8/LLVM-20.1.8-Linux-X64.tar.xz.jsonl` —
  retrieved 2026-10-23: 10 422 bytes, sha256 `00beee3c049c219a524f567bf08c667c160926092623366ad23c37d5c6aca75d`,
  equal to GitHub's record of that asset (271269921). A Sigstore bundle whose in-toto statement, of predicate type
  `https://slsa.dev/provenance/v1`, names the subject `LLVM-20.1.8-Linux-X64.tar.xz` with sha256
  `1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6`, built by
  `.github/workflows/release-tasks.yml` at `refs/tags/llvmorg-20.1.8` of `https://github.com/llvm/llvm-project`
  (its run 16159480195, attempt 1), and logged at Rekor index 268489885, integrated 2025-07-09T05:32:25Z. Read as
  the project's statement: its signature was not verified.

## What would change this

An asset deleted and uploaded again under the same name, which `"immutable": false` allows: its digest would differ,
and CI's check would then refuse the download before unpacking it. A release that moved its tag would move the
records above as well. Neither is a version change: the version is the compiler's D-349, read in its tree.

## Confidence and gaps

High for the size and the digest: the bytes themselves and two of the project's own records agree. The provenance
bundle's signature was not verified, so it is read as the project's statement, not as proof of who built the asset.
CI's own fetch, on cycle 0.0.1a's step 1 push, is the second reading of the asset itself.
