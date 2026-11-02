import ast, inspect, re, textwrap

HINT = re.compile(r"require|auth|token|key|verify|session|admin|secret|login|csrf", re.I)

def audit(app):
    print("# before_request hooks by blueprint (None = whole app)")
    for bp, funcs in app.before_request_funcs.items():
        print(bp, [f"{f.__module__}.{f.__name__}" for f in funcs])
    print("# routes")
    for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        view = app.view_functions[r.endpoint]
        wrapped = hasattr(view, "__wrapped__")
        fn = inspect.unwrap(view)
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        except (OSError, TypeError, SyntaxError, IndentationError):
            print(f"{r.rule}\t{r.endpoint}\t?")
            continue
        # first real function definition; fall back to the whole snippet
        node = next((n for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))), tree)
        decos = [ast.unparse(d) for d in getattr(node, "decorator_list", [])
                 if "route" not in ast.unparse(d)]
        calls = {ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)}
        hits = sorted(c for c in calls if HINT.search(c))
        print(f"{r.rule}\t{r.endpoint}\twrapped={wrapped}\tdecorators={decos}\tcalls={hits}")

if __name__ == "__main__":
    from app import create_app
    audit(create_app(check_database=False, load_environment=False))