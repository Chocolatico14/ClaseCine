from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import uuid

# -------------------------
# DATACLASSES (modelo limpio)
# -------------------------

@dataclass
class Pelicula:
    titulo: str
    genero: str
    duracion: int  # minutos
    horarios: List[str] = field(default_factory=list)

    def mostrar(self) -> str:
        return f"{self.titulo} ({self.genero}) - {self.duracion}min - Horarios: {', '.join(self.horarios)}"


@dataclass
class Boleto:
    codigo: str
    pelicula: str
    horario: str
    sala: int
    asientos: List[Tuple[int, int]]  # lista de (fila, columna) 0-based
    cliente_correo: str

    def mostrar(self) -> str:
        lugares = ', '.join([f"F{f+1}C{c+1}" for f, c in self.asientos])
        return f"Boleto {self.codigo} - {self.pelicula} @ {self.horario} - Sala {self.sala} - {lugares} - Cliente: {self.cliente_correo}"


@dataclass
class Cliente:
    nombre: str
    correo: str
    boletos: List[str] = field(default_factory=list)  # guardamos códigos de boletos


@dataclass
class Administrador:
    nombre: str
    correo: Optional[str] = None


@dataclass
class Sala:
    numero: int
    filas: int = 5
    columnas: int = 5
    asientos: List[List[bool]] = field(init=False)

    def __post_init__(self):
        self.asientos = [[False for _ in range(self.columnas)] for _ in range(self.filas)]

    def mostrar_asientos(self) -> None:
        for i, fila in enumerate(self.asientos):
            estado = ' '.join('X' if ocupado else 'O' for ocupado in fila)
            print(f"Fila {i+1}: {estado}")

    def disponibles(self, lista_asientos: List[Tuple[int, int]]) -> bool:
        for f, c in lista_asientos:
            if not (0 <= f < self.filas and 0 <= c < self.columnas):
                return False
            if self.asientos[f][c]:
                return False
        return True

    def ocupar(self, lista_asientos: List[Tuple[int, int]]) -> None:
        for f, c in lista_asientos:
            self.asientos[f][c] = True

    def liberar(self, lista_asientos: List[Tuple[int, int]]) -> None:
        for f, c in lista_asientos:
            self.asientos[f][c] = False


# -------------------------
# CINE (orquestador)
# -------------------------

@dataclass
class Cine:
    nombre: str
    cartelera: List[Pelicula] = field(default_factory=list)
    salas: List[Sala] = field(default_factory=list)
    ventas: Dict[str, Boleto] = field(default_factory=dict)  # codigo -> Boleto

    def agregar_sala(self, sala: Sala) -> None:
        self.salas.append(sala)

    def agregar_pelicula(self, pelicula: Pelicula) -> None:
        self.cartelera.append(pelicula)

    def mostrar_cartelera(self) -> None:
        if not self.cartelera:
            print("Cartelera vacía.")
            return
        for p in self.cartelera:
            print("-", p.mostrar())

    def _buscar_pelicula(self, titulo: str) -> Optional[Pelicula]:
        return next((p for p in self.cartelera if p.titulo.lower() == titulo.lower()), None)

    def _buscar_sala(self, numero: int) -> Optional[Sala]:
        return next((s for s in self.salas if s.numero == numero), None)

    def vender_boleto(self, cliente: Cliente, titulo: str, horario: str, num_sala: int, asientos: List[Tuple[int, int]]):
        pelicula = self._buscar_pelicula(titulo)
        if not pelicula:
            return False, "Película no encontrada."
        if horario not in pelicula.horarios:
            return False, "Horario no disponible."
        sala = self._buscar_sala(num_sala)
        if not sala:
            return False, "Sala inexistente."
        if not sala.disponibles(asientos):
            return False, "Asientos no disponibles o inválidos."

        sala.ocupar(asientos)
        codigo = str(uuid.uuid4())[:8]
        boleto = Boleto(codigo, pelicula.titulo, horario, sala.numero, asientos, cliente.correo)
        self.ventas[codigo] = boleto
        cliente.boletos.append(codigo)

        # 🎁 NUEVA FUNCIONALIDAD: AVISO DE COLECCIONABLE
        peliculas_especiales = ["Kimetsu no Yaiba: Castillo Infinito", "Megalodon"]
        mensaje_extra = ""
        if pelicula.titulo in peliculas_especiales:
            mensaje_extra = (
                f"\n🎁 ¡Promoción especial! Al comprar '{pelicula.titulo}' "
                f"obtienes una caja coleccionable exclusiva sin costo adicional."
            )

        return True, f"{boleto.mostrar()}{mensaje_extra}"

    def cancelar_boleto(self, codigo: str, cliente: Optional[Cliente] = None):
        if codigo not in self.ventas:
            return False, "Boleto no encontrado."
        boleto = self.ventas[codigo]
        if cliente and boleto.cliente_correo != cliente.correo:
            return False, "No autorizado: el boleto no pertenece a este cliente."
        sala = self._buscar_sala(boleto.sala)
        if sala:
            sala.liberar(boleto.asientos)
        del self.ventas[codigo]
        if cliente and codigo in cliente.boletos:
            cliente.boletos.remove(codigo)
        return True, "Cancelación exitosa."

    def estadisticas(self) -> None:
        if not self.ventas:
            print("No hay ventas registradas.")
            return
        conteo = {}
        for b in self.ventas.values():
            conteo[b.pelicula] = conteo.get(b.pelicula, 0) + 1
        peli_top = max(conteo, key=conteo.get)
        print("Película más vista:", peli_top)
        print("Ventas totales:", len(self.ventas))


