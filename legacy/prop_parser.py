import re
from lark import Lark
from tree_sitter import Language, Parser
from particle_utils import logger

# Tree-sitter setup
try:
    JS_LANG = Language("/app/tree-sitter-libs/javascript.so", "javascript")
    TS_PARSER = Parser()
    TS_PARSER.set_language(JS_LANG)
except ImportError:
    # If tree-sitter Python package isn't installed, this will fail—fallback to Lark
    TS_PARSER = None
    logger.debug("Tree-sitter Python package not found, falling back")

# Lark fallback
signature_grammar = """
    start: signature
    signature: EXPORT DEFAULT? (FUNCTION | CONST | ARROW) IDENTIFIER? "(" params? ")" block
    params: param ("," param)*
    param: IDENTIFIER (":" TYPE)? ("=" default)?
    default: VALUE
    block: "{" "}" | "=>" expr
    expr: /.+/
    EXPORT: "export"
    DEFAULT: "default"
    FUNCTION: "function"
    CONST: "const"
    ARROW: "=>"
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    TYPE: /[a-zA-Z_][a-zA-Z0-9_]*(?:\[\])?/
    VALUE: /[^,)}]+/
    %ignore /\s+/
    %ignore /\/\/.*/
    %ignore /\/\*[\s\S]*?\*\//
"""
lark_parser = Lark(signature_grammar, start="start")

def extract_props(content, rich=True):
    """Extract props with Tree-sitter (if available), falling back to Lark then regex."""
    props = []

    # Tree-sitter attempt
    if TS_PARSER:
        try:
            tree = TS_PARSER.parse(content.encode())
            query = JS_LANG.query("""
                (jsx_element
                  (jsx_opening_element
                    (jsx_attribute (property_identifier) @jsx_prop)))
            """)
            captures = query.captures(tree.root_node)
            for node, capture_name in captures:
                prop = node.text.decode()
                if prop not in ["className", "style", "key", "ref", "name", "size", "color"]:
                    desc = prop
                    if rich and "on" in prop.lower():
                        desc += ": function"
                    props.append(desc)
            props = list(dict.fromkeys(props))
            if props and rich:
                if "useScrollValue" in content:
                    props.extend(["scrollY", "previousScrollY", "isScrollingUp"])
                if "useNavigation" in content:
                    props.append("currentTab")
                if "useRole" in content:
                    props.append("isAttendee")
                if "map(" in content and "currentTabs" in content:
                    props.append("tabs: array")
            if props:
                logger.debug(f"Tree-sitter found props: {props}")
                return props
        except Exception as e:
            logger.debug(f"Tree-sitter parse failed: {e}")

    # Lark fallback
    try:
        tree = lark_parser.parse(content)
        if not tree.find_data("param"):
            logger.debug("No props in function signature (Lark)")
        else:
            for param in tree.find_data("param"):
                prop_name = next(param.children[0].children).value
                prop_type = next((c.value for c in param.children if c.type == "TYPE"), None)
                desc = f"{prop_name}: {prop_type}" if rich and prop_type else prop_name
                props.append(desc)
        if props:
            return props
    except Exception as e:
        logger.debug(f"Lark parse failed: {e}")

    # Regex fallback
    jsx_props = re.findall(r"<[A-Z][\w]*\s+[^>]*?([a-zA-Z]+)=", content, re.DOTALL)
    seen = set()
    for prop in jsx_props:
        if prop not in ["className", "style", "key", "ref", "name", "size", "color"] and prop not in seen:
            desc = prop
            if rich:
                if "on" in prop.lower():
                    desc += ": function"
                elif prop.lower() in ["active", "visible", "disabled"]:
                    desc += ": boolean"
                elif f"{prop}." in content or f"{prop}[" in content:
                    desc += ": array | object"
            props.append(desc)
            seen.add(prop)

    # Hook inference
    if rich:
        if "useScrollValue" in content:
            props.extend(["scrollY", "previousScrollY", "isScrollingUp"])
        if "useNavigation" in content:
            props.append("currentTab")
        if "useRole" in content:
            props.append("isAttendee")
        if "map(" in content and "currentTabs" in content:
            props.append("tabs: array")

    return list(dict.fromkeys(props))