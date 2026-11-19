
import sqlite3
from pathlib import Path
from datetime import date, datetime


# =========================================================
# CONFIGURACAO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "finance.db"


# =========================================================
# CONEXAO
# =========================================================

def conectar():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(DB_PATH)
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


# =========================================================
# CRIACAO DAS TABELAS
# =========================================================

def criar_tabelas():
    with conectar() as conexao:

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL
                    CHECK(type IN ('income', 'expense')),
                UNIQUE(name, type)
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                account_type TEXT NOT NULL,
                initial_balance_cents INTEGER NOT NULL DEFAULT 0
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount_cents INTEGER NOT NULL
                    CHECK(amount_cents > 0),
                type TEXT NOT NULL
                    CHECK(type IN ('income', 'expense')),
                transaction_date TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                notes TEXT,
                FOREIGN KEY(category_id) REFERENCES categories(id),
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date
            ON transactions(transaction_date)
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_account
            ON transactions(account_id)
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_category
            ON transactions(category_id)
        """)

        categorias = [
            ("Salário", "income"),
            ("Investimentos", "income"),
            ("Outras receitas", "income"),
            ("Alimentação", "expense"),
            ("Transporte", "expense"),
            ("Moradia", "expense"),
            ("Lazer", "expense"),
            ("Saúde", "expense"),
            ("Educação", "expense"),
            ("Outras despesas", "expense")
        ]

        conexao.executemany("""
            INSERT OR IGNORE INTO categories (name, type)
            VALUES (?, ?)
        """, categorias)


# =========================================================
# VALIDACOES AUXILIARES
# =========================================================

def validar_data(data_texto):
    try:
        datetime.strptime(data_texto, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("Data inválida. Utilize AAAA-MM-DD.")


def validar_tipo(tipo):
    if tipo not in ("income", "expense"):
        raise ValueError("Tipo inválido.")


# =========================================================
# CONTAS
# =========================================================

def criar_conta(nome, tipo="checking", saldo_inicial=0):
    nome = nome.strip()

    if not nome:
        raise ValueError("Informe o nome da conta.")

    if saldo_inicial < 0:
        raise ValueError("O saldo inicial não pode ser negativo.")

    with conectar() as conexao:
        try:
            conexao.execute("""
                INSERT INTO accounts (
                    name,
                    account_type,
                    initial_balance_cents
                )
                VALUES (?, ?, ?)
            """, (nome, tipo, saldo_inicial))

        except sqlite3.IntegrityError:
            raise ValueError("Já existe uma conta com esse nome.")


def listar_contas():
    with conectar() as conexao:
        return conexao.execute("""
            SELECT
                id,
                name,
                account_type,
                initial_balance_cents
            FROM accounts
            ORDER BY name
        """).fetchall()


def listar_contas_com_saldo():
    with conectar() as conexao:
        return conexao.execute("""
            SELECT
                a.id,
                a.name,
                a.account_type,
                a.initial_balance_cents,

                a.initial_balance_cents
                + COALESCE(SUM(
                    CASE
                        WHEN t.type = 'income'
                            THEN t.amount_cents
                        WHEN t.type = 'expense'
                            THEN -t.amount_cents
                        ELSE 0
                    END
                ), 0) AS current_balance

            FROM accounts a

            LEFT JOIN transactions t
                ON t.account_id = a.id

            GROUP BY a.id

            ORDER BY a.name
        """).fetchall()


def atualizar_conta(conta_id, nome, tipo, saldo_inicial):
    nome = nome.strip()

    if not nome:
        raise ValueError("Informe o nome da conta.")

    if saldo_inicial < 0:
        raise ValueError("O saldo inicial não pode ser negativo.")

    with conectar() as conexao:
        try:
            cursor = conexao.execute("""
                UPDATE accounts
                SET name = ?,
                    account_type = ?,
                    initial_balance_cents = ?
                WHERE id = ?
            """, (nome, tipo, saldo_inicial, conta_id))

            if cursor.rowcount == 0:
                raise ValueError("Conta não encontrada.")

        except sqlite3.IntegrityError:
            raise ValueError("Já existe uma conta com esse nome.")


def excluir_conta(conta_id):
    with conectar() as conexao:

        quantidade = conexao.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE account_id = ?
        """, (conta_id,)).fetchone()[0]

        if quantidade > 0:
            raise ValueError(
                "Esta conta possui transações. "
                "Exclua ou transfira essas transações antes."
            )

        total = conexao.execute("""
            SELECT COUNT(*) FROM accounts
        """).fetchone()[0]

        if total <= 1:
            raise ValueError(
                "O aplicativo precisa ter pelo menos uma conta."
            )

        cursor = conexao.execute("""
            DELETE FROM accounts WHERE id = ?
        """, (conta_id,))

        if cursor.rowcount == 0:
            raise ValueError("Conta não encontrada.")


