# PawLang 😺 — an emoji programming language

PawLang is a small, statically-typed programming language whose keywords and operators are emojis, together with the front end of a compiler for it, written in Python. The compiler reads PawLang source, runs **lexical analysis** and **recursive-descent parsing**, and prints the resulting **Abstract Syntax Tree** (AST).

This is the compiler front end (lexer + parser): it tokenises the source and builds a fully-checked syntax tree, reporting precise errors with line and column. Semantic analysis and code generation were planned as a later stage.

## The language

| Concept | Syntax |
| --- | --- |
| Types | `🐾32` (32-bit int), `🐾64` (64-bit int), `🎏` (bool) |
| Mutability | `🧊` constant, `🪄` mutable |
| Boolean literals | `😺` true, `😿` false |
| Declaration | `🧊 🐾32 x { 10 }` |
| Assignment | `x ⬅️ 5` |
| Arithmetic | `➕` `➖` `✖️` |
| Comparison | `🤝` == `🙅` != `⟰` > `⟱` < `⟰=` >= `⟱=` <= |
| If / else | `🐈‍⬛ cond { ... } 🐾else { ... }` |
| Return (last statement) | `➡️ x` |
| Overflow pragma | `🛎️overflow on` / `off` |
| Comment | `// ...` |

### Example program

```
🛎️overflow off

🧊 🐾32 a { 10 }
🪄 🐾64 b { 20 }

b ⬅️ a ➕ 5

🐈‍⬛ b ⟰ 10 {
    🧊 🎏 c { 😺 }
} 🐾else {
    🧊 🎏 d { 😿 }
}

➡️ b
```

This declares a constant 32-bit `a` and a mutable 64-bit `b`, reassigns `b`, branches on `b > 10`, and returns `b`.

### Grammar

The parser is a direct, hand-written implementation of this EBNF grammar — one function per rule. Operator handling in `expr` gives a single level of binary operators over `factor` atoms.

```ebnf
program    ::= [pragma] stmt* [returnStmt]
pragma     ::= "🛎️overflow" ("on" | "off")

stmt       ::= decl | assign | ifStmt
ifStmt     ::= "🐈‍⬛" expr "{" stmt+ "}" ["🐾else" "{" stmt+ "}"]
decl       ::= mutability type ID "{" expr "}"
assign     ::= ID "⬅️" expr
returnStmt ::= "➡️" expr

mutability ::= "🧊" | "🪄"
type       ::= "🐾32" | "🐾64" | "🎏"
expr       ::= factor [ (comp_op | arith_op) factor ]
comp_op    ::= "🤝" | "🙅" | "⟰" | "⟱" | "⟰=" | "⟱="
arith_op   ::= "➕" | "➖" | "✖️"
factor     ::= ID | number | "😺" | "😿"
```

Blocks may not be empty, a pragma (if present) must come first, and `return` must be the last statement — all enforced by the parser.

## How it works

1. **Lexer** — scans the source into tokens, recognising the multi-codepoint emoji sequences (the if-cat `🐈‍⬛` is several Unicode code points joined by zero-width joiners), tracking line and column for every token, and skipping comments and whitespace.
2. **Parser** — a recursive-descent parser that consumes the token stream and builds typed AST nodes (`DeclNode`, `AssignNode`, `IfNode`, `BinaryOpNode`, …), raising a `Compilation error: [line, col] …` on anything that doesn't fit the grammar.
3. **Output** — the AST is printed and written to the output file.

## Run it

Needs Python 3.10+. No dependencies.

```bash
./compiler.py <input.txt> <output.ast>

echo "🧊 🐾32 x { 10 } ➡️ x" > program.txt
./compiler.py program.txt program.ast
```

On success it prints the AST; on invalid input it prints a compilation error with the location.

## Tests

```bash
python3 run_tests.py
```

There are 30 tests: 15 **happy-path** programs that must compile (declarations, assignments, every comparison operator, nested if/else, a full program, comments) and 15 **error** cases that must be rejected (missing mutability or type, empty blocks, double operators, a statement after `return`, unknown symbols, malformed pragmas). All 30 pass.

## Layout

| Path | Contents |
| --- | --- |
| `compiler.py` | The lexer, parser, AST nodes and CLI |
| `tests/happy/` | Programs that must compile |
| `tests/errors/` | Programs that must be rejected |
| `run_tests.py` | Runs the whole suite |

## License

[MIT](LICENSE)