# -------------------------
# UTILIDADES Y MENÚ (MVP)
# -------------------------

def pedir_asientos_cantidad() -> List[Tuple[int, int]]:
    try:
        n = int(input("¿Cuántos asientos desea reservar? (ej. 1): ").strip())
    except ValueError:
        print("Entrada inválida.")
        return []
    lista = []
    for i in range(n):
        try:
            f = int(input(f"Asiento {i+1} - fila (1..): ")) - 1
            c = int(input(f"Asiento {i+1} - columna (1..): ")) - 1
            lista.append((f, c))
        except ValueError:
            print("Entrada inválida, se omite asiento.")
    return lista


def main():
    cine = Cine("Cine Universidad")
    cine.agregar_sala(Sala(numero=1, filas=6, columnas=8))
    cine.agregar_sala(Sala(numero=2, filas=5, columnas=6))

    admin = Administrador("Laura")
    cine.agregar_pelicula(Pelicula("El Viaje", "Aventura", 120, ["15:00", "18:00"]))
    cine.agregar_pelicula(Pelicula("Misterio Nocturno", "Suspenso", 95, ["16:30", "19:30"]))
    cine.agregar_pelicula(Pelicula("Kimetsu no Yaiba: Castillo Infinito", "Anime", 110, ["20:00", "22:30"]))
    cine.agregar_pelicula(Pelicula("Megalodon", "Acción", 105, ["17:00", "21:00"]))

    clientes: Dict[str, Cliente] = {}

    while True:
        print("\n=== MENÚ ===")
        print("1. Ver cartelera")
        print("2. Comprar boleto")
        print("3. Cancelar boleto")
        print("4. Estadísticas")
        print("0. Salir")
        op = input("Opción: ").strip()

        if op == "0":
            print("Saliendo...")
            break
        elif op == "1":
            cine.mostrar_cartelera()
        elif op == "2":
            nombre = input("Nombre: ").strip()
            correo = input("Correo: ").strip()
            cliente = clientes.get(correo) or Cliente(nombre, correo)
            clientes[correo] = cliente
            cine.mostrar_cartelera()
            titulo = input("Título: ").strip()
            horario = input("Horario (ej. 18:00): ").strip()
            try:
                sala_num = int(input("Número de sala: ").strip())
            except ValueError:
                print("Sala inválida.")
                continue
            sala = cine._buscar_sala(sala_num)
            if not sala:
                print("Sala no existe.")
                continue
            print("Plano de asientos (O libre, X ocupado):")
            sala.mostrar_asientos()
            asientos = pedir_asientos_cantidad()
            ok, resp = cine.vender_boleto(cliente, titulo, horario, sala_num, asientos)
            print(resp if ok else f"Error: {resp}")
        elif op == "3":
            codigo = input("Código boleto: ").strip()
            correo = input("Ingrese su correo (opcional): ").strip()
            cliente = clientes.get(correo) if correo else None
            ok, msg = cine.cancelar_boleto(codigo, cliente)
            print(msg)
        elif op == "4":
            cine.estadisticas()
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
