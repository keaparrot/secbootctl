import unittest

from tests import unittest_helper


class TestAppController(unittest_helper.ControllerTestCase):
    FEATURE_NAME = 'app'


if __name__ == '__main__':
    unittest.main()