# =========================================================
# CATEGORIAS
# =========================================================

def listar_categorias(tipo=None):
    with conectar() as conexao:

        if tipo:
            validar_tipo(tipo)

            return conexao.execute("""
                SELECT id, name, type
                FROM categories
                WHERE type = ?
                ORDER BY name
            """, (tipo,)).fetchall()

        return conexao.execute("""
            SELECT id, name, type
            FROM categories
            ORDER BY type, name
        """).fetchall()


def criar_categoria(nome, tipo):
    nome = nome.strip()
    validar_tipo(tipo)

    if not nome:
        raise ValueError("Informe o nome da categoria.")

    with conectar() as conexao:
        try:
            conexao.execute("""
                INSERT INTO categories (name, type)
                VALUES (?, ?)
            """, (nome, tipo))

        except sqlite3.IntegrityError:
            raise ValueError("Essa categoria já existe.")


def atualizar_categoria(categoria_id, nome, tipo):
    nome = nome.strip()
    validar_tipo(tipo)

    if not nome:
        raise ValueError("Informe o nome da categoria.")

    with conectar() as conexao:
        try:
            cursor = conexao.execute("""
                UPDATE categories
                SET name = ?,
                    type = ?
                WHERE id = ?
            """, (nome, tipo, categoria_id))

            if cursor.rowcount == 0:
                raise ValueError("Categoria não encontrada.")

        except sqlite3.IntegrityError:
            raise ValueError(
                "Já existe uma categoria com esse nome e tipo."
            )


def excluir_categoria(categoria_id):
    with conectar() as conexao:

        quantidade = conexao.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE category_id = ?
        """, (categoria_id,)).fetchone()[0]

        if quantidade > 0:
            raise ValueError(
                "Esta categoria possui transações vinculadas."
            )

        cursor = conexao.execute("""
            DELETE FROM categories WHERE id = ?
        """, (categoria_id,))

        if cursor.rowcount == 0:
            raise ValueError("Categoria não encontrada.")


# =========================================================
# TRANSACOES
# =========================================================

def adicionar_transacao(
    descricao,
    valor_centavos,
    tipo,
    data,
    categoria_id,
    conta_id,
    observacoes=None
):
    descricao = descricao.strip()
    validar_tipo(tipo)
    validar_data(data)

    if not descricao:
        raise ValueError("A descrição não pode ficar vazia.")

    if valor_centavos <= 0:
        raise ValueError("O valor precisa ser positivo.")

    with conectar() as conexao:

        categoria = conexao.execute("""
            SELECT type
            FROM categories
            WHERE id = ?
        """, (categoria_id,)).fetchone()

        if categoria is None or categoria[0] != tipo:
            raise ValueError("Categoria inexistente ou incompatível.")

        conta = conexao.execute("""
            SELECT id FROM accounts WHERE id = ?
        """, (conta_id,)).fetchone()

        if conta is None:
            raise ValueError("Conta não encontrada.")

        conexao.execute("""
            INSERT INTO transactions (
                description,
                amount_cents,
                type,
                transaction_date,
                category_id,
                account_id,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            descricao,
            valor_centavos,
            tipo,
            data,
            categoria_id,
            conta_id,
            observacoes
        ))


