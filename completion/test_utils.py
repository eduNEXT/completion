"""
Common functionality to support writing tests around completion.
"""
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
from datetime import datetime

from django.contrib.auth.models import User
import factory
from factory.django import DjangoModelFactory
import mock
from opaque_keys.edx.keys import UsageKey, CourseKey
from pytz import UTC

from .models import BlockCompletion


class UserFactory(DjangoModelFactory):
    """
    A Factory for User objects.
    """
    class Meta(object):
        model = User
        django_get_or_create = ('email', 'username')

    _DEFAULT_PASSWORD = 'test'

    username = factory.Sequence(u'robot{0}'.format)
    email = factory.Sequence(u'robot+test+{0}@edx.org'.format)
    password = factory.PostGenerationMethodCall('set_password', _DEFAULT_PASSWORD)
    first_name = factory.Sequence(u'Robot{0}'.format)
    last_name = 'Test'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1, tzinfo=UTC)
    date_joined = datetime(2011, 1, 1, tzinfo=UTC)


class CompletionSetUpMixin(object):
    """
    Mixin to provide set_up_completion() function to child TestCase classes.
    """
    COMPLETION_SWITCH_ENABLED = False

    @classmethod
    def setUpClass(cls):
        super(CompletionSetUpMixin, cls).setUpClass()
        cls.waffle_patcher = mock.patch('completion.waffle.waffle')
        cls.mock_waffle = cls.waffle_patcher.start()
        cls.mock_waffle.return_value.is_enabled.return_value = cls.COMPLETION_SWITCH_ENABLED

    @classmethod
    def tearDownClass(cls):
        super(CompletionSetUpMixin, cls).tearDownClass()
        cls.waffle_patcher.stop()

    def setUp(self):
        super(CompletionSetUpMixin, self).setUp()
        self.block_key = UsageKey.from_string('block-v1:edx+test+run+type@video+block@doggos')
        self.course_key = CourseKey.from_string('course-v1:edx+test+run')
        self.user = UserFactory()

    def set_up_completion(self):
        """
        Creates a stub completion record for a (user, course, block).
        """
        self.completion = BlockCompletion.objects.create(
            user=self.user,
            course_key=self.block_key.course_key,
            block_type=self.block_key.block_type,
            block_key=self.block_key,
            completion=0.5,
        )

    @contextmanager
    def override_completion_switch(self, enabled):
        """
        Overrides the completion-enabled waffle switch value within a context.
        """
        self.mock_waffle.return_value.is_enabled.return_value = enabled
        yield
        self.mock_waffle.return_value.is_enabled.return_value = self.COMPLETION_SWITCH_ENABLED
