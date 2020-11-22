# mae.

*m*aps *a*re *e*verything. an experiment in language construction with an
inicidental [lisp syntax](#why-lisp-syntax).

## syntax.

we use lisp syntax. definitions use `def`. maps use curly braces. commas and
colons are whitespace. calling maps is indexing into them.

### why lisp syntax?

because i am lazy, lisp is easy to parse, and syntax doesn’t matter. i mean,
did you look at the error messages?

## data types

the fun is in the definitions.

### booleans.

`true` is any non-empty map. `false` is the empty map. any map can be a
boolean.

### integers.

numerical values are maps with `n` entries. any map can be an integer. there is
a reader expression for array syntax using brackets; it just generates the
indices. there are reader literals, but since the only way to generate a key is
to generate a recursively different map, any number over 5 is gnarly, and over
25 it becomes borderline unusable. fun.

### arrays.

maps with integral keys can be used like arrays.

## control structures

or: is this your card?

### conditionals.

conditionals are maps from `true` and `false` to other values. we can thus
define the function

```clojure
(def (if cond a b)
  (({true a false b} cond))) ; branches are nullary fns
```

multi-branch conditionals work the same way, but there is no function for them.

### loops

loops happen when we iterate over maps. you have `foldr`, `map`, and `filter`
at your disposal.

```clojure
(def (print-all-keys m) (map (fn (k v) (prn k)) m))
```

## faqs

### is this functional programming?

it is maptional programming, naturally.

### should i just read this, chuckle, and leave?

yes, you should.

### how can i support the development of mae?

mae is not currently being developed, but, if you want to show your love, be
kind to someone else.