def listar_transacoes(
    busca=None,
    tipo=None,
    categoria_id=None,
    conta_id=None,
    data_inicio=None,
    data_fim=None
):
    consulta = """
        SELECT
            t.id,
            t.description,
            t.amount_cents,
            t.type,
            t.transaction_date,
            c.name,
            a.name,
            t.category_id,
            t.account_id,
            t.notes

        FROM transactions t

        JOIN categories c
            ON t.category_id = c.id

        JOIN accounts a
            ON t.account_id = a.id

        WHERE 1 = 1
    """

    parametros = []

    if busca:
        consulta += """
            AND (
                t.description LIKE ?
                OR c.name LIKE ?
                OR a.name LIKE ?
                OR t.notes LIKE ?
            )
        """

        termo = f"%{busca.strip()}%"
        parametros.extend([termo, termo, termo, termo])

    if tipo:
        validar_tipo(tipo)
        consulta += " AND t.type = ?"
        parametros.append(tipo)

    if categoria_id:
        consulta += " AND t.category_id = ?"
        parametros.append(categoria_id)

    if conta_id:
        consulta += " AND t.account_id = ?"
        parametros.append(conta_id)

    if data_inicio:
        validar_data(data_inicio)
        consulta += " AND t.transaction_date >= ?"
        parametros.append(data_inicio)

    if data_fim:
        validar_data(data_fim)
        consulta += " AND t.transaction_date <= ?"
        parametros.append(data_fim)

    consulta += """
        ORDER BY t.transaction_date DESC, t.id DESC
    """

    with conectar() as conexao:
        return conexao.execute(
            consulta,
            parametros
        ).fetchall()


def excluir_transacao(transacao_id):
    with conectar() as conexao:
        cursor = conexao.execute("""
            DELETE FROM transactions
            WHERE id = ?
        """, (transacao_id,))

        if cursor.rowcount == 0:
            raise ValueError("Transação não encontrada.")


def atualizar_transacao(
    transacao_id,
    descricao,
    valor_centavos,
    tipo,
    data,
    categoria_id,
    conta_id,
    observacoes=None
):
    descricao = descricao.strip()
    validar_tipo(tipo)
    validar_data(data)

    if not descricao:
        raise ValueError("A descrição não pode ficar vazia.")

    if valor_centavos <= 0:
        raise ValueError("O valor precisa ser maior que zero.")

    with conectar() as conexao:

        categoria = conexao.execute("""
            SELECT type
            FROM categories
            WHERE id = ?
        """, (categoria_id,)).fetchone()

        if categoria is None or categoria[0] != tipo:
            raise ValueError("Categoria inexistente ou incompatível.")

        conta = conexao.execute("""
            SELECT id FROM accounts WHERE id = ?
        """, (conta_id,)).fetchone()

        if conta is None:
            raise ValueError("Conta não encontrada.")

        cursor = conexao.execute("""
            UPDATE transactions
            SET description = ?,
                amount_cents = ?,
                type = ?,
                transaction_date = ?,
                category_id = ?,
                account_id = ?,
                notes = COALESCE(?, notes)
            WHERE id = ?
        """, (
            descricao,
            valor_centavos,
            tipo,
            data,
            categoria_id,
            conta_id,
            observacoes,
            transacao_id
        ))

        if cursor.rowcount == 0:
            raise ValueError("Transação não encontrada.")


# =========================================================
# RESUMO FINANCEIRO
# =========================================================

def obter_resumo(
    data_inicio=None,
    data_fim=None,
    conta_id=None
):
    filtros = []
    parametros = []

    if data_inicio:
        validar_data(data_inicio)
        filtros.append("transaction_date >= ?")
        parametros.append(data_inicio)

    if data_fim:
        validar_data(data_fim)
        filtros.append("transaction_date <= ?")
        parametros.append(data_fim)

    if conta_id:
        filtros.append("account_id = ?")
        parametros.append(conta_id)

    where = ""

    if filtros:
        where = "WHERE " + " AND ".join(filtros)

    with conectar() as conexao:

        saldo_inicial = conexao.execute("""
            SELECT COALESCE(SUM(initial_balance_cents), 0)
            FROM accounts
        """).fetchone()[0]

        totais = conexao.execute(f"""
            SELECT
                COALESCE(SUM(
                    CASE WHEN type = 'income'
                    THEN amount_cents ELSE 0 END
                ), 0),

                COALESCE(SUM(
                    CASE WHEN type = 'expense'
                    THEN amount_cents ELSE 0 END
                ), 0)

            FROM transactions
            {where}
        """, parametros).fetchone()

        receitas, despesas = totais

        saldo = saldo_inicial

        movimentacoes = conexao.execute("""
            SELECT type, amount_cents
            FROM transactions
        """).fetchall()

        for tipo, valor in movimentacoes:
            if tipo == "income":
                saldo += valor
            else:
                saldo -= valor

        return {
            "saldo": saldo,
            "receitas": receitas,
            "despesas": despesas
        }


