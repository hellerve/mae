import unittest
from mae import Mae, Map, Var, RunError

class MapApplyTests(unittest.TestCase):
    def test_multiple_arguments_raises_runerror(self):
        env = Mae()
        m = Map({})
        args = [Var('a'), Var('b')]
        with self.assertRaises(RunError) as cm:
            m.apply(args, env)
        msg = str(cm.exception)
        self.assertIn('map can only applied to one argument', msg)
        # ensure all arguments are listed in the message
        self.assertIn('a', msg)
        self.assertIn('b', msg)

if __name__ == '__main__':
    unittest.main()
