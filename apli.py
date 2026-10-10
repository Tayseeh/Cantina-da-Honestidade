from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'chave_secreta_cantina'

def executa_sql(sql, valores=None):
    try:
        myconn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='', # Coloque sua senha do MySQL
            database='cantina',
        )
        mycur = myconn.cursor(dictionary=True) 

        if valores:
            mycur.execute(sql, valores)
        else:
            mycur.execute(sql)

        if sql.strip().lower().startswith('select'):
            registros = mycur.fetchall()
        else:
            myconn.commit()
            registros = []

        mycur.close()
        myconn.close()
        return registros

    except Error as error:
        print(f"Erro no Banco de Dados: {error}")
        if 'myconn' in locals() and myconn.is_connected():
            myconn.rollback()
            myconn.close()
        return None

def inicializar_banco():
    # Comando SQL
    sql_criar_tabela = """
    CREATE TABLE IF NOT EXISTS produtos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(50) NOT NULL,
        preco DECIMAL(10, 2) NOT NULL,
        quantidade_estoque INT NOT NULL
    )
    """
    executa_sql(sql_criar_tabela)
    print("Verificação do banco de dados concluída: Tabela 'produtos' pronta!")

    # --- Rota de login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        
        if usuario == 'admin' and senha == '123':
            session['logado'] = True
            flash('Bem-vindo!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# --- Rota do crud  ---
@app.route('/')
def index():
    if 'logado' not in session:
        return redirect(url_for('login'))

    # função READ
    produtos = executa_sql("SELECT * FROM produtos ORDER BY id DESC")
    return render_template('index.html', produtos=produtos)

@app.route('/incluir', methods=['POST'])
def incluir():
    nome = request.form['nome'].strip()
    preco = request.form['preco'].replace(',', '.')
    estoque = request.form['estoque']

    # função CREATE
    sql = "INSERT INTO produtos (nome, preco, quantidade_estoque) VALUES (%s, %s, %s)"
    executa_sql(sql, (nome, float(preco), int(estoque)))
    
    flash('Produto incluído com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        preco = request.form['preco'].replace(',', '.')
        estoque = request.form['estoque']
        
        # função UPDATE
        sql = "UPDATE produtos SET nome=%s, preco=%s, quantidade_estoque=%s WHERE id=%s"
        executa_sql(sql, (nome, float(preco), int(estoque), id))
        
        flash('Produto alterado com sucesso!', 'success')
        return redirect(url_for('index'))
    else:
        produtos = executa_sql("SELECT * FROM produtos WHERE id = %s", (id,))
        produto = produtos[0] if produtos else None
        return render_template('editar.html', produto=produto)

@app.route('/excluir/<int:id>')
def excluir(id):
    # função DELETE
    executa_sql("DELETE FROM produtos WHERE id = %s", (id,))
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    inicializar_banco() 
    app.run(debug=True)