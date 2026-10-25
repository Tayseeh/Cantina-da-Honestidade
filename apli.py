from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
import math
#http://127.0.0.1:5000/login
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
    #-- executa_sql ("DROP TABLE IF EXISTS produtos") # Apaga a antiga para atualizar

    sql_criar_tabela = """
    CREATE TABLE IF NOT EXISTS produtos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(30) NOT NULL,
        valor_compra DECIMAL(10, 2) NOT NULL,
        valor_venda DECIMAL(10, 2) NOT NULL,
        quantidade_estoque INT NOT NULL,
        descricao TEXT,
        ativo BOOLEAN DEFAULT 1
    )
    """
    executa_sql(sql_criar_tabela)
    print("Verificação concluída: Tabela 'produtos' pronta")

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

# --- rota do crud  ---
@app.route('/')
def index():
    if 'logado' not in session:
        return redirect(url_for('login'))

    pagina = request.args.get('page', 1, type=int)
    busca = request.args.get('q', '').strip()
    itens_por_pagina = 5
    offset = (pagina - 1) * itens_por_pagina

    if busca:
        termo_banco = f"%{busca}%"
        resultado_total = executa_sql("SELECT COUNT(*) as total FROM produtos WHERE nome LIKE %s AND ativo = 1", (termo_banco,))
        sql = "SELECT * FROM produtos WHERE nome LIKE %s AND ativo = 1 ORDER BY nome ASC LIMIT %s OFFSET %s"
        produtos = executa_sql(sql, (termo_banco, itens_por_pagina, offset))
    else:
        resultado_total = executa_sql("SELECT COUNT(*) as total FROM produtos WHERE ativo = 1")
        sql = "SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome ASC LIMIT %s OFFSET %s"
        produtos = executa_sql(sql, (itens_por_pagina, offset))
    total_produtos = resultado_total[0]['total'] if resultado_total else 0
    total_paginas = math.ceil(total_produtos / itens_por_pagina)

    return render_template('index.html', produtos=produtos, pagina_atual=pagina, total_paginas=total_paginas, busca=busca)
#-- rota incluir
@app.route('/incluir', methods=['POST'])
def incluir():
    nome = request.form['nome'].strip()
    descricao = request.form.get('descricao', '').strip()
    valor_compra = request.form['valor_compra'].replace(',', '.')
    valor_venda = request.form['valor_venda'].replace(',', '.')
    estoque = request.form['estoque']

    #-- VALIDAÇÃO DE DUPLICIDADE
    sql_busca = "SELECT id FROM produtos WHERE LOWER(nome) = LOWER(%s) AND ativo = 1"
    produto_existente = executa_sql(sql_busca, (nome,))
    
    if produto_existente:
        flash(f'O produto "{nome}" já está cadastrado! Se precisar atualizar use o botão Editar.', 'warning')
        return redirect(url_for('index'))
    
    sql_inserir = "INSERT INTO produtos (nome, descricao, valor_compra, valor_venda, quantidade_estoque) VALUES (%s, %s, %s, %s, %s)"
    executa_sql(sql_inserir, (nome, descricao, float(valor_compra), float(valor_venda), int(estoque)))
    flash('Produto incluído com sucesso!', 'success')
    return redirect(url_for('index'))

#-- rota edit
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        descricao = request.form.get('descricao', '').strip()
        valor_compra = request.form['valor_compra'].replace(',', '.')
        valor_venda = request.form['valor_venda'].replace(',', '.')
        estoque = request.form['estoque']
        
        # função UPDATE
        sql = "UPDATE produtos SET nome=%s, descricao=%s, valor_compra=%s, valor_venda=%s, quantidade_estoque=%s WHERE id=%s"
        executa_sql(sql, (nome, descricao, float(valor_compra), float(valor_venda), int(estoque), id))
        
        flash('Produto alterado com sucesso', 'success')
        return redirect(url_for('index'))
    else:
        produtos = executa_sql("SELECT * FROM produtos WHERE id = %s", (id,))
        produto = produtos[0] if produtos else None
        return render_template('editar.html', produto=produto)
#-- rota excluir
@app.route('/excluir/<int:id>')
def excluir(id):
    #Soft Delete
    executa_sql("UPDATE produtos SET ativo = 0 WHERE id = %s", (id,))
    flash('Produto excluído com sucesso', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    inicializar_banco() 
    app.run(debug=True)