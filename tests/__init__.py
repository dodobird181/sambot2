import os
import random
import shutil
import unittest.mock

import settings


class UuidSeederMixin:
    """
    Seed uuid.uuid4 generation. NOTE: This mixin requires
    that children call super().setUp() when overriding.
    """

    def setUp(self):
        super().setUp()
        random.seed("uuidseeder!")
        os.urandom = random.randbytes


class DatabaseTestCase(UuidSeederMixin, unittest.TestCase):
    """
    Base class for database-modifying tests. This class creates a
    temporary test database directory and seeds uuid.uuid4 generation.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.PICKLE_DB_PATH = "tstpkldb/"
        os.mkdir(settings.PICKLE_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.PICKLE_DB_PATH)
