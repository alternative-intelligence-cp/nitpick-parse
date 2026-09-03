# Glossary

One word per concept, one concept per word. Where the parsing world uses a word
two ways, this table says which one `nparse` means.

| Term | Means, in `nparse` |
|---|---|
| **input** | the `uint8[]` the caller owns and hands over. Never copied, never read from a file by this library. |
| **cursor** | the read position over the input, with its total operations. Never a lexer. |
| **span** | a half-open pair of byte offsets into the input. Never a line/column pair. |
| **event** | one item of the pull stream: a container boundary, a key, or a scalar. 24 bytes, no owning field. |
| **step** | one call's answer: `Ev`, `Fault` or `Done`. |
| **fault** | a `ParseError` **value** — what a malformed input produces. **Never** an `error:` identity. |
| **error** | one of the two `error:` identities, `EParseState` and `EParseEncode`. Only a *caller* can cause one. |
| **scalar** | a leaf value: null, bool, number, string, or a format's date/time. |
| **text ref** | where a scalar's bytes are — in the input, or in the parser's scratch. Valid until the next step. |
| **scratch** | the parser's own byte buffer, holding only scalars an escape forced it to rewrite. |
| **format** | an implementation of the `Format` trait. What every other ecosystem would call a plugin. |
| **plugin** | the same thing. There is no other kind: no dynamic loading, no registry. |
| **document** | the arena-backed tree a caller gets when they want one instead of a stream. |
| **node** | one element of a document. 56 bytes, POD, addressing its text by offset into the pool. |
| **pool** | the document's byte store, holding every scalar's text exactly once. |
| **frame** | one entry of the explicit depth stack. |
| **depth** | container nesting, bounded by `NPARSE_MAX_DEPTH` and never held on the machine stack. |
| **the round trip** | parse → print → parse, and the two trees agree. The oracle. |
| **canonical form** | the one output form a format's writer produces with no options set. |
| **corpus** | a vendored conformance suite with its upstream commit recorded. A gate, not a suggestion. |
| **dialect** | CSV's parameters. The only format with any. |
| **subset** | the part of a format this library implements, stated construct by construct. YAML has one; the others do not. |

## Words deliberately not used

| Not used | Because |
|---|---|
| "token" (in the public API) | the event stream is the interface; a token is an internal detail of one format's scanner |
| "lexer" | the shared layer is a *cursor* and a set of scanning primitives, not a lexer, and the distinction is what keeps it format-neutral |
| "AST" | this library produces a *value* tree, not a syntax tree — no trivia, no concrete syntax, no incremental reparse (`PLUGIN_MODEL.md` §7) |
| "CST" | likewise, and a CST is what the *other* library would produce |
| "error" for a malformed input | a malformed input produces a **fault**. The distinction is the library's central design decision. |
| "exception" | there are none in the language |
| "value" for a `Node` | a node is a node; "value" is what a map's pair holds, to keep the key/value pairing readable |
| "parse a file" | there is no such function. The caller supplies bytes. |
| "streaming" for the tree builder | the tree builder consumes a stream and produces a tree; only the event path is streaming |
