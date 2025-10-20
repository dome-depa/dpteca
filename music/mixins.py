from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

class StaffMixing(UserPassesTestMixin):

    """ scopo di mixin è fare in modo che solo lo staff possa creare nuovi artisti """

    # Utenti non autenticati vengono reindirizzati al login,
    # utenti autenticati ma non staff ricevono 403.
    raise_exception = True
    login_url = 'login'
    permission_denied_message = "Devi essere membro dello staff per accedere a questa pagina."

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        # Utente non autenticato: redirect al login
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # Utente autenticato ma senza permesso: 403
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()