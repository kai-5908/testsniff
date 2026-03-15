from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from tokenize import TokenInfo

from testsniff.parser.ast_index import ASTIndex
from testsniff.parser.tokens import collect_tokens


@dataclass(slots=True)
class ModuleContext:
    path: Path
    source_text: str
    tree: ast.AST
    tokens: tuple[TokenInfo, ...]
    index: ASTIndex

    @classmethod
    def from_source(cls, path: Path, source_text: str) -> ModuleContext:
        tree = ast.parse(source_text, filename=str(path))
        tokens = collect_tokens(source_text)
        index = ASTIndex.from_tree(tree)
        return cls(path=path, source_text=source_text, tree=tree, tokens=tokens, index=index)
