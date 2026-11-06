from django.contrib.auth.base_user import BaseUserManager


def normalizar_email(email):
    """E-mails são guardados e comparados sempre em minúsculas, sem espaços nas pontas."""
    return (email or "").strip().lower()


class UsuarioManager(BaseUserManager):
    """Cria usuários do atende+, que entram pelo e-mail em vez de um nome de usuário."""

    use_in_migrations = True

    def get_by_natural_key(self, email):
        # Usado no login: encontra o usuário independentemente de maiúsculas.
        return self.get(email=normalizar_email(email))

    def _criar(self, email, password, **campos):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        perfil = campos.get("perfil", self.model.Perfil.CLIENTE)
        if perfil == self.model.Perfil.CLIENTE and not campos.get("empresa"):
            raise ValueError("Clientes precisam informar a empresa.")
        usuario = self.model(email=normalizar_email(email), **campos)
        usuario.set_password(password)  # grava só o hash da senha (RNF03)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **campos):
        campos.setdefault("is_superuser", False)
        return self._criar(email, password, **campos)

    def create_superuser(self, email, password=None, **campos):
        """Usado pelo comando `createsuperuser`: cria um administrador com acesso total."""
        campos["perfil"] = self.model.Perfil.ADMINISTRADOR
        campos["is_superuser"] = True
        return self._criar(email, password, **campos)
