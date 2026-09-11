import pathlib, sys, unittest

root = pathlib.Path(__file__).parent
sys.path.insert(0, str(root))

loader = unittest.TestLoader()
suite = loader.discover(str(root / "tests"), pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
