#!/usr/bin/env python
import atexit
import copy
import itertools
import os
import re
import readline
import sys


class ParseError(Exception):
    pass


class RunError(Exception):
    pass


class Mae:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}
        if not parent:
            self.globalize()

    def globalize(self):
        self.vars = {
            "def": define,
            "=": eq,
            "this": ths,
            "next": nxt,
            "prn": prn,
            "add": add,
            "rem": rem,
        }
        [self.evaluate(e) for e in PRELUDE]

    def bind(self, k, v):
        self.vars[k] = v

    def lookup(self, k):
        if k in self.vars:
            return self.vars[k]
        if self.parent:
            return self.parent.lookup(k)
        raise RunError(f"no variable named {k}")

    def bindings(self):
        if not self.parent:
            return f"bindings: {self.vars}"
        return f"bindings: {self.vars}, parent: {self.parent.bindings()}"

    def evaluate(self, expr):
        return expr.evaluate(self)


class Expr:
    pass


class Val(Expr):
    def evaluate(self, m):
        return self


class Var(Expr):
    def __init__(self, name):
        self.name = name

    def evaluate(self, m):
        return m.lookup(self.name).evaluate(m)

    def apply(self, m):
        return self.env.evaluate(self.env.lookup(self.name))

    def __repr__(self):
        return self.name

    def __eq__(self, o):
        return self.name == str(o)

    def __hash__(self):
        return hash(self.name)


class Map(Val):
    def __init__(self, m):
        self.m = m

    def evaluate(self, m):
        return Map({m.evaluate(k): m.evaluate(v) for k, v in self.m.items()})

    def apply(self, args, m):
        if len(args) != 1:
            raise RunError(
                f"map can only applied to one argument (got ({', '.join(str(a) for a in args)}))!"
            )

        return self.m.get(m.evaluate(args[0]), Map({}))

    def this(self):
        l = list(self.m.items())
        if not l:
            return Map({})
        if len(l) == 1:
            return l[0][0]
        return Map(dict([l[0]]))

    def next(self):
        l = list(self.m.items())
        if not l:
            return Map({})
        if len(l) == 1:
            return l[0][1]
        return Map(dict(l[1:]))

    def __repr__(self):
        return str(self.m)

    def __eq__(self, o):
        return self.m == o.m

    def __hash__(self):
        return hash(str(self))


class Fn(Val):
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def evaluate(self, env):
        return Closure(self, env)

    def __repr__(self):
        return f"{{({' '.join(str(a) for a in self.args)}) -> {self.body}}}"


class Closure(Val):
    def __init__(self, f, env):
        self.f = f
        self.env = env

    def apply(self, args, env):
        e = self.env
        m = Mae(parent=e)
        if len(args) != len(self.f.args):
            raise RunError(
                f"function called with {len(args)} arguments, but expected {len(self.f.args)}."
            )
        for k, v in zip(self.f.args, args):
            m.bind(k.name, env.evaluate(v))
        return m.evaluate(self.f.body)

    def __repr__(self):
        return f"{{({' '.join(str(a) for a in self.f.args)}) -> {self.f.body}}}"


class Primitive(Val):
    def __init__(self, f):
        self.f = f

    def apply(self, args, env):
        return self.f(env, args)

    def __repr__(self):
        return "<primitive>"


class App(Expr):
    def __init__(self, f, args):
        self.f = f
        self.args = args

    def evaluate(self, env):
        return env.evaluate(self.f).apply(self.args, env)

    def __repr__(self):
        return f"({self.f} {' '.join(str(a) for a in self.args)})"

    def __getitem__(self, key):
        if key == 0:
            return self.f
        if type(key) is slice:
            s = slice(key.start - 1 if key.start else None, key.stop, key.step)
            return self.args[s]
        return self.args[key - 1]

    def to_list(self):
        l = self.args
        if self.f:
            return [self.f, *l]
        return l


def def_(m, args):
    l = len(args)
    if l != 2:
        raise RunError(f"def takes two arguments, {l} given.")
    v = m.evaluate(args[1])
    m.bind(args[0].name, v)
    return v


