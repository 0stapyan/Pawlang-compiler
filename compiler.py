#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Course Project Stage 1: Custom Language Lexer & Parser
Language: EmojiCat (Paw32, Paw64, FishBool)
Syntax:
  - Pragma: 🛎️overflow on|off
  - Types: 🐾32, 🐾64, 🎏
  - Mutability: 🧊 (const), 🪄 (var)
  - Bool: 😺 (true), 😿 (false)
  - Control: 🐈‍⬛ { ... } 🐾else { ... }
  - Return: ➡️
  - Assign: ⬅️
  - Ops: ➕ ➖ ✖️
  - Cmp: 🤝 🙅 ⟰ ⟱ ⟰= ⟱=
"""

import sys
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Union

# Token types
TT_EOF      = "EOF"
TT_NEWLINE  = "NEWLINE"
TT_IDENT    = "IDENT"
TT_NUMBER   = "NUMBER"
TT_LBRACE   = "LBRACE"     # {
TT_RBRACE   = "RBRACE"     # }
TT_KEYWORD  = "KEYWORD"

# New tokens
TT_TYPE_32  = "TYPE_32"    # 🐾32
TT_TYPE_64  = "TYPE_64"    # 🐾64
TT_TYPE_BOOL= "TYPE_BOOL"  # 🎏
TT_LIT_TRUE = "LIT_TRUE"   # 😺
TT_LIT_FALSE= "LIT_FALSE"  # 😿
TT_MUT_CONST= "MUT_CONST"  # 🧊
TT_MUT_VAR  = "MUT_VAR"    # 🪄
TT_ASSIGN   = "ASSIGN"     # ⬅️
TT_RETURN   = "RETURN"     # ➡️
TT_IF       = "IF"         # 🐈‍⬛

# Arithmetics
TT_PLUS     = "PLUS"       # ➕
TT_MINUS    = "MINUS"      # ➖
TT_STAR     = "STAR"       # ✖️

# Comparison
TT_CMP_EQ   = "CMP_EQ"     # 🤝
TT_CMP_NEQ  = "CMP_NEQ"    # 🙅
TT_CMP_GT   = "CMP_GT"     # ⟰
TT_CMP_LT   = "CMP_LT"     # ⟱
TT_CMP_GTE  = "CMP_GTE"    # ⟰=
TT_CMP_LTE  = "CMP_LTE"    # ⟱=

TT_UNKNOWN  = "UNKNOWN"

KEYWORDS = {
    "🛎️overflow", "on", "off", # Pragma
    "🐾else",                 # If-else
}

@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    col: int

class ASTNode:
    """Base class for all AST nodes."""
    pass

FactorNode = Union['IDNode', 'NumberNode', 'BoolNode']
ExprNode = Union[FactorNode, 'BinaryOpNode']
StmtNode = Union['DeclNode', 'AssignNode', 'IfNode']

@dataclass
class IDNode(ASTNode):
    name: str

@dataclass
class NumberNode(ASTNode):
    value: str 

@dataclass
class BoolNode(ASTNode):
    """Represents 😺 (true) or 😿 (false)"""
    token: Token

@dataclass
class BinaryOpNode(ASTNode):
    """Represents ➕, ➖, ✖️, 🤝, 🙅, ⟰, ⟱, ⟰=, ⟱="""
    op: Token
    left: FactorNode
    right: FactorNode

@dataclass
class DeclNode(ASTNode):
    """Declaration: 🧊 🐾32 x { 10 }"""
    mutability: Token
    type_name: Token
    var_id: IDNode
    initial_expr: ExprNode

@dataclass
class CodeBlockNode(ASTNode):
    """Code block: { stmt+ }"""
    statements: List[StmtNode]

@dataclass
class IfNode(ASTNode):
    """If-Else: 🐈‍⬛ expr { ... } 🐾else { ... }"""
    condition: ExprNode
    then_block: CodeBlockNode
    else_block: Optional[CodeBlockNode]

@dataclass
class AssignNode(ASTNode):
    """Assignment: x ⬅️ expr"""
    var_id: IDNode
    new_value: ExprNode

@dataclass
class ReturnNode(ASTNode):
    """Return: ➡️ expr"""
    expr: ExprNode

@dataclass
class PragmaNode(ASTNode):
    """Pragma: 🛎️overflow on|off"""
    setting: Token

@dataclass
class ProgramNode(ASTNode):
    """Root program node"""
    pragma: Optional[PragmaNode]
    statements: List[StmtNode]
    return_stmt: Optional[ReturnNode]

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.line = 1
        self.col = 1
        self.n = len(text)

    def _peek(self) -> str:
        return self.text[self.i] if self.i < self.n else ""
    
    def _peek_n(self, n: int) -> str:
        """Returns next n symbols"""
        return self.text[self.i : self.i + n]

    def _advance(self, count: int = 1) -> str:
        ch = ""
        for _ in range(count):
            ch = self.text[self.i] if self.i < self.n else ""
            if ch:
                self.i += 1
                if ch == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
        return ch

    def _make(self, t: str, lex: str, line: int, col: int) -> Token:
        return Token(t, lex, line, col)

    def tokens(self) -> List[Token]:
        toks: List[Token] = []
        S_INITIAL, S_IDENT, S_NUM = 0, 1, 2
        state = S_INITIAL
        buf = ""
        tok_line = self.line
        tok_col  = self.col

        def flush_ident():
            nonlocal buf
            if not buf:
                return
            ttype = TT_KEYWORD if buf in KEYWORDS else TT_IDENT
            toks.append(self._make(ttype, buf, tok_line, tok_col))
            buf = ""

        def flush_number():
            nonlocal buf
            if not buf:
                return
            toks.append(self._make(TT_NUMBER, buf, tok_line, tok_col))
            buf = ""

        while True:
            ch = self._peek()

            if state == S_INITIAL:
                if ch == "":
                    break
                
                if ch == '/':
                    if self._peek_n(2) == '//':
                        while ch and ch != '\n':
                            ch = self._advance()
                        if ch == '\n':
                            self._advance()
                        toks.append(self._make(TT_NEWLINE, "\\n", self.line-1, 1))
                        continue

                if ch in ' \t\r':
                    self._advance()
                    continue
                if ch == '\n':
                    self._advance()
                    toks.append(self._make(TT_NEWLINE, "\\n", self.line-1, 1))
                    continue

                if ch.isalpha():
                    state = S_IDENT
                    buf = ch
                    tok_line, tok_col = self.line, self.col
                    self._advance()
                    continue
                if ch.isdigit():
                    state = S_NUM
                    buf = ch
                    tok_line, tok_col = self.line, self.col
                    self._advance()
                    continue

                if ch == '{':
                    self._advance()
                    toks.append(self._make(TT_LBRACE, "{", self.line, self.col-1)); continue
                if ch == '}':
                    self._advance()
                    toks.append(self._make(TT_RBRACE, "}", self.line, self.col-1)); continue

                
                # Types (🐾32, 🐾64, 🎏)
                if ch == '🐾':
                    if self._peek_n(5) == '🐾else': 
                        toks.append(self._make(TT_KEYWORD, "🐾else", self.line, self.col)); 
                        self._advance(5); 
                        continue
                    if self._peek_n(3) == '🐾32':
                        toks.append(self._make(TT_TYPE_32, "🐾32", self.line, self.col)); self._advance(3); continue
                    if self._peek_n(3) == '🐾64':
                        toks.append(self._make(TT_TYPE_64, "🐾64", self.line, self.col)); self._advance(3); continue
                    
                if ch == '🎏':
                    toks.append(self._make(TT_TYPE_BOOL, "🎏", self.line, self.col)); self._advance(); continue
                
                # Literals (😺, 😿)
                if ch == '😺':
                    toks.append(self._make(TT_LIT_TRUE, "😺", self.line, self.col)); self._advance(); continue
                if ch == '😿':
                    toks.append(self._make(TT_LIT_FALSE, "😿", self.line, self.col)); self._advance(); continue
                
                # Mutability (🧊, 🪄)
                if ch == '🧊':
                    toks.append(self._make(TT_MUT_CONST, "🧊", self.line, self.col)); self._advance(); continue
                if ch == '🪄':
                    toks.append(self._make(TT_MUT_VAR, "🪄", self.line, self.col)); self._advance(); continue
                
                # Management (🐈‍⬛, ➡️)
                if ch == '🐈':
                    if self._peek_n(3) == '🐈‍⬛':
                        toks.append(self._make(TT_IF, "🐈‍⬛", self.line, self.col))
                        self._advance(3)
                        continue
                
                if ch == '➡':
                    if self._peek_n(2) == '➡️':
                        toks.append(self._make(TT_RETURN, "➡️", self.line, self.col))
                        self._advance(2)
                        continue
                
                # Assignment (⬅️)
                if ch == '⬅':
                    if self._peek_n(2) == '⬅️':
                        toks.append(self._make(TT_ASSIGN, "⬅️", self.line, self.col))
                        self._advance(2)
                        continue
                
                # Arithmetics (➕, ➖, ✖️)
                if ch == '➕':
                    toks.append(self._make(TT_PLUS, "➕", self.line, self.col)); self._advance(); continue
                if ch == '➖':
                    toks.append(self._make(TT_MINUS, "➖", self.line, self.col)); self._advance(); continue
                if ch == '✖':
                    if self._peek_n(2) == '✖️':
                        toks.append(self._make(TT_STAR, "✖️", self.line, self.col))
                        self._advance(2)
                        continue
                
                # Comparison (🤝, 🙅, ⟰, ⟱)
                if ch == '🤝':
                    toks.append(self._make(TT_CMP_EQ, "🤝", self.line, self.col)); self._advance(); continue
                if ch == '🙅':
                    toks.append(self._make(TT_CMP_NEQ, "🙅", self.line, self.col)); self._advance(); continue
                
                if ch == '⟰':
                    if self._peek_n(2) == '⟰=':
                        toks.append(self._make(TT_CMP_GTE, "⟰=", self.line, self.col)); self._advance(2); continue
                    else:
                        toks.append(self._make(TT_CMP_GT, "⟰", self.line, self.col)); self._advance(); continue
                
                if ch == '⟱':
                    if self._peek_n(2) == '⟱=':
                        toks.append(self._make(TT_CMP_LTE, "⟱=", self.line, self.col)); self._advance(2); continue
                    else:
                        toks.append(self._make(TT_CMP_LT, "⟱", self.line, self.col)); self._advance(); continue

                # Pragma (🛎️)
                if ch == '🛎':
                    if self._peek_n(10) == '🛎️overflow': 
                        toks.append(self._make(TT_KEYWORD, "🛎️overflow", self.line, self.col)); 
                        self._advance(10); 
                        continue

                # Unknown symbol
                self._advance()
                toks.append(self._make(TT_UNKNOWN, ch, self.line, self.col-1))
                continue

            elif state == S_IDENT:
                if ch.isalnum():
                    buf += ch
                    self._advance()
                    continue
                flush_ident()
                state = S_INITIAL
                continue

            elif state == S_NUM:
                if ch.isdigit():
                    buf += ch
                    self._advance()
                    continue
                flush_number()
                state = S_INITIAL
                continue

        # Очистка буферів в кінці файлу
        if state == S_IDENT:
            flush_ident()
        elif state == S_NUM:
            flush_number()

        toks.append(self._make(TT_EOF, "", self.line, self.col))
        return toks

class CompileError(Exception): pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.toks = tokens
        self.i = 0
        self.arith_ops = (TT_PLUS, TT_MINUS, TT_STAR)
        self.cmp_ops = (
            TT_CMP_EQ, TT_CMP_NEQ, TT_CMP_GT, TT_CMP_LT, TT_CMP_GTE, TT_CMP_LTE
        )

    def _peek(self) -> Token:
        return self.toks[self.i]

    def _advance(self) -> Token:
        t = self._peek()
        if t.type != TT_EOF:
            self.i += 1
        return t
    
    def _match(self, *types: str) -> Optional[Token]:
        """If the current token = one of the types, consume it and return it."""
        t = self._peek()
        if t.type in types:
            self._advance()
            return t
        return None

    def _expect(self, typ: str, msg: str) -> Token:
        t = self._peek()
        if t.type != typ:
            raise CompileError(f"[line {t.line}, col {t.col}] {msg}, got {t.type} '{t.lexeme}'")
        return self._advance()

    def _skip_newlines(self):
        """Skips all consecutive NEWLINE tokens."""
        while self._peek().type == TT_NEWLINE:
            self._advance()

    # factor ::= ID | number | "😺" | "😿"
    def parse_factor(self) -> FactorNode:
        t = self._peek()
        if t.type == TT_IDENT:
            self._advance()
            return IDNode(name=t.lexeme)
        elif t.type == TT_NUMBER:
            self._advance()
            return NumberNode(value=t.lexeme)
        elif t.type in (TT_LIT_TRUE, TT_LIT_FALSE):
            self._advance()
            return BoolNode(token=t)
        
        raise CompileError(f"[line {t.line}, col {t.col}] expected factor (IDENT, NUMBER, 😺, 😿), got {t.type} '{t.lexeme}'")

    # expr ::= factor [ (comp_op | arith_op) factor ]
    def parse_expr(self) -> ExprNode:
        lhs: FactorNode = self.parse_factor()

        t = self._peek()
        op_types = self.arith_ops + self.cmp_ops
        
        if t.type in op_types:
            op_tok = self._advance()
            rhs: FactorNode = self.parse_factor()
            return BinaryOpNode(op=op_tok, left=lhs, right=rhs)
        
        return lhs

    # decl ::= mutability type ID "{" expr "}"
    # mutability ::= "🧊" | "🪄"
    # type ::= "🐾32" | "🐾64" | "🎏"
    def parse_decl(self) -> DeclNode:
        mut_tok = self._match(TT_MUT_CONST, TT_MUT_VAR)
        if not mut_tok:
            raise CompileError(f"[line {self._peek().line}] expected mutability (🧊 or 🪄)")
        
        type_tok = self._match(TT_TYPE_32, TT_TYPE_64, TT_TYPE_BOOL)
        if not type_tok:
            raise CompileError(f"[line {self._peek().line}] expected type (🐾32, 🐾64, 🎏)")

        ident_tok = self._expect(TT_IDENT, "expected variable name after type")
        
        self._expect(TT_LBRACE, "expected '{' after variable name")
        val_expr: ExprNode = self.parse_expr()
        self._expect(TT_RBRACE, "expected '}' after initializer")
        
        return DeclNode(
            mutability=mut_tok,
            type_name=type_tok,
            var_id=IDNode(name=ident_tok.lexeme),
            initial_expr=val_expr
        )

    # assign ::= ID "⬅️" expr
    def parse_assign(self) -> AssignNode:
        ident_tok = self._expect(TT_IDENT, "expected variable name for assignment")
        self._expect(TT_ASSIGN, "expected '⬅️' after variable name")
        val_expr: ExprNode = self.parse_expr()
        return AssignNode(var_id=IDNode(name=ident_tok.lexeme), new_value=val_expr)

    def parse_code_block(self) -> CodeBlockNode:
        statements: List[StmtNode] = []
        self._expect(TT_LBRACE, "expected '{' to begin code block")
        self._skip_newlines()

        if self._peek().type == TT_RBRACE:
            raise CompileError(f"[line {self._peek().line}] if/else blocks cannot be empty")

        while self._peek().type != TT_RBRACE and self._peek().type != TT_EOF:
            statements.append(self.parse_stmt())
            self._skip_newlines()
        
        self._expect(TT_RBRACE, "expected '}' to end code block")
        return CodeBlockNode(statements=statements)

    # ifStmt ::= "🐈‍⬛" expr "{" stmt+ "}" ["🐾else" "{" stmt+ "}"]
    def parse_if(self) -> IfNode:
        self._expect(TT_IF, "expected '🐈‍⬛' keyword")
        
        condition = self.parse_expr() 
        self._skip_newlines()
        
        then_block = self.parse_code_block()
        else_block = None
        
        self._skip_newlines()
        t = self._peek()
        if t.type == TT_KEYWORD and t.lexeme == "🐾else":
            self._advance()
            self._skip_newlines()
            else_block = self.parse_code_block()
            
        return IfNode(condition=condition, then_block=then_block, else_block=else_block)

    # returnStmt ::= "➡️" expr
    def parse_return_stmt(self) -> ReturnNode:
        self._expect(TT_RETURN, "expected '➡️' keyword")
        expr: ExprNode = self.parse_expr() 
        return ReturnNode(expr=expr)

    # stmt ::= decl | assign | ifStmt
    def parse_stmt(self) -> StmtNode:
        t = self._peek()
        
        if t.type in (TT_MUT_CONST, TT_MUT_VAR):
            return self.parse_decl()
        
        elif t.type == TT_IDENT:
            return self.parse_assign()
            
        elif t.type == TT_IF:
            return self.parse_if()
            
        raise CompileError(f"[line {t.line}, col {t.col}] unexpected statement start {t.type} '{t.lexeme}'")

    # pragma ::= "🛎️overflow" ("on" | "off")
    def parse_pragma(self) -> Optional[PragmaNode]:
        t = self._peek()
        if t.type == TT_KEYWORD and t.lexeme == "🛎️overflow":
            self._advance()
            setting_tok = self._peek()
            if setting_tok.type == TT_KEYWORD and setting_tok.lexeme in ("on", "off"):
                self._advance()
                return PragmaNode(setting=setting_tok)
            else:
                raise CompileError(f"[line {t.line}] 🛎️overflow must be followed by 'on' or 'off'")
        return None

    # program ::= [pragma] stmt* [returnStmt]
    def parse_program(self) -> ProgramNode:
        statements: List[StmtNode] = []
        return_stmt: Optional[ReturnNode] = None
        
        self._skip_newlines()
        pragma = self.parse_pragma()
        
        if pragma:
            self._skip_newlines()

        while True:
            t = self._peek()
            if t.type == TT_EOF:
                break
                
            if t.type == TT_RETURN:
                return_stmt = self.parse_return_stmt()
                self._skip_newlines()
                if self._peek().type != TT_EOF:
                    raise CompileError(f"[line {self._peek().line}] unexpected statements after '➡️' (return)")
                break
            
            statements.append(self.parse_stmt())
            self._skip_newlines()

        return ProgramNode(pragma=pragma, statements=statements, return_stmt=return_stmt)

    def parse(self) -> ProgramNode:
        return self.parse_program()
    

def compile_file(inp: str, outp: str) -> None:
    src = open(inp, "r", encoding="utf-8").read()
    
    lex = Lexer(src)
    toks = lex.tokens()
    
    parser = Parser(toks)
    try:
        ast_root = parser.parse()
        
        print("--- AST Output ---")
        print(ast_root)
        print("------------------")
        
    except CompileError as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        sys.exit(2)
        
    with open(outp, "w", encoding="utf-8") as f:
        f.write(str(ast_root))

def main():
    if len(sys.argv) != 3:
        print("Usage: compiler.py <input.txt> <output.ast>", file=sys.stderr)
        sys.exit(1)
    compile_file(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()