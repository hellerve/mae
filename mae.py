#!/usr/bin/env python
import sys


class ParseError(Exception): pass
class RunError(Exception): pass


class Mae:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}
        if not parent:
            self.globalize()


    def globalize(self):
        self.vars = {
            "def": define,
            "fn": fn,
            "=": eq,
            "this": ths,
            "next": nxt,
            "prn": prn,
            "add": add,
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
    def __repr__(self):
        return self.__str__()


class Val(Expr):
    def evaluate(self, m):
        return self

    def __repr__(self):
        return self.__str__()


class Var(Expr):
    def __init__(self, name):
        self.name = name

    def evaluate(self, m):
        return m.lookup(self.name).evaluate(m)

    def apply(self, m):
        return self.env.evaluate(self.env.lookup(self.name))

    def __str__(self):
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
                f"map can only applied to one argument (got {args})!"
            )

        return self.m[m.evaluate(args[0])]

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

    def __str__(self):
        return str(self.m)

    def __eq__(self, o):
        return self.m == o.m

    def __hash__(self):
        return hash(str(self))


class Fn(Val):
    def __init__(self, args, body, env):
        self.args = args
        self.body = body
        self.env = env

    def apply(self, args, env):
        e = self.env
        m = Mae(parent=e)
        if len(args) != len(self.args):
            raise RunError(
                f"function called with {len(args)} arguments, but expected {len(self.args)}."
            )
        for k, v in zip(self.args, args):
            m.bind(k.name, env.evaluate(v))
        return [m.evaluate(e) for e in self.body][-1]

    def __str__(self):
        return f"(fn ({' '.join(str(a) for a in self.args)}) {' '.join(str(b) for b in self.body)})"


class Primitive(Val):
    def __init__(self, f):
        self.f = f

    def apply(self, args, env):
        return self.f(env, args)

    def __str__(self):
        return "<primitive>"


class App(Expr):
    def __init__(self, f, args):
        self.f = f
        self.args = args

    def evaluate(self, env):
        return env.evaluate(self.f).apply(self.args, env)

    def __str__(self):
        return f"({self.f} {' '.join(str(a) for a in self.args)})"

    def __getitem__(self, key):
        if key == 0:
            return self.f
        if type(key) is slice:
            s = slice(
                key.start-1 if key.start else None,
                key.stop,
                key.step
            )
            return self.args[s]
        return self.args[key-1]

    def to_list(self):
        l = self.args
        if self.f:
            return [self.f, *l]
        return l


def def_(m, args):
    l = len(args)
    if l < 2:
        raise RunError(
            f"def takes at least two arguments, {l} given."
        )
    if type(args[0]) is not App:
        if l != 2:
            raise RunError(
                f"def of a variable takes at least two arguments, {l} given."
            )
        v = m.evaluate(args[1])
        m.bind(args[0].name, v)
        return v
    v = Fn(args[0][1:], args[1:], m)
    v.env = m
    m.bind(args[0][0], v)
    return v


def fn_(m, args):
    l = len(args)
    if l < 2:
        raise RunError(
            f"fn takes at least two arguments, {l} given."
        )
    if type(args[0]) is not App:
        raise RunError(
            f"fn takes a list as first argument."
        )
    return Fn(args[0].to_list(), args[1:], m)


def eq_(m, args):
    l = len(args)
    if l != 2:
        raise RunError(
            f"= takes two arguments, {l} given."
        )
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


define = Primitive(def_)
fn = Primitive(fn_)
eq = Primitive(eq_)
nxt = Primitive(nxt_)
ths = Primitive(ths_)
prn = Primitive(prn_)
add = Primitive(add_)


def tokenize(s):
    special = "(){}[]"

    for c in special:
        s = s.replace(c, f" {c} ")

    return s.split()


def pairs(l):
    if len(l) % 2 != 0:
        raise ParseError("Map length not even.")
    for i in range (0, len(l), 2):
        yield l[i:i+2]



def empty(): return Map({})


def make_int(i):
    return Map({make_int(e): empty() for e in range(i)})


def build_map(l):
    def enum_(l):
        for i, v in enumerate(l):
            yield make_int(i), v
    return Map(dict(enum_(l)))


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
        "{": lambda l: Map(dict(pairs(l))),
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


def parse(s):
    tokens = tokenize(s)

    res = []
    while tokens:
        res.append(read_tokens(tokens))

    return res


def repl():
    m = Mae()
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


if __name__ == '__main__':
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        file_(sys.argv[1])
    else:
        print("usage: ./mae.py <file>")
