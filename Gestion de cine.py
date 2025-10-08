import uuid
import random
from datetime import datetime, timedelta
from collections import defaultdict

class Pelicula:
    def __init__(self, titulo, genero, duracion, clasificacion, coleccionable=None, precio_coleccionable=0):
        self.titulo, self.genero, self.duracion, self.clasificacion = titulo, genero, duracion, clasificacion
        self.horarios = []  # Lista de tuplas (horario: datetime, sala: Sala)
        self.coleccionable = coleccionable  # Nombre del coleccionable
        self.precio_coleccionable = precio_coleccionable  # Precio extra o 0 si es gratis

    def mostrar_informacion(self):
        info = f"{self.titulo} ({self.genero}, {self.duracion} min, {self.clasificacion})"
        if self.coleccionable:
            costo = "gratis" if self.precio_coleccionable == 0 else f"por ${self.precio_coleccionable} extra"
            info += f" - Coleccionable: {self.coleccionable} ({costo})"
        return info

    def agregar_horario(self, horario, sala):
        self.horarios.append((horario, sala))
        sala.agregar_horario(horario)

    def get_alternative_horarios(self, current_horario):
        return sorted([(h, s.get_occupancy(h)) for h, s in self.horarios if h != current_horario], key=lambda x: x[1])

class Sala:
    def __init__(self, numero, filas=5, columnas=10):
        self.numero, self.filas, self.columnas = numero, filas, columnas
        self.horarios_asientos = {}  # horario -> {asiento: ocupado}

    def agregar_horario(self, horario):
        self.horarios_asientos[horario] = {f"{chr(65 + i)}{j + 1}": False for i in range(self.filas) for j in range(self.columnas)}

    def mostrar_asientos(self, horario):
        if horario not in self.horarios_asientos:
            raise ValueError("No hay función en este horario.")
        print(f"Asientos para horario {horario} en sala {self.numero}:")
        for i in range(self.filas):
            print(f"{chr(65 + i)} {' '.join('[X]' if self.horarios_asientos[horario][f'{chr(65 + i)}{j + 1}'] else '[ ]' for j in range(self.columnas))}")

    def ocupar_asientos(self, horario, asientos):
        if horario not in self.horarios_asientos:
            raise ValueError("No hay función en este horario.")
        for asiento in asientos:
            if asiento not in self.horarios_asientos[horario] or self.horarios_asientos[horario][asiento]:
                raise ValueError(f"Asiento {asiento} inválido o ya ocupado.")
            self.horarios_asientos[horario][asiento] = True

    def liberar_asientos(self, horario, asientos):
        if horario not in self.horarios_asientos:
            raise ValueError("No hay función en este horario.")
        for asiento in asientos:
            self.horarios_asientos[horario][asiento] = False

    def get_occupancy(self, horario):
        if horario not in self.horarios_asientos:
            return 0
        asientos = self.horarios_asientos[horario]
        return (sum(asientos.values()) / len(asientos)) * 100 if asientos else 0

    def is_full(self, horario):
        return self.get_occupancy(horario) >= 100

class Boleto:
    def __init__(self, codigo, pelicula, horario, asientos, cliente, coleccionable=None, precio_extra=0):
        self.codigo, self.pelicula, self.horario, self.asientos, self.cliente = codigo, pelicula, horario, asientos, cliente
        self.coleccionable = coleccionable
        self.precio_extra = precio_extra

    def mostrar_detalles(self):
        detalles = f"Boleto {self.codigo}: {self.pelicula.titulo} at {self.horario}, asientos: {', '.join(self.asientos)} for {self.cliente.nombre}"
        if self.coleccionable:
            detalles += f" + Coleccionable: {self.coleccionable} (${self.precio_extra})"
        return detalles