# =========================================================
# HISTORICO MENSAL
# =========================================================

def obter_historico_periodo(data_inicio=None, data_fim=None, agrupamento="dia"):
    if agrupamento not in ("dia", "mes"):
        raise ValueError("Agrupamento deve ser 'dia' ou 'mes'.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        if data_inicio is None:
            cursor.execute(
                "SELECT MIN(transaction_date) FROM transactions"
            )
            primeira_data = cursor.fetchone()[0]

            if primeira_data is None:
                return []

            data_inicio = primeira_data

        if data_fim is None:
            data_fim = date.today().isoformat()

        inicio = date.fromisoformat(data_inicio)
        fim = date.fromisoformat(data_fim)

        if inicio > fim:
            return []

        cursor.execute(
            """
            SELECT transaction_date, LOWER(type), SUM(amount_cents)
            FROM transactions
            WHERE transaction_date BETWEEN ? AND ?
            GROUP BY transaction_date, LOWER(type)
            ORDER BY transaction_date
            """,
            (data_inicio, data_fim)
        )

        registros = cursor.fetchall()

        valores = {}

        for data, tipo, total in registros:
            chave = data if agrupamento == "dia" else data[:7]

            if chave not in valores:
                valores[chave] = {"receitas": 0, "despesas": 0}

            if tipo == "receita":
                valores[chave]["receitas"] += total or 0
            elif tipo == "despesa":
                valores[chave]["despesas"] += total or 0

        resultado = []

        if agrupamento == "dia":
            quantidade_dias = (fim - inicio).days + 1

            for i in range(quantidade_dias):
                dia = date.fromordinal(inicio.toordinal() + i)
                chave = dia.isoformat()
                dados = valores.get(
                    chave,
                    {"receitas": 0, "despesas": 0}
                )

                resultado.append((
                    chave,
                    dados["receitas"],
                    dados["despesas"]
                ))

        else:
            ano = inicio.year
            mes = inicio.month

            while (ano, mes) <= (fim.year, fim.month):
                chave = f"{ano:04d}-{mes:02d}"
                dados = valores.get(
                    chave,
                    {"receitas": 0, "despesas": 0}
                )

                resultado.append((
                    chave,
                    dados["receitas"] / 100,
                    dados["despesas"] / 100
                ))

                mes += 1

                if mes == 13:
                    mes = 1
                    ano += 1

        return resultado

    finally:
        conexao.close()


# =========================================================
# DESPESAS POR CATEGORIA
# =========================================================

def obter_despesas_por_categoria(
    data_inicio=None,
    data_fim=None,
    conta_id=None
):
    consulta = """
        SELECT
            c.id,
            c.name,
            COALESCE(SUM(t.amount_cents), 0) AS total

        FROM categories c

        LEFT JOIN transactions t
            ON t.category_id = c.id
            AND t.type = 'expense'
    """

    parametros = []
    condicoes = []

    if data_inicio:
        validar_data(data_inicio)
        condicoes.append("t.transaction_date >= ?")
        parametros.append(data_inicio)

    if data_fim:
        validar_data(data_fim)
        condicoes.append("t.transaction_date <= ?")
        parametros.append(data_fim)

    if conta_id:
        condicoes.append("t.account_id = ?")
        parametros.append(conta_id)

    if condicoes:
        consulta += " AND " + " AND ".join(condicoes)

    consulta += """
        WHERE c.type = 'expense'
        GROUP BY c.id, c.name
        HAVING total > 0
        ORDER BY total DESC
    """

    with conectar() as conexao:
        return conexao.execute(
            consulta,
            parametros
        ).fetchall()


# =========================================================
# INICIALIZACAO MANUAL
# =========================================================

if __name__ == "__main__":
    criar_tabelas()
    print("Banco de dados inicializado.")
    print(f"Localização: {DB_PATH}")
