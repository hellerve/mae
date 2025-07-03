import unittest
from mae import Mae, Map, Var, Fn, RunError

class MapMethodTests(unittest.TestCase):
    def test_this_and_next_empty(self):
        m = Map({})
        self.assertEqual(m.this(), Map({}))
        self.assertEqual(m.next(), Map({}))

    def test_this_and_next_singleton(self):
        key = Map({})
        value = Map({})
        m = Map({key: value})
        self.assertEqual(m.this(), key)
        self.assertEqual(m.next(), value)

    def test_this_and_next_multiple(self):
        key1 = Map({})
        value1 = Map({'foo': Map({})})
        key2 = Map({'bar': Map({})})
        value2 = Map({})
        m = Map({key1: value1, key2: value2})
        self.assertEqual(m.this(), Map({key1: value1}))
        self.assertEqual(m.next(), Map({key2: value2}))

    def test_apply_existing_and_missing_key(self):
        key = Map({})
        val = Map({'v': Map({})})
        m = Map({key: val})
        env = Mae()
        self.assertEqual(m.apply([key], env), val)
        self.assertEqual(m.apply([Map({Map({}): Map({})})], env), Map({}))

class ClosureAndEqTests(unittest.TestCase):
    def test_closure_wrong_argument_count(self):
        env = Mae()
        f = Fn([Var('a')], Var('a')).evaluate(env)
        with self.assertRaises(RunError):
            f.apply([], env)

    def test_eq_primitive(self):
        env = Mae()
        eq = env.lookup('=')
        m1 = Map({Map({}): Map({})})
        m2 = Map({Map({}): Map({})})
        self.assertEqual(eq.apply([m1, m2], env), Map({Map({}): Map({})}))
        m3 = Map({Map({}): Map({Map({}): Map({})})})
        self.assertEqual(eq.apply([m1, m3], env), Map({}))

if __name__ == '__main__':
    unittest.main()
