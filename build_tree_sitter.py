# build_tree_sitter.py
from tree_sitter import Language
import os

# Ensure tree-sitter-javascript is in the right spot
if not os.path.exists("tree-sitter-javascript"):
    print("Please clone tree-sitter-javascript into this directory first!")
    exit(1)

# Build the shared library
Language.build_library('build/my-languages.so', ['tree-sitter-javascript'])
print("Built my-languages.so successfully!")