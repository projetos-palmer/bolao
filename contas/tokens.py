from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TokenConfirmacaoEmail(PasswordResetTokenGenerator):
    """Token seguro para confirmação de e-mail."""

    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk)
            + str(timestamp)
            + str(user.email_confirmado)
            + str(user.email)
        )


token_confirmacao = TokenConfirmacaoEmail()
