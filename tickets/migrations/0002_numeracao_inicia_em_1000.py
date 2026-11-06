# RN01: o primeiro ticket recebe o número 1000.

from django.db import migrations

PRIMEIRO_NUMERO = 1000


def iniciar_numeracao(apps, schema_editor):
    conexao = schema_editor.connection
    with conexao.cursor() as cursor:
        if conexao.vendor == "sqlite":
            # No SQLite, o próximo id vem da tabela interna sqlite_sequence.
            cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'ticket'")
            cursor.execute(
                "INSERT INTO sqlite_sequence (name, seq) VALUES ('ticket', %s)", [PRIMEIRO_NUMERO - 1]
            )
        elif conexao.vendor == "mysql":  # MySQL e MariaDB
            cursor.execute(f"ALTER TABLE ticket AUTO_INCREMENT = {PRIMEIRO_NUMERO}")


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(iniciar_numeracao, migrations.RunPython.noop),
    ]