def eq_(m, args):
    l = len(args)
    if l != 2:
        raise RunError(f"= takes two arguments, {l} given.")
    if m.evaluate(args[0]) == m.evaluate(args[1]):
        return Map({Map({}): Map({})})
    else:
        return Map({})


def ths_(m, args):
    l = len(args)
    if l != 1:
        raise RunError(f"this takes one argument, {l} given.")
    return m.evaluate(args[0]).this()


def nxt_(m, args):
    l = len(args)
    if l != 1:
        raise RunError(f"next takes one argument, {l} given.")
    return m.evaluate(args[0]).next()


def prn_(m, args):
    print(*(m.evaluate(a) for a in args))

    return Map({})


def add_(m, args):
    res = {}
    for a in args:
        res = {**res, **(m.evaluate(a).m)}
    return Map(res)


def rem_(m, args):
    l = len(args)
    if l != 2:
        raise RunError(f"rem takes two arguments, {l} given.")
    res = copy.deepcopy(m.evaluate(args[0]).m)
    k = m.evaluate(args[1])
    del res[k]
    return Map(res)


define = Primitive(def_)
eq = Primitive(eq_)
nxt = Primitive(nxt_)
ths = Primitive(ths_)
prn = Primitive(prn_)
add = Primitive(add_)
rem = Primitive(rem_)


def tokenize(s):
    s = s.replace(",", " ").replace(":", " ")
    special = "(){}[]"

    for c in special:
        s = s.replace(c, f" {c} ")

    return s.split()


def pairs(l):
    if len(l) % 2 != 0:
        raise ParseError("Map length not even.")
    for i in range(0, len(l), 2):
        yield l[i : i + 2]


def empty():
    return Map({})


def make_int(i):
    return Map({make_int(e): empty() for e in range(i)})


def build_map(l):
    def enum_(l):
        for i, v in enumerate(l):
            yield make_int(i), v

    return Map(dict(enum_(l)))


def build_fn(l):
    if len(l) != 3:
        raise ParseError("Malformed function definition: {l}.")
    return Fn(l[0].to_list(), l[2])


def read_tokens(tokens):
    openers = "({["
    closers = {
        "(": ")",
        "[": "]",
        "{": "}",
    }
    builders = {
        "(": lambda l: App(l[0], l[1:]) if l else App(None, []),
        "[": build_map,
        "{": lambda l: build_fn(l)
        if len(l) > 2 and l[1] == "->"
        else Map(dict(pairs(l))),
    }
    if not tokens:
        raise ParseError("Unclosed expression.")

    token = tokens.pop(0)

    if token in openers:
        l = []
        closer = closers[token]
        build = builders[token]
        while tokens[0] != closer:
            l.append(read_tokens(tokens))
        tokens.pop(0)
        return build(l)
    elif token in "}])":
        raise ParseError("Unexpected expression close.")
    elif token.isdigit():
        return make_int(int(token))
    else:
        return Var(token)


def strip_comments(s):
    return re.sub(";.*", "", s)


def parse(s):
    s = strip_comments(s)
    tokens = tokenize(s)

    res = []
    while tokens:
        res.append(read_tokens(tokens))

    return res


class Completer:
    def __init__(self, m):
        self.m = m

    def complete(self, text, state):
        if state == 0:
            if text:
                self.matches = [s for s in self.m.vars if s.startswith(text)]
            else:
                self.matches = self.m.vars.keys()

        if len(self.matches) > state:
            return self.matches[state]


def setup_readline(m):
    histfile = os.path.join(os.path.expanduser("~"), ".mae_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)

    readline.set_completer(Completer(m).complete)


def repl():
    m = Mae()
    setup_readline(m)
    while True:
        try:
            expr = input("> ")
        except EOFError:
            return

        if expr == ":q":
            print("vale.")
            return

        try:
            expr = parse(expr)
        except ParseError as e:
            print(e)
            continue

        try:
            print("=>", [m.evaluate(e) for e in expr][-1])
        except RunError as e:
            print(e)


def file_(name):
    with open(name) as f:
        m = Mae()
        [m.evaluate(e) for e in parse(f.read())]


with open("prelude.mae") as f:
    PRELUDE = parse(f.read())


if __name__ == "__main__":
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        file_(sys.argv[1])
    else:
        print("usage: ./mae.py <file>")
