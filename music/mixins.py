from django.contrib.auth.mixins import UserPassesTestMixin

class StaffMixing(UserPassesTestMixin):

    """ scopo di mixin è fare in modo che solo lo staff possa creare nuovi artisti """

    def test_func(self):
        return self.request.user.is_staff