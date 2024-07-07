from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  

class Catalogo:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            if (err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR):
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            codigo INT AUTO_INCREMENT PRIMARY KEY,
            descripcion VARCHAR(255) NOT NULL,
            cantidad INT NOT NULL,
            precio DECIMAL(10, 2) NOT NULL)''')
        self.conn.commit()

        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)

    def agregar_producto(self, descripcion, cantidad, precio):
        sql = "INSERT INTO productos (descripcion, cantidad, precio) VALUES (%s, %s, %s)"
        valores = (descripcion, cantidad, precio)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.lastrowid

    def consultar_producto(self, codigo):
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {codigo}")
        return self.cursor.fetchone()

    def modificar_producto(self, codigo, nueva_descripcion, nueva_cantidad, nuevo_precio):
        sql = "UPDATE productos SET descripcion = %s, cantidad = %s, precio = %s WHERE codigo = %s"
        valores = (nueva_descripcion, nueva_cantidad, nuevo_precio, codigo)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    def listar_productos(self):
        self.cursor.execute("SELECT * FROM productos")
        productos = self.cursor.fetchall()

        total_cantidad = sum(p['cantidad'] for p in productos)
        total_precio = sum(p['cantidad'] * p['precio'] for p in productos)

        productos.append({
            'codigo': 'Totales',
            'descripcion': '',
            'cantidad': total_cantidad,
            'precio': total_precio
        })

        return productos

    def eliminar_producto(self, codigo):
        self.cursor.execute(f"DELETE FROM productos WHERE codigo = {codigo}")
        self.conn.commit()
        return self.cursor.rowcount > 0

    def mostrar_producto(self, codigo):
        producto = self.consultar_producto(codigo)
        if (producto):
            print("-" * 40)
            print(f"Código.....: {producto['codigo']}")
            print(f"Descripción: {producto['descripcion']}")
            print(f"Cantidad...: {producto['cantidad']}")
            print(f"Precio.....: {producto['precio']}")
            print("-" * 40)
        else:
            print("Producto no encontrado.")

catalogo = Catalogo(host='pabarreiro.mysql.pythonanywhere-services.com', user='pabarreiro', password='729183Pablo', database='pabarreiro$miapp')

@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = catalogo.listar_productos()
    return jsonify(productos)

@app.route("/productos/<int:codigo>", methods=["GET"])
def mostrar_producto(codigo):
    producto = catalogo.consultar_producto(codigo)
    if producto:
        return jsonify(producto), 201
    else:
        return "Producto no encontrado", 404

@app.route("/productos", methods=["POST"])
def agregar_producto():
    descripcion = request.form['descripcion']
    cantidad = request.form['cantidad']
    precio = request.form['precio']

    nuevo_codigo = catalogo.agregar_producto(descripcion, cantidad, precio)
    if nuevo_codigo:
        return jsonify({"mensaje": "Producto agregado correctamente.", "codigo": nuevo_codigo}), 201
    else:
        return jsonify({"mensaje": "Error al agregar el producto."}), 500

@app.route("/productos/<int:codigo>", methods=["PUT"])
def modificar_producto(codigo):
    nueva_descripcion = request.form.get("descripcion")
    nueva_cantidad = request.form.get("cantidad")
    nuevo_precio = request.form.get("precio")

    if catalogo.modificar_producto(codigo, nueva_descripcion, nueva_cantidad, nuevo_precio):
        return jsonify({"mensaje": "Producto modificado"}), 200
    else:
        return jsonify({"mensaje": "Producto no encontrado"}), 403

@app.route("/productos/<int:codigo>", methods=["DELETE"])
def eliminar_producto(codigo):
    if catalogo.eliminar_producto(codigo):
        return jsonify({"mensaje": "Producto eliminado"}), 200
    else:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

if __name__ == "__main__":
    app.run(debug=True)