class Cine:
    def __init__(self, nombre):
        self.nombre, self.salas, self.cartelera, self.ventas = nombre, [], [], []

    def agregar_sala(self, sala):
        self.salas.append(sala)

    def agregar_pelicula(self, pelicula):
        self.cartelera.append(pelicula)

    def mostrar_cartelera(self):
        if not self.cartelera:
            return print("No hay películas en cartelera.")
        for idx, pel in enumerate(self.cartelera, 1):
            print(f"{idx}. {pel.mostrar_informacion()}")
            for i, (h, s) in enumerate(pel.horarios, 1):
                status = " (Sala llena)" if s.is_full(h) else f" (Ocupación: {s.get_occupancy(h):.2f}%)"
                print(f"   {i}. {h.strftime('%I:%M %p')} en Sala {s.numero}{status}")

    def vender_boleto(self, cliente, pelicula, horario, asientos, coleccionable=False):
        if pelicula not in self.cartelera or not (sala := next((s for h, s in pelicula.horarios if h == horario), None)):
            raise ValueError("Película o horario no disponible.")
        if sala.is_full(horario):
            raise ValueError("Sala llena.")
        sala.ocupar_asientos(horario, asientos)
        precio_extra = pelicula.precio_coleccionable if coleccionable else 0
        boleto = Boleto(uuid.uuid4().hex[:8].upper(), pelicula, horario, asientos, cliente,
                        pelicula.coleccionable if coleccionable else None, precio_extra)
        self.ventas.append(boleto)
        cliente.boletos.append(boleto)
        return boleto

    def cancelar_boleto(self, codigo):
        if not (boleto := next((b for b in self.ventas if b.codigo == codigo), None)):
            raise ValueError("Boleto no encontrado.")
        if datetime.now() >= boleto.horario:
            raise ValueError("No se puede cancelar después del inicio de la función.")
        if sala := next((s for h, s in boleto.pelicula.horarios if h == boleto.horario), None):
            sala.liberar_asientos(boleto.horario, boleto.asientos)
        self.ventas.remove(boleto)
        boleto.cliente.boletos.remove(boleto)
        return True

    def generar_reporte(self, inicio=None, fin=None):
        inicio, fin = inicio or datetime.min, fin or datetime.max
        ventas = [v for v in self.ventas if inicio <= v.horario <= fin]
        if not ventas:
            return {"mensaje": "No hay ventas en el período seleccionado."}
        vistas = defaultdict(int)
        concurrencia = defaultdict(int)
        total_por_sala = defaultdict(int)
        for v in ventas:
            vistas[v.pelicula.titulo] += len(v.asientos)
            concurrencia[(v.pelicula.titulo, v.horario)] += len(v.asientos)
            if sala := next((s for h, s in v.pelicula.horarios if h == v.horario), None):
                total_por_sala[sala.numero] += len(v.asientos)
        return {
            "pelicula_mas_vista": max(vistas, key=vistas.get, default="Ninguna"),
            "horarios_mas_concurridos": [(f"{pel} at {h}", c) for (pel, h), c in sorted(concurrencia.items(), key=lambda x: x[1], reverse=True)],
            "total_por_funcion": {f"{pel} at {h}": c for (pel, h), c in concurrencia.items()},
            "total_por_sala": dict(total_por_sala)
        }

class Cliente:
    def __init__(self, nombre, correo):
        self.nombre, self.correo, self.boletos = nombre, correo, []

    def comprar_boleto(self, cine, pelicula, horario, asientos, coleccionable=False):
        return cine.vender_boleto(self, pelicula, horario, asientos, coleccionable)

    def cancelar_boleto(self, cine, codigo):
        return cine.cancelar_boleto(codigo)

    def mostrar_boletos(self):
        if not self.boletos:
            return print("No tienes boletos.")
        for b in self.boletos:
            print(b.mostrar_detalles())

class Administrador:
    def __init__(self, nombre, id_administrador, correo):
        self.nombre, self.id_administrador, self.correo = nombre, id_administrador, correo

    def agregar_pelicula(self, cine, pelicula, horario, sala):
        cine.agregar_pelicula(pelicula)
        pelicula.agregar_horario(horario, sala)

    def consultar_reporte(self, cine, inicio=None, fin=None):
        return cine.generar_reporte(inicio, fin)

def preconfigurar_cine(cine):
    salas = [Sala(1), Sala(2)]
    for sala in salas:
        cine.agregar_sala(sala)
    peliculas = [
        Pelicula("Inception", "Ciencia Ficción", 148, "PG-13", coleccionable="Caja de Inception", precio_coleccionable=10),
        Pelicula("The Lion King", "Animación", 118, "G", coleccionable="Aviso de The Lion King", precio_coleccionable=0)
    ]
    horarios = [
        (datetime(2025, 10, 8, 19, 0), salas[0]),  # 7:00 PM
        (datetime(2025, 10, 8, 21, 30), salas[0]), # 9:30 PM
        (datetime(2025, 10, 8, 19, 30), salas[1]), # 7:30 PM
        (datetime(2025, 10, 8, 22, 0), salas[1])   # 10:00 PM
    ]
    for pel_idx, hor_slice in enumerate([slice(0, 2), slice(2, 4)]):
        pel = peliculas[pel_idx]
        for h, s in horarios[hor_slice]:
            pel.agregar_horario(h, s)
        cine.agregar_pelicula(pel)
        for h, s in pel.horarios:
            asientos_total = s.filas * s.columnas
            num_ocupados = random.randint(0, asientos_total)
            asientos_ocupados = random.sample(list(s.horarios_asientos[h].keys()), num_ocupados)
            s.ocupar_asientos(h, asientos_ocupados)

