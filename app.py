import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            tipo TEXT CHECK(tipo IN ('ingreso', 'gasto'))
        )
    ''')
    conn.commit()
    conn.close()


init_db()


def obtener_resumen_mes(categoria=None):
    """
    Obtiene el resumen de ingresos y gastos.
    Si se especifica una categoría, se filtran los datos según ella.
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if categoria:
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS ingresos,
                SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END) AS gastos
            FROM transacciones
            WHERE categoria = ?
        ''', (categoria,))
    else:
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS ingresos,
                SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END) AS gastos
            FROM transacciones
        ''')

    resultado = cursor.fetchone()
    conn.close()

    ingresos = resultado[0] if resultado[0] is not None else 0
    gastos = resultado[1] if resultado[1] is not None else 0

    return {
        'ingresos': ingresos,
        'gastos': gastos,
        'balance': ingresos - gastos
    }


@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Obtener categorías únicas para el datalist y el filtro
    cursor.execute('SELECT DISTINCT categoria FROM transacciones')
    categorias = [row[0] for row in cursor.fetchall()]

    # Obtener filtro de categoría de los parámetros GET
    categoria_filtro = request.args.get('categoria_filtro')
    if categoria_filtro:
        cursor.execute('SELECT * FROM transacciones WHERE categoria = ? ORDER BY fecha DESC', (categoria_filtro,))
    else:
        cursor.execute('SELECT * FROM transacciones ORDER BY fecha DESC')
    transacciones = cursor.fetchall()
    conn.close()

    # Obtener resumen filtrado si es necesario
    resumen = obtener_resumen_mes(categoria_filtro if categoria_filtro else None)

    return render_template('index.html',
                           transacciones=transacciones,
                           resumen=resumen,
                           categorias=categorias)


@app.route('/agregar', methods=['POST'])
def agregar_transaccion():
    fecha = request.form['fecha']
    categoria = request.form['categoria']
    monto = request.form['monto']
    tipo = request.form['tipo']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transacciones (fecha, categoria, monto, tipo)
        VALUES (?, ?, ?, ?)
    ''', (fecha, categoria, float(monto), tipo))
    conn.commit()
    conn.close()

    return redirect('/')


@app.route('/borrar-seleccionados', methods=['POST'])
def borrar_seleccionados():
    # Recupera los IDs de las transacciones seleccionadas
    ids = request.form.getlist('transacciones[]')
    if ids:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # Se prepara la consulta para eliminar los registros con los IDs especificados
        query = "DELETE FROM transacciones WHERE id IN ({seq})".format(
            seq=','.join(['?'] * len(ids))
        )
        cursor.execute(query, ids)
        conn.commit()
        conn.close()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
