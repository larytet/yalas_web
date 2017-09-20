import os
import unittest
import tempfile


from yalas import import app

class AppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app
        app.testing = True

    def tearDown(self):
        os.close(self.db_fd)

    def test_index(self):
        rv = self.app.get('/')
        assert b'Index Page' in rv.data
        
if __name__ == '__main__':
    unittest.main()