def menu_cliente(cine, cliente):
    while True:
        print("\nMenú Cliente: 1. Ver cartelera 2. Comprar boleto 3. Cancelar boleto 4. Ver mis boletos 5. Salir")
        opcion = input("Elige: ")
        if opcion == "1":
            cine.mostrar_cartelera()
        elif opcion == "2":
            cine.mostrar_cartelera()
            try:
                pel = cine.cartelera[int(input("Película (1 o 2): ")) - 1]
                print("Horarios:")
                for i, (h, s) in enumerate(pel.horarios, 1):
                    print(f"{i}. {h.strftime('%I:%M %p')} en Sala {s.numero} ({s.get_occupancy(h):.2f}%)")
                idx_hor = int(input(f"Horario (1-{len(pel.horarios)}): ")) - 1
                horario, sala = pel.horarios[idx_hor]
                if sala.get_occupancy(horario) >= 80:
                    print("Alta ocupación. Alternativas:")
                    for h, o in pel.get_alternative_horarios(horario)[:2]:
                        print(f" - {h.strftime('%I:%M %p')} ({o:.2f}%)")
                    if input("¿Continuar? (s/n): ").lower() != 's':
                        continue
                if sala.is_full(horario):
                    print("Sala llena. Elige otro horario.")
                    continue
                sala.mostrar_asientos(horario)
                # Nuevo: Permitir al usuario elegir asientos
                asientos_str = input("Ingresa los asientos (ej. A1 B2, separados por espacio): ").upper().split()
                # Validar formato de los asientos
                for asiento in asientos_str:
                    if not (len(asiento) >= 2 and asiento[0].isalpha() and asiento[1:].isdigit() and
                            ord(asiento[0]) - 65 < sala.filas and 1 <= int(asiento[1:]) <= sala.columnas):
                        raise ValueError(f"Asiento {asiento} inválido.")
                coleccionable = False
                if pel.coleccionable:
                    costo = "gratis" if pel.precio_coleccionable == 0 else f"por ${pel.precio_coleccionable} extra"
                    print(f"¡Hey! Para esta película, puedes obtener el coleccionable '{pel.coleccionable}' {costo}.")
                    if input("¿Quieres agregarlo? (s/n): ").lower() == 's':
                        coleccionable = True
                boleto = cliente.comprar_boleto(cine, pel, horario, asientos_str, coleccionable)
                print("Compra exitosa!", boleto.mostrar_detalles())
            except Exception as e:
                print(f"Error: {e}")
        elif opcion == "3" and cliente.boletos:
            try:
                cliente.mostrar_boletos()
                codigo = input("Ingresa el código del boleto a cancelar: ").upper()
                cliente.cancelar_boleto(cine, codigo)
                print("Boleto cancelado.")
            except Exception as e:
                print(f"Error: {e}")
        elif opcion == "4":
            cliente.mostrar_boletos()
        elif opcion == "5":
            break
        else:
            print("Opción inválida.")

def menu_admin(cine, admin):
    while True:
        print("\nMenú Admin: 1. Consultar reporte 2. Salir")
        if (opcion := input("Elige: ")) == "1":
            reporte = admin.consultar_reporte(cine)
            if "mensaje" in reporte:
                print(reporte["mensaje"])
            else:
                print(f"Película más vista: {reporte['pelicula_mas_vista']}")
                for h, c in reporte['horarios_mas_concurridos']:
                    print(f" - {h}: {c} entradas")
        elif opcion == "2":
            break
        else:
            print("Opción inválida.")

def main():
    cine = Cine("Cine Estrella")
    preconfigurar_cine(cine)
    admin, cliente = Administrador("Admin", "A001", "admin@cine.com"), Cliente("Cliente Ejemplo", "cliente@example.com")
    while True:
        print("\nSistema de Cine: 1. Admin 2. Cliente 3. Salir")
        opcion = input("Elige: ")
        if opcion == "1":
            menu_admin(cine, admin)
        elif opcion == "2":
            menu_cliente(cine, cliente)
        elif opcion == "3":
            break
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()