"""Motor del modo resistencia: probabilidades, estado, powerups, iconos, mecánicas y turnos."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field, replace

from Comun.config_historia import GRUPOS_TEMATICOS, etiqueta_grupo_tematico
from Comun.emojis_escape import (
    EMOJI_NIEBLA_AMBOS,
    EMOJI_NIEBLA_ENUNCIADO,
    EMOJI_NIEBLA_OPCIONES,
)
from Comun.modelos import Pregunta
from Comun.motor_nucleo import EstadoPartida, FeedbackRespuesta, ResultadoRespuesta, evaluar_respuesta
from Comun.pool_libre import EstadoSeleccionPool


# --- Probabilidades ---

# Progreso lineal desde la pregunta 5 hasta ~180 (t=1).
PREGUNTAS_HASTA_EXTREMO_PROB = 175
PREGUNTA_MIN_EVENTOS_ALEATORIOS = 5

PROB_BUENA_INICIAL = 0.90
PROB_BUENA_FINAL = 0.03
PROB_MALA_INICIAL = 0.03
PROB_MALA_FINAL = 0.90

# Escala la prob. de evento favorable de escalada (doble/triple); la curva buena va ~90 %→3 %.
FACTOR_EVENTO_BUENO_ESCALADA = 0.18


@dataclass(frozen=True)
class CuotasBancoResistencia:
    plantillas: int
    exclusivas: int


def progreso_probabilidad_resistencia(numero_pregunta: int) -> int:
    return max(0, numero_pregunta - PREGUNTA_MIN_EVENTOS_ALEATORIOS)


def factor_progreso_resistencia(
    numero_pregunta: int,
    *,
    preguntas_hasta_extremo: int = PREGUNTAS_HASTA_EXTREMO_PROB,
) -> float:
    """0 al empezar eventos, 1 en la fase tardía (curva lineal)."""
    if numero_pregunta < PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        return 0.0
    progreso = progreso_probabilidad_resistencia(numero_pregunta)
    if preguntas_hasta_extremo <= 0:
        return 1.0
    return min(1.0, progreso / preguntas_hasta_extremo)


def probabilidad_buena_resistencia(numero_pregunta: int) -> float:
    """Alta al inicio, casi nula al final (~45 % en el punto medio)."""
    t = factor_progreso_resistencia(numero_pregunta)
    return PROB_BUENA_INICIAL + (PROB_BUENA_FINAL - PROB_BUENA_INICIAL) * t


def probabilidad_evento_bueno_escalada(numero_pregunta: int) -> float:
    """Prob. de doble/triple en escalada (mucho menor que prob. buena bruta)."""
    return probabilidad_buena_resistencia(numero_pregunta) * FACTOR_EVENTO_BUENO_ESCALADA


def probabilidad_mala_resistencia(numero_pregunta: int) -> float:
    """Casi nula al inicio, alta al final (~45 % en el punto medio)."""
    t = factor_progreso_resistencia(numero_pregunta)
    return PROB_MALA_INICIAL + (PROB_MALA_FINAL - PROB_MALA_INICIAL) * t


def factor_bueno_resistencia(numero_pregunta: int) -> float:
    """Peso relativo de recompensas/eventos favorables (1 → 0)."""
    return 1.0 - factor_progreso_resistencia(numero_pregunta)


def factor_malo_resistencia(numero_pregunta: int) -> float:
    """Peso relativo de penalizaciones/eventos hostiles (0 → 1)."""
    return factor_progreso_resistencia(numero_pregunta)


def factor_progreso_banco_resistencia(
    numero_pregunta: int,
    *,
    preguntas_hasta_completo: int = PREGUNTAS_HASTA_EXTREMO_PROB,
) -> float:
    """0 en la primera pregunta; 1 cuando el banco dinámico está completo."""
    if numero_pregunta <= 1:
        return 0.0
    if preguntas_hasta_completo <= 0:
        return 1.0
    return min(1.0, (numero_pregunta - 1) / preguntas_hasta_completo)


def cuotas_banco_resistencia(
    numero_pregunta: int,
    total_plantillas: int,
    total_exclusivas: int,
) -> CuotasBancoResistencia:
    """Cuántas plantillas y exclusivas están desbloqueadas en este turno."""
    t = factor_progreso_banco_resistencia(numero_pregunta)
    if t >= 1.0:
        return CuotasBancoResistencia(
            plantillas=total_plantillas,
            exclusivas=total_exclusivas,
        )
    return CuotasBancoResistencia(
        plantillas=min(total_plantillas, int(t * total_plantillas)),
        exclusivas=min(total_exclusivas, int(t * total_exclusivas)),
    )

# --- Mecánicas (tipos y constantes) ---

_MALDIGIONES: tuple[tuple[str, str, str], ...] = (
    ("niebla", "Maldición: niebla en el enunciado", EMOJI_NIEBLA_ENUNCIADO),
    ("sin_objetos", "Maldición: no puedes usar objetos", "⛔"),
    ("relampago", "Maldición: relámpago forzado", "⚡"),
)


# Presión por racha alta: la pregunta actual se vuelve más exigente (sin castigos automáticos).
PRESION_RACHA_UMBRAL = 25
_PRESION_RACHA_ESCALA = 30.0

# Desafío aparte: X aciertos en Y segundos (fin de partida si expira). Distinto del tiempo por pregunta.
PREGUNTA_MIN_DESAFIO_BLOQUE_RESISTENCIA = 120


@dataclass
class DesafioBloqueTiempoResistencia:
    """Bloque de aciertos con tiempo total; independiente del cronómetro por pregunta."""

    aciertos_objetivo: int
    tiempo_limite_seg: int
    aciertos_logrados: int = 0
    inicio_monotonic: float = field(default_factory=time.monotonic)

    def tiempo_restante_seg(self) -> int:
        rest = int(self.tiempo_limite_seg - (time.monotonic() - self.inicio_monotonic))
        return max(0, rest)

    def completado(self) -> bool:
        return self.aciertos_logrados >= self.aciertos_objetivo

    def expirado(self) -> bool:
        return not self.completado() and self.tiempo_restante_seg() <= 0


def probabilidad_desafio_bloque_resistencia(numero_pregunta: int) -> float:
    if numero_pregunta < PREGUNTA_MIN_DESAFIO_BLOQUE_RESISTENCIA:
        return 0.0
    t = factor_progreso_resistencia(numero_pregunta)
    if t < 0.5:
        return 0.0
    return 0.06 + 0.14 * min(1.0, (t - 0.5) * 2.0)


def params_desafio_bloque_resistencia(numero_pregunta: int) -> tuple[int, int]:
    """Devuelve (aciertos necesarios, segundos de bloque) según el progreso."""
    t = factor_progreso_resistencia(numero_pregunta)
    if t < 0.75:
        return (3, 90)
    if t < 0.9:
        return (4, 75)
    return (5, 60)


def formatear_aviso_desafio_bloque(desafio: DesafioBloqueTiempoResistencia) -> str:
    n = desafio.aciertos_objetivo
    seg = desafio.tiempo_limite_seg
    texto = (
        f"Desafío de bloque: consigue {n} acierto"
        f"{'s' if n != 1 else ''} en {seg} s o pierdes la partida."
    )
    return prefijar_emoji(texto, "⏲️")

@dataclass(frozen=True)
class BloqueFiltroActivo:
    """Filtro temporal sobre el pool ya disponible (materia, tipo, grupo, curso o semestre)."""

    etiqueta: str
    preguntas_restantes: int
    materia: str | None = None
    tipo: str | None = None
    grupo: str | None = None
    curso: str | None = None
    semestre: str | None = None


_ETIQUETA_TIPO: dict[str, str] = {
    "Teoria": "Teoría",
    "Calculo": "Cálculo",
    "General": "generales",
}


def _etiqueta_bloque(n: int, descripcion: str) -> str:
    return f"Bloque: {n} preguntas {descripcion}"


def _descripcion_grupo_tematico(grupo: str, pool: list[Pregunta]) -> str:
    clave = str(grupo).strip()
    if clave in GRUPOS_TEMATICOS:
        return f"de {GRUPOS_TEMATICOS[clave]}"
    materias = sorted({p.materia for p in pool if p.grupo == grupo and p.materia})
    if len(materias) == 1:
        return f"de {materias[0]}"
    if materias:
        resto = f" (+{len(materias) - 2})" if len(materias) > 2 else ""
        return f"de {' · '.join(materias[:2])}{resto}"
    return f"de {etiqueta_grupo_tematico(grupo)}"


def _descripcion_tipo(tipo: str) -> str:
    etiqueta = _ETIQUETA_TIPO.get(tipo, tipo)
    if tipo in _ETIQUETA_TIPO:
        return f"de {etiqueta}"
    return f"de tipo {etiqueta}"


def _descripcion_curso(curso: str) -> str:
    return f"del curso {curso}"


def _descripcion_semestre(curso: str, semestre: str) -> str:
    if curso:
        return f"del curso {curso} · semestre {semestre}"
    return f"del semestre {semestre}"


@dataclass(frozen=True)
class RecompensaApuesta:
    mult_puntos: int = 1
    delta_vidas: int = 0
    powerup_id: str | None = None
    cantidad_powerup: int = 1
    powerup_aleatorio: bool = False


@dataclass(frozen=True)
class CosteApuesta:
    """Penalización si fallas la pregunta con apuesta activa."""

    vidas_fallo: int = 1  # Total de vidas perdidas (1 = solo el fallo habitual)
    puntos_perdidos: int = 0
    pierde_powerup_aleatorio: bool = False
    pierde_todos_objetos: bool = False
    fin_partida: bool = False


@dataclass(frozen=True)
class ApuestaRiesgo:
    etiqueta: str
    recompensa: RecompensaApuesta
    coste: CosteApuesta


APUESTAS_DISPONIBLES: tuple[ApuestaRiesgo, ...] = (
    ApuestaRiesgo(
        "Doble o nada",
        RecompensaApuesta(mult_puntos=2),
        CosteApuesta(vidas_fallo=2),
    ),
    ApuestaRiesgo(
        "Triple arriesgado",
        RecompensaApuesta(mult_puntos=3),
        CosteApuesta(vidas_fallo=2),
    ),
    ApuestaRiesgo(
        "Cuádruple audaz",
        RecompensaApuesta(mult_puntos=4),
        CosteApuesta(vidas_fallo=3),
    ),
    ApuestaRiesgo(
        "Todo o nada",
        RecompensaApuesta(mult_puntos=5),
        CosteApuesta(vidas_fallo=3),
    ),
    ApuestaRiesgo(
        "Botín seguro",
        RecompensaApuesta(powerup_aleatorio=True),
        CosteApuesta(vidas_fallo=1),
    ),
    ApuestaRiesgo(
        "Vida de la suerte",
        RecompensaApuesta(delta_vidas=1),
        CosteApuesta(puntos_perdidos=35),
    ),
    ApuestaRiesgo(
        "Cofre arriesgado",
        RecompensaApuesta(mult_puntos=2, powerup_aleatorio=True),
        CosteApuesta(pierde_powerup_aleatorio=True),
    ),
    ApuestaRiesgo(
        "Escudo de oro",
        RecompensaApuesta(powerup_id="escudo"),
        CosteApuesta(vidas_fallo=2, puntos_perdidos=20),
    ),
    ApuestaRiesgo(
        "Impulso doble",
        RecompensaApuesta(mult_puntos=2, delta_vidas=1),
        CosteApuesta(pierde_powerup_aleatorio=True, vidas_fallo=1),
    ),
    ApuestaRiesgo(
        "Ruleta roja",
        RecompensaApuesta(mult_puntos=3),
        CosteApuesta(pierde_todos_objetos=True, vidas_fallo=1),
    ),
    ApuestaRiesgo(
        "Última carta",
        RecompensaApuesta(mult_puntos=4),
        CosteApuesta(fin_partida=True),
    ),
    ApuestaRiesgo(
        "Riesgo mortal",
        RecompensaApuesta(mult_puntos=3, powerup_aleatorio=True),
        CosteApuesta(fin_partida=True),
    ),
)


@dataclass
class MaldicionActiva:
    id: str
    etiqueta: str
    preguntas_restantes: int = 1


# --- Estado ---

VIDAS_MAX_INICIAL = 5
VIDAS_MAX_ABSOLUTO = 9
VIDAS_MIN_CAP = 2


def _pity_eventos_resistencia_nuevo():
    from Comun.resistencia_partida import PityEventosResistencia

    return PityEventosResistencia()


@dataclass
class EstadoResistencia:
    """Racha de aciertos seguidos (se corta al fallar); vidas e inventario aparte."""

    racha: int = 0
    mejor_racha: int = 0  # récord de la partida; solo ranking/resumen, no afecta al juego
    vidas_max: int = VIDAS_MAX_INICIAL
    inventario: dict[str, int] = field(default_factory=dict)
    letras_ocultas: frozenset[str] = field(default_factory=frozenset)
    fraccion_enunciado: float = 1.0
    tiempo_extra_seg: int = 0
    relampago_forzado_seg: int | None = None
    escudo_activo: bool = False
    ultimo_evento: str = ""
    semilla_partida: int | None = None
    bloque_filtro: BloqueFiltroActivo | None = None
    apuesta_oferta: ApuestaRiesgo | None = None
    apuesta_activa: ApuestaRiesgo | None = None
    maldicion: MaldicionActiva | None = None
    ventana_resultados: list[bool] = field(default_factory=list)
    tiradas_recompensa: int = 0
    objetos_bloqueados: bool = False
    powerups_usados_en_pregunta: set[str] = field(default_factory=set)
    banco_resistencia: object | None = None
    presion_racha_intensidad: float = 0.0
    desafio_bloque: DesafioBloqueTiempoResistencia | None = None
    pity_eventos: object = field(default_factory=lambda: _pity_eventos_resistencia_nuevo())

    def reset_pregunta(self) -> None:
        self.letras_ocultas = frozenset()
        self.fraccion_enunciado = 1.0
        self.tiempo_extra_seg = 0
        self.relampago_forzado_seg = None
        self.ultimo_evento = ""
        self.presion_racha_intensidad = 0.0
        self.objetos_bloqueados = False
        self.powerups_usados_en_pregunta.clear()

    def reiniciar_slot_pregunta(self) -> None:
        """Nueva pregunta en el mismo turno (cambio): limpia ayudas de la anterior."""
        self.letras_ocultas = frozenset()
        self.tiempo_extra_seg = 0
        self.powerups_usados_en_pregunta.clear()

    def registrar_acierto(self) -> None:
        self.racha += 1
        self.mejor_racha = max(self.mejor_racha, self.racha)

    def registrar_fallo(self) -> None:
        self.racha = 0

    def cantidad(self, powerup_id: str) -> int:
        return max(0, self.inventario.get(powerup_id, 0))

    def agregar_powerup(self, powerup_id: str, cantidad: int = 1) -> None:
        if cantidad <= 0:
            return
        self.inventario[powerup_id] = self.cantidad(powerup_id) + cantidad

    def consumir_powerup(self, powerup_id: str) -> bool:
        n = self.cantidad(powerup_id)
        if n <= 0:
            return False
        if n == 1:
            self.inventario.pop(powerup_id, None)
        else:
            self.inventario[powerup_id] = n - 1
        return True

    def inventario_resumen(self) -> str:

        partes = [
            prefijar_emoji(f"{etiqueta_powerup(pid)}×{n}", emoji_powerup(pid))
            for pid, n in sorted(self.inventario.items())
            if n > 0
        ]
        return ", ".join(partes) if partes else "vacío"


def texto_segmento_desafio_bloque(er: EstadoResistencia) -> str | None:
    db = er.desafio_bloque
    if db is None:
        return None
    return f"{db.aciertos_logrados}/{db.aciertos_objetivo}·{db.tiempo_restante_seg()}s"


def desafio_bloque_expirado(er: EstadoResistencia) -> bool:
    db = er.desafio_bloque
    return db is not None and db.expirado()


def _intentar_activar_desafio_bloque(
    er: EstadoResistencia,
    numero_pregunta: int,
) -> str | None:
    if er.desafio_bloque is not None:
        return None
    prob = probabilidad_desafio_bloque_resistencia(numero_pregunta)
    if prob <= 0.0:
        return None
    rng = rng_partida(er, numero_pregunta * 43 + 5107)
    if rng.random() > prob:
        return None
    aciertos, segundos = params_desafio_bloque_resistencia(numero_pregunta)
    er.desafio_bloque = DesafioBloqueTiempoResistencia(
        aciertos_objetivo=aciertos,
        tiempo_limite_seg=segundos,
    )
    return formatear_aviso_desafio_bloque(er.desafio_bloque)


def _tick_desafio_bloque_tras_acierto(er: EstadoResistencia, *, acierto: bool) -> list[str]:
    db = er.desafio_bloque
    if db is None or not acierto:
        return []
    db.aciertos_logrados += 1
    if not db.completado():
        return []
    er.desafio_bloque = None
    return [prefijar_emoji("Desafío de bloque superado.", "✅")]


def finalizar_partida_por_desafio_bloque(estado: EstadoPartida, er: EstadoResistencia) -> str:
    er.desafio_bloque = None
    if estado.vidas_restantes is not None:
        estado.vidas_restantes = 0
    return prefijar_emoji("Desafío de bloque: tiempo agotado.", "⏲️")


# --- Powerups ---

LETRAS_OPCION = ("A", "B", "C", "D")

# Escala la prob. de premio por tirada (la curva buena va de ~90 % a ~3 %).
FACTOR_TIRADA_RECOMPENSA = 0.20
# Cupo de tiradas de recompensa tras cada acierto (independiente de eventos/popups).
MAX_TIRADAS_RECOMPENSA_ACIERTO = 2

POWERUPS: dict[str, tuple[str, str]] = {
    "fifty_fifty": ("50/50", "Quita 2 respuestas incorrectas"),
    "bomba": ("Bomba", "Destruyes una respuesta incorrecta"),
    "skip": ("Saltar", "Siguiente pregunta sin perder vida (corta la racha)"),
    "tiempo_extra": ("+Tiempo", "Añade 20 s a esta pregunta"),
    "escudo": ("Escudo", "El próximo fallo no cuesta vida ni corta la racha"),
    "cambio": ("Cambio", "Sustituye por una pregunta parecida (misma materia y tipo)"),
}

POWERUPS_LOOT = tuple(POWERUPS.keys())


@dataclass(frozen=True)
class EventoRecompensaResistencia:
    etiqueta: str
    delta_vidas: int = 0
    delta_vidas_max: int = 0
    powerup_id: str | None = None
    cantidad_powerup: int = 1


def etiqueta_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, powerup_id))[0]


def descripcion_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, ""))[1]


MENSAJE_POWERUP_YA_USADO = "Solo puedes usar un objeto por pregunta."

POWERUPS_INCOMPATIBLES_EN_PREGUNTA: dict[str, frozenset[str]] = {
    "bomba": frozenset({"fifty_fifty"}),
    "fifty_fifty": frozenset({"bomba"}),
}


def puede_usar_powerup_en_pregunta(powerup_id: str, usados: set[str]) -> str | None:
    """Devuelve mensaje de error si el objeto no puede usarse en esta pregunta."""
    if powerup_id in usados:
        if powerup_id in POWERUPS:
            return f"Ya usaste {etiqueta_powerup(powerup_id)} en esta pregunta."
        return "Ya usaste este objeto en esta pregunta."
    incompatibles = POWERUPS_INCOMPATIBLES_EN_PREGUNTA.get(powerup_id, frozenset())
    for usado in usados:
        if usado in incompatibles:
            nom = etiqueta_powerup(powerup_id)
            otro = etiqueta_powerup(usado) if usado in POWERUPS else usado
            return f"No puedes combinar {nom} con {otro} en la misma pregunta."
    return None


def revocar_powerup_usado(usados: set[str], powerup_id: str) -> None:
    usados.discard(powerup_id)


def _incorrectas(p: Pregunta) -> list[str]:
    correcta = p.correcta if p.correcta in LETRAS_OPCION else ""
    return [letra for letra in LETRAS_OPCION if letra != correcta and p.opciones.get(letra)]


def letras_ocultas_fifty_fifty(p: Pregunta, rng: random.Random | None = None) -> frozenset[str]:
    rng = rng or random.Random()
    malas = _incorrectas(p)
    rng.shuffle(malas)
    return frozenset(malas[:2])


def letras_ocultas_bomba(p: Pregunta, rng: random.Random | None = None) -> frozenset[str]:
    rng = rng or random.Random()
    malas = _incorrectas(p)
    if not malas:
        return frozenset()
    return frozenset({rng.choice(malas)})


def letras_ocultas_por_cantidad(
    p: Pregunta,
    cantidad: int,
    *,
    semilla: int,
) -> frozenset[str]:
    if cantidad <= 0:
        return frozenset()
    rng = random.Random(semilla * 31 + len(p.texto))
    malas = _incorrectas(p)
    rng.shuffle(malas)
    return frozenset(malas[: min(cantidad, len(malas))])


def texto_pregunta_visible(texto: str, fraccion: float) -> str:
    """Recorta el enunciado y tapa el resto (evento niebla)."""
    if fraccion >= 1.0 or not texto.strip():
        return texto
    fraccion = max(0.2, min(1.0, fraccion))
    corte = max(8, int(len(texto) * fraccion))
    visible = texto[:corte].rstrip()
    if len(visible) >= len(texto):
        return texto
    resto = len(texto) - len(visible)
    return f"{visible} {'▓' * min(48, max(8, resto))}"


def _generar_recompensa_aleatoria(
    rng: random.Random,
    *,
    numero_pregunta: int,
) -> EventoRecompensaResistencia:

    factor_bueno = max(0.08, factor_bueno_resistencia(numero_pregunta))
    factor_malo = max(0.08, factor_malo_resistencia(numero_pregunta))
    tabla = [
        (0.22 * factor_bueno, EventoRecompensaResistencia("¡Vida extra!", delta_vidas=1), False),
        (0.12 * factor_bueno, EventoRecompensaResistencia("Corazón máximo +1", delta_vidas_max=1), False),
        (
            0.16 * factor_malo,
            EventoRecompensaResistencia("Corazón máximo −1", delta_vidas_max=-1),
            True,
        ),
    ]
    roll = rng.random()
    acum = 0.0
    for peso, evento, _es_malo in tabla:
        acum += peso
        if roll < acum:
            return evento
    pid = rng.choice(POWERUPS_LOOT)
    return EventoRecompensaResistencia(
        f"Objeto: {etiqueta_powerup(pid)}",
        powerup_id=pid,
    )


def tirar_recompensas_tras_acierto(
    er: EstadoResistencia,
    *,
    numero_pregunta: int,
) -> list[EventoRecompensaResistencia]:
    """Bonificaciones tras acertar; más probables al inicio, raras al final."""

    prob_tirada = probabilidad_buena_resistencia(numero_pregunta) * FACTOR_TIRADA_RECOMPENSA
    resultados: list[EventoRecompensaResistencia] = []
    for _ in range(MAX_TIRADAS_RECOMPENSA_ACIERTO):
        er.tiradas_recompensa += 1
        rng = rng_partida(er, er.tiradas_recompensa * 9973 + 42)
        if rng.random() > prob_tirada:
            continue
        resultados.append(_generar_recompensa_aleatoria(rng, numero_pregunta=numero_pregunta))
    return resultados

# --- Iconos ---

EMOJI_POWERUP: dict[str, str] = {
    "fifty_fifty": "✂️",
    "bomba": "💣",
    "skip": "⏭️",
    "tiempo_extra": "⏱️",
    "escudo": "🛡️",
    "cambio": "🔄",
}

_SEPARADOR_EMOJI = "  "


def emoji_powerup(powerup_id: str) -> str:
    return EMOJI_POWERUP.get(powerup_id, "🎁")


def etiqueta_powerup_con_emoji(powerup_id: str) -> str:
    return prefijar_emoji(etiqueta_powerup(powerup_id), emoji_powerup(powerup_id))


def prefijar_emoji(texto: str, emoji: str) -> str:
    if not emoji or not texto.strip():
        return texto
    if texto.startswith(emoji):
        return texto
    return f"{emoji}{_SEPARADOR_EMOJI}{texto}"


def separar_emoji_mensaje(mensaje: str) -> tuple[str, str]:
    """Devuelve (emoji, resto) si el mensaje lleva emoji al inicio."""
    if _SEPARADOR_EMOJI in mensaje:
        emoji, resto = mensaje.split(_SEPARADOR_EMOJI, 1)
        if resto and len(emoji) <= 4:
            return emoji.strip(), resto.strip()
    return "", mensaje


def emoji_evento_etiqueta(etiqueta: str) -> str:
    if etiqueta.startswith("Relámpago"):
        return "⚡"
    if etiqueta.startswith("Niebla:"):
        if "enunciado y opciones" in etiqueta:
            return EMOJI_NIEBLA_AMBOS
        if "enunciado" in etiqueta:
            return EMOJI_NIEBLA_ENUNCIADO
        return EMOJI_NIEBLA_OPCIONES
    if etiqueta == "Doble puntos":
        return "✨"
    if etiqueta == "Triple puntos":
        return "💎"
    if etiqueta == "Pregunta difícil":
        return "🔥"
    if etiqueta == "Pregunta extra difícil":
        return "☠️"
    if etiqueta.startswith("Bloque:"):
        return "📚"
    if "Maldición" in etiqueta:
        return "💀"
    if "Hito racha" in etiqueta:
        return "🏅"

    if any(ap.etiqueta == etiqueta for ap in APUESTAS_DISPONIBLES):
        return "🎰"
    return "🎲"


def descripcion_evento_etiqueta(etiqueta: str) -> str:
    if etiqueta.startswith("Relámpago"):
        seg = etiqueta.split(":")[-1].strip() if ":" in etiqueta else ""
        return f"Menos tiempo para responder{f' ({seg})' if seg else ''}."
    if etiqueta.startswith("Niebla:") and "enunciado" in etiqueta:
        return "Solo verás parte del enunciado de la pregunta."
    if etiqueta.startswith("Niebla:"):
        return "El juego ocultará una o más respuestas incorrectas."
    if etiqueta in {"Doble puntos", "Triple puntos"}:
        return f"Si aciertas, sumarás {etiqueta.lower()} en esta pregunta."
    if etiqueta == "Pregunta difícil":
        return "Esta pregunta será más difícil de lo habitual en esta fase."
    if etiqueta == "Pregunta extra difícil":
        return "Una pregunta muy exigente para esta fase de la partida."
    return etiqueta


def emoji_recompensa_etiqueta(etiqueta: str) -> str:
    if etiqueta.startswith("Objeto: "):
        nombre = etiqueta.removeprefix("Objeto: ").strip()
        for pid, (nom, _) in POWERUPS.items():
            if nom == nombre:
                return emoji_powerup(pid)
        return "🎁"
    if "Vida extra" in etiqueta:
        return "❤️"
    if "pierdes 1 vida" in etiqueta.lower():
        return "💔"
    if "máximo +1" in etiqueta or "maximo +1" in etiqueta.lower():
        return "💖"
    if "máximo −1" in etiqueta or ("maximo" in etiqueta.lower() and "−1" in etiqueta):
        return "🩶"
    return "🎁"


def emoji_aviso_exclusiva() -> str:
    return "⭐"

# --- Mecánicas (funciones) ---


def presion_racha_umbral() -> int:
    return PRESION_RACHA_UMBRAL


def intensidad_presion_racha(racha: int) -> float:
    """Escala con la racha; puede superar 1.0 y romper topes de eventos negativos."""
    if racha < PRESION_RACHA_UMBRAL:
        return 0.0
    exceso = racha - PRESION_RACHA_UMBRAL
    return exceso / _PRESION_RACHA_ESCALA


def exceso_presion_racha(racha: int) -> float:
    """Porción por encima del nivel «completo» (1.0) de presión."""
    return max(0.0, intensidad_presion_racha(racha) - 1.0)


def formatear_aviso_presion_racha(intensidad: float) -> str:
    if intensidad > 1.0:
        texto = (
            "Presión extrema de la racha: se acumulan eventos hostiles "
            "más allá del límite habitual."
        )
    elif intensidad < 0.35:
        texto = "La racha aprieta: el enunciado será más difícil de leer."
    elif intensidad < 0.65:
        texto = "Presión de la racha: menos margen y más niebla en esta pregunta."
    else:
        texto = "Presión de la racha: esta pregunta es especialmente exigente."
    return prefijar_emoji(texto, "⚖️")


def preparar_presion_racha_turno(
    er: EstadoResistencia,
    numero_pregunta: int,
) -> str | None:
    """Marca la intensidad de presión del turno (sin quitar vidas ni cortar racha)."""
    del numero_pregunta  # reservado para avisos deterministas futuros
    t = intensidad_presion_racha(er.racha)
    er.presion_racha_intensidad = t
    if t <= 0.0:
        return None
    return formatear_aviso_presion_racha(t)


def aplicar_presion_racha_modificadores(
    er: EstadoResistencia,
    p: Pregunta,
    numero_pregunta: int,
) -> None:
    """Modificadores extra según la racha; con racha extrema apila efectos hostiles."""
    t = er.presion_racha_intensidad
    if t <= 0.0:
        return

    base = min(1.0, t)
    from Comun.eventos_partida import niebla_disponible_resistencia

    niebla_ok = niebla_disponible_resistencia(numero_pregunta)
    if niebla_ok:
        er.fraccion_enunciado = min(er.fraccion_enunciado, max(0.35, 1.0 - 0.35 * base))
    if base >= 0.25:
        seg = max(5, int(14 - 8 * base))
        if er.relampago_forzado_seg is None or er.relampago_forzado_seg > seg:
            er.relampago_forzado_seg = seg
    if niebla_ok and base >= 0.4:
        n_ocultas = 1 if base < 0.7 else 2
        er.letras_ocultas = er.letras_ocultas | letras_ocultas_por_cantidad(
            p,
            n_ocultas,
            semilla=numero_pregunta + 9001,
        )
    if base >= 0.75:
        rng = rng_partida(er, numero_pregunta * 101 + int(base * 1000))
        if rng.random() < 0.35 + 0.4 * base:
            er.objetos_bloqueados = True

    if t <= 1.0:
        return

    exceso = t - 1.0
    if niebla_ok:
        er.fraccion_enunciado = min(er.fraccion_enunciado, max(0.15, 0.30 - 0.08 * min(exceso, 2.0)))
    seg_ext = max(3, int(6 - 2 * min(exceso, 1.5)))
    if er.relampago_forzado_seg is None or er.relampago_forzado_seg > seg_ext:
        er.relampago_forzado_seg = seg_ext
    if niebla_ok:
        n_extra = min(2, 1 + int(exceso))
        er.letras_ocultas = er.letras_ocultas | letras_ocultas_por_cantidad(
            p,
            n_extra,
            semilla=numero_pregunta + 17003 + er.racha,
        )
    er.objetos_bloqueados = True
    if niebla_ok and exceso >= 0.5:
        er.fraccion_enunciado = min(er.fraccion_enunciado, 0.22)

def rng_partida(er: EstadoResistencia, clave: int) -> random.Random:
    base = er.semilla_partida if er.semilla_partida is not None else 0
    return random.Random(base * 1_000_003 + clave * 104_729)


def configurar_partida_resistencia(er: EstadoResistencia, *, preset_id: str) -> None:
    del er, preset_id


def texto_progreso_resistencia(er: EstadoResistencia, numero_pregunta: int) -> str:
    return f"#{numero_pregunta} · Racha {er.racha}"


def _pregunta_cumple_bloque(p: Pregunta, bloque: BloqueFiltroActivo) -> bool:
    if bloque.materia and p.materia != bloque.materia:
        return False
    if bloque.tipo and p.tipo != bloque.tipo:
        return False
    if bloque.grupo and p.grupo != bloque.grupo:
        return False
    if bloque.curso and p.curso != bloque.curso:
        return False
    if bloque.semestre and p.semestre != bloque.semestre:
        return False
    return True


def consumir_bloque_filtro(er: EstadoResistencia) -> None:
    """Avanza el filtro de bloque; al expirar vuelve al pool por defecto del momento."""
    if not er.bloque_filtro or er.bloque_filtro.preguntas_restantes <= 0:
        return
    rest = er.bloque_filtro.preguntas_restantes - 1
    if rest <= 0:
        er.bloque_filtro = None
        return
    bf = er.bloque_filtro
    er.bloque_filtro = BloqueFiltroActivo(
        etiqueta=bf.etiqueta,
        preguntas_restantes=rest,
        materia=bf.materia,
        tipo=bf.tipo,
        grupo=bf.grupo,
        curso=bf.curso,
        semestre=bf.semestre,
    )


def _materias_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.materia for p in pool if p.materia})


def _grupos_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.grupo for p in pool if p.grupo})


def _cursos_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.curso for p in pool if p.curso})


def _pares_curso_semestre_en_pool(pool: list[Pregunta]) -> list[tuple[str, str]]:
    return sorted({(p.curso, p.semestre) for p in pool if p.curso and p.semestre})


def _generar_bloque_filtro(
    pool: list[Pregunta],
    numero_pregunta: int,
    er: EstadoResistencia,
) -> BloqueFiltroActivo | None:
    if er.bloque_filtro and er.bloque_filtro.preguntas_restantes > 0:
        return None
    if numero_pregunta < PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        return None
    rng = rng_partida(er, numero_pregunta * 37 + 901)

    prob = probabilidad_buena_resistencia(numero_pregunta) * 0.42
    if rng.random() > prob:
        return None

    n = rng.randint(3, 5)
    opciones: list[BloqueFiltroActivo] = []
    materias = _materias_en_pool(pool)
    grupos = _grupos_en_pool(pool)
    if materias:
        mat = rng.choice(materias)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, f"de {mat}"),
                preguntas_restantes=n,
                materia=mat,
            )
        )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, _descripcion_tipo("Calculo")),
            preguntas_restantes=n,
            tipo="Calculo",
        )
    )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, _descripcion_tipo("Teoria")),
            preguntas_restantes=n,
            tipo="Teoria",
        )
    )
    if grupos:
        g = rng.choice(grupos)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, _descripcion_grupo_tematico(g, pool)),
                preguntas_restantes=n,
                grupo=g,
            )
        )
    cursos = _cursos_en_pool(pool)
    if cursos:
        curso = rng.choice(cursos)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, _descripcion_curso(curso)),
                preguntas_restantes=n,
                curso=curso,
            )
        )
    pares_cs = _pares_curso_semestre_en_pool(pool)
    if pares_cs:
        curso, semestre = rng.choice(pares_cs)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, _descripcion_semestre(curso, semestre)),
                preguntas_restantes=n,
                curso=curso,
                semestre=semestre,
            )
        )
    return rng.choice(opciones)


def _riesgo_apuesta(apuesta: ApuestaRiesgo) -> float:
    r = apuesta.recompensa
    c = apuesta.coste
    score = (c.vidas_fallo - 1) * 1.25
    score += c.puntos_perdidos / 30.0
    if c.pierde_powerup_aleatorio:
        score += 1.0
    if c.pierde_todos_objetos:
        score += 2.0
    if c.fin_partida:
        score += 5.0
    score -= (r.mult_puntos - 1) * 0.35
    score -= r.delta_vidas * 0.9
    if r.powerup_id or r.powerup_aleatorio:
        score -= 0.7
    return max(0.4, score)


def _elegir_apuesta(rng: random.Random, numero_pregunta: int) -> ApuestaRiesgo:
    """Elige una apuesta; al avanzar la partida pesan más las de mayor riesgo."""
    t = factor_progreso_resistencia(numero_pregunta)
    centro = 1.0 + t * 4.5
    pesos = [1.0 / (0.6 + abs(_riesgo_apuesta(ap) - centro)) for ap in APUESTAS_DISPONIBLES]
    return rng.choices(APUESTAS_DISPONIBLES, weights=pesos, k=1)[0]


def oferta_apuesta_para_pregunta(
    numero_pregunta: int,
    er: EstadoResistencia,
) -> ApuestaRiesgo | None:
    if numero_pregunta < 8:
        return None
    if er.maldicion is not None:
        return None
    if er.apuesta_activa is not None:
        return None
    rng = rng_partida(er, numero_pregunta * 53 + 4049)

    prob = probabilidad_buena_resistencia(numero_pregunta) * 0.34
    if rng.random() > prob:
        return None
    return _elegir_apuesta(rng, numero_pregunta)


def _texto_recompensa_apuesta(recompensa: RecompensaApuesta) -> str:

    partes: list[str] = []
    if recompensa.mult_puntos > 1:
        partes.append(f"×{recompensa.mult_puntos} puntos")
    if recompensa.delta_vidas > 0:
        n = recompensa.delta_vidas
        partes.append(f"+{n} vida" + ("s" if n > 1 else ""))
    if recompensa.powerup_id:
        nom = etiqueta_powerup(recompensa.powerup_id)
        if recompensa.cantidad_powerup > 1:
            partes.append(f"{recompensa.cantidad_powerup}× {nom}")
        else:
            partes.append(f"objeto {nom}")
    elif recompensa.powerup_aleatorio:
        partes.append("un objeto al azar")
    return ", ".join(partes) if partes else "sin bonus extra"


def _texto_coste_apuesta(coste: CosteApuesta) -> str:
    if coste.fin_partida:
        return "la partida termina al instante"
    partes: list[str] = []
    if coste.vidas_fallo <= 1:
        partes.append("pierdes 1 vida como de costumbre")
    else:
        partes.append(f"pierdes {coste.vidas_fallo} vidas")
    if coste.puntos_perdidos > 0:
        partes.append(f"−{coste.puntos_perdidos} puntos")
    if coste.pierde_todos_objetos:
        partes.append("pierdes todos los objetos")
    elif coste.pierde_powerup_aleatorio:
        partes.append("pierdes un objeto al azar")
    return "; ".join(partes)


def formatear_aviso_apuesta(apuesta: ApuestaRiesgo) -> str:
    recomp = _texto_recompensa_apuesta(apuesta.recompensa)
    coste = _texto_coste_apuesta(apuesta.coste)
    texto = f"{apuesta.etiqueta}: si aciertas, {recomp}; si fallas, {coste}."
    return prefijar_emoji(texto, "🎰")


def preparar_eventos_nuevo_turno(
    er: EstadoResistencia,
    pool: list[Pregunta],
    numero_pregunta: int,
) -> list[str]:
    """Eventos al cargar una pregunta nueva (presión de racha, bloque, apuesta)."""
    avisos: list[str] = []
    aviso_presion = preparar_presion_racha_turno(er, numero_pregunta)
    if aviso_presion:
        avisos.append(aviso_presion)
    bloque = _generar_bloque_filtro(pool, numero_pregunta, er)
    if bloque:
        er.bloque_filtro = bloque
        avisos.append(formatear_aviso_bloque(bloque.etiqueta))
    if not er.apuesta_oferta:
        er.apuesta_oferta = oferta_apuesta_para_pregunta(numero_pregunta, er)
    aviso_bloque = _intentar_activar_desafio_bloque(er, numero_pregunta)
    if aviso_bloque:
        avisos.append(aviso_bloque)
    return avisos


def formatear_aviso_bloque(etiqueta: str) -> str:
    return prefijar_emoji(etiqueta, "📚")


def formatear_aviso_maldicion(etiqueta: str) -> str:
    return prefijar_emoji(etiqueta, "💀")


def _activar_maldicion(er: EstadoResistencia, numero_pregunta: int) -> MaldicionActiva | None:
    if er.maldicion is not None:
        return None
    fallos = sum(1 for ok in er.ventana_resultados if not ok)
    if len(er.ventana_resultados) < 3 or fallos < 2:
        return None
    rng = rng_partida(er, numero_pregunta * 71 + 3001)

    if rng.random() > probabilidad_mala_resistencia(numero_pregunta):
        return None
    from Comun.eventos_partida import niebla_disponible_resistencia

    maldiciones = list(_MALDIGIONES)
    if not niebla_disponible_resistencia(numero_pregunta):
        maldiciones = [m for m in maldiciones if m[0] != "niebla"]
    if not maldiciones:
        return None
    cid, etiqueta, _ = rng.choice(maldiciones)
    duracion = 2 if rng.random() < 0.35 else 1
    return MaldicionActiva(id=cid, etiqueta=etiqueta, preguntas_restantes=duracion)


def aplicar_efectos_maldicion(er: EstadoResistencia) -> None:
    if not er.maldicion:
        return
    cid = er.maldicion.id
    if cid == "niebla":
        er.fraccion_enunciado = min(er.fraccion_enunciado, 0.45)
    elif cid == "sin_objetos":
        er.objetos_bloqueados = True
    elif cid == "relampago":
        er.relampago_forzado_seg = 8


def procesar_post_turno_resistencia(
    er: EstadoResistencia,
    *,
    acierto: bool,
    numero_pregunta: int,
) -> list[str]:
    """Tras evaluar respuesta: ventana de fallos, maldiciones y tick de maldición activa."""
    avisos: list[str] = []
    er.ventana_resultados.append(acierto)
    if len(er.ventana_resultados) > 3:
        er.ventana_resultados.pop(0)

    if er.maldicion:
        er.maldicion.preguntas_restantes -= 1
        if er.maldicion.preguntas_restantes <= 0:
            er.maldicion = None
            er.objetos_bloqueados = False

    if not acierto:
        nueva = _activar_maldicion(er, numero_pregunta)
        if nueva:
            er.maldicion = nueva
            avisos.append(formatear_aviso_maldicion(nueva.etiqueta))

    avisos.extend(_tick_desafio_bloque_tras_acierto(er, acierto=acierto))

    er.apuesta_activa = None
    er.apuesta_oferta = None
    return avisos


def pregunta_compatible_bloque(p: Pregunta, er: EstadoResistencia) -> bool:
    """Sin bloque activo: todas las preguntas del pool del momento son válidas."""
    if not er.bloque_filtro or er.bloque_filtro.preguntas_restantes <= 0:
        return True
    return _pregunta_cumple_bloque(p, er.bloque_filtro)



def formatear_aviso_recompensa(etiqueta: str) -> str:
    if etiqueta.startswith("Objeto: "):
        texto = f"¡Obtuviste {etiqueta.removeprefix('Objeto: ')}!"
    else:
        texto = etiqueta
    return prefijar_emoji(texto, emoji_recompensa_etiqueta(etiqueta))


def formatear_aviso_evento(etiqueta: str) -> str:
    if etiqueta.startswith("Relámpago"):
        seg = etiqueta.split(":")[-1].strip() if ":" in etiqueta else ""
        texto = f"¡Pregunta relámpago!{f' {seg}' if seg else ''}"
    elif etiqueta in {"Doble puntos", "Triple puntos"}:
        texto = f"¡{etiqueta} en esta pregunta!"
    elif etiqueta.startswith("Niebla:"):
        if "enunciado" in etiqueta:
            texto = "¡Parte del enunciado estará oculta!"
        else:
            texto = f"¡{etiqueta}!"
    elif etiqueta in {"Pregunta difícil", "Pregunta extra difícil"}:
        texto = f"¡{etiqueta}!"
    else:
        texto = f"Ahora: {etiqueta}"
    return prefijar_emoji(texto, emoji_evento_etiqueta(etiqueta))



# --- Motor turnos ---
def aviso_apuesta_activa(er: EstadoResistencia) -> str | None:
    if not er.apuesta_activa:
        return None
    return formatear_aviso_apuesta(er.apuesta_activa)


@dataclass(frozen=True)
class ResultadoTurnoResistencia:
    feedback: FeedbackRespuesta
    reintentar_pregunta: bool = False
    avisos_extra: tuple[str, ...] = ()
    mult_apuesta: int = 1


def crear_estado_resistencia(vidas_iniciales: int) -> EstadoResistencia:
    er = EstadoResistencia()
    er.vidas_max = max(vidas_iniciales, er.vidas_max)
    return er


def aplicar_modificadores_visuales_escalada(
    er: EstadoResistencia,
    escalada: EscaladaResistencia,
    p: Pregunta,
    numero_pregunta: int,
) -> None:
    """Oculta respuestas o parte del enunciado según eventos de la escalada."""
    er.fraccion_enunciado = escalada.fraccion_enunciado
    if escalada.opciones_ocultas > 0:
        ocultas = letras_ocultas_por_cantidad(
            p,
            escalada.opciones_ocultas,
            semilla=numero_pregunta,
        )
        er.letras_ocultas = er.letras_ocultas | ocultas
    aplicar_presion_racha_modificadores(er, p, numero_pregunta)
    aplicar_efectos_maldicion(er)


def texto_pregunta_para_turno(p: Pregunta, er: EstadoResistencia) -> str:
    return texto_pregunta_visible(p.texto, er.fraccion_enunciado)


def tiempo_pregunta_efectivo(reglas_seg: int | None, er: EstadoResistencia) -> int | None:
    if er.relampago_forzado_seg is not None:
        base = er.relampago_forzado_seg
    elif reglas_seg is None:
        return None
    else:
        base = reglas_seg
    return max(3, base + er.tiempo_extra_seg)


def aplicar_recompensa(
    estado: EstadoPartida,
    er: EstadoResistencia,
    evento: EventoRecompensaResistencia,
) -> None:
    if evento.delta_vidas_max:
        er.vidas_max = max(
            VIDAS_MIN_CAP,
            min(VIDAS_MAX_ABSOLUTO, er.vidas_max + evento.delta_vidas_max),
        )
        if estado.vidas_restantes is not None and estado.vidas_restantes > er.vidas_max:
            estado.vidas_restantes = er.vidas_max
    if evento.delta_vidas and estado.vidas_restantes is not None:
        estado.vidas_restantes = max(0, min(er.vidas_max, estado.vidas_restantes + evento.delta_vidas))
    if evento.powerup_id:
        er.agregar_powerup(evento.powerup_id, evento.cantidad_powerup)
    er.ultimo_evento = evento.etiqueta


def usar_powerup(
    powerup_id: str,
    er: EstadoResistencia,
    p: Pregunta,
) -> str | None:
    """Consume un comodín; devuelve mensaje de error o None si OK."""
    if er.objetos_bloqueados:
        return "Maldición activa: no puedes usar objetos."
    err_uso = puede_usar_powerup_en_pregunta(powerup_id, er.powerups_usados_en_pregunta)
    if err_uso:
        return err_uso
    if not er.consumir_powerup(powerup_id):
        return "No tienes ese objeto."
    if powerup_id == "fifty_fifty":
        er.letras_ocultas = letras_ocultas_fifty_fifty(p)
    elif powerup_id == "bomba":
        ocultas = letras_ocultas_bomba(p)
        er.letras_ocultas = er.letras_ocultas | ocultas
    elif powerup_id == "tiempo_extra":
        er.tiempo_extra_seg += 20
    elif powerup_id == "escudo":
        er.escudo_activo = True
    elif powerup_id == "skip":
        pass
    elif powerup_id == "cambio":
        pass
    else:
        return f"Objeto desconocido: {powerup_id}"
    er.powerups_usados_en_pregunta.add(powerup_id)
    return None


def bonificacion_puntos_racha(racha: int) -> float:
    """Multiplicador de puntos por aciertos seguidos (la racha solo afecta a la puntuación)."""
    if racha < 2:
        return 1.0
    return 1.0 + min(1.0, (racha - 1) * 0.05)


def aplicar_bonificaciones_puntos_resistencia(
    estado: EstadoPartida,
    *,
    puntos_prev: int,
    racha: int,
    mult_escalada: int,
    exclusiva: bool,
    acierto: bool,
    tiempo_agotado: bool,
    mult_apuesta: int = 1,
) -> None:
    """Aplica multiplicadores de escalada, racha, apuesta y pregunta exclusiva."""
    if not acierto or tiempo_agotado:
        return
    delta = estado.puntos_arcade - puntos_prev
    if delta <= 0:
        return
    extra = 0.0
    if mult_escalada > 1:
        extra += delta * (mult_escalada - 1)
    bonif_racha = bonificacion_puntos_racha(racha)
    if bonif_racha > 1.0:
        extra += delta * (bonif_racha - 1.0)
    if exclusiva:
        extra += delta * 0.5
    if mult_apuesta > 1:
        extra += delta * (mult_apuesta - 1)
    if extra > 0:
        estado.puntos_arcade += int(extra)


def _aplicar_recompensa_apuesta_exito(
    estado: EstadoPartida,
    er: EstadoResistencia,
    *,
    numero_pregunta: int,
) -> list[str]:
    if not er.apuesta_activa:
        return []
    recompensa = er.apuesta_activa.recompensa
    avisos: list[str] = []
    if recompensa.delta_vidas:
        aplicar_recompensa(
            estado,
            er,
            EventoRecompensaResistencia(
                "Apuesta: vida extra",
                delta_vidas=recompensa.delta_vidas,
            ),
        )
        n = recompensa.delta_vidas
        avisos.append(f"Apuesta: +{n} vida" + ("s" if n > 1 else ""))
    if recompensa.powerup_id:
        er.agregar_powerup(recompensa.powerup_id, recompensa.cantidad_powerup)
        nom = etiqueta_powerup(recompensa.powerup_id)
        avisos.append(f"Apuesta: {nom}")
    elif recompensa.powerup_aleatorio:
        rng = rng_partida(er, numero_pregunta * 19 + 7701)
        pid = rng.choice(POWERUPS_LOOT)
        er.agregar_powerup(pid, 1)
        avisos.append(f"Apuesta: {etiqueta_powerup(pid)}")
    return avisos


def _aplicar_penalizacion_apuesta(
    estado: EstadoPartida,
    er: EstadoResistencia,
    *,
    fallo: bool,
    numero_pregunta: int,
) -> tuple[bool, list[str]]:
    """Penalización de la apuesta activa. Devuelve (fin_partida, avisos)."""
    if not fallo or not er.apuesta_activa:
        return False, []
    coste = er.apuesta_activa.coste
    avisos: list[str] = []
    if coste.fin_partida:
        if estado.vidas_restantes is not None:
            estado.vidas_restantes = 0
        avisos.append("Apuesta perdida: fin de partida.")
        return True, avisos
    extra = max(0, coste.vidas_fallo - 1)
    if extra > 0 and estado.vidas_restantes is not None:
        estado.vidas_restantes = max(0, estado.vidas_restantes - extra)
    if coste.puntos_perdidos > 0:
        estado.puntos_arcade = max(0, estado.puntos_arcade - coste.puntos_perdidos)
        avisos.append(f"Apuesta: −{coste.puntos_perdidos} puntos")
    if coste.pierde_todos_objetos and er.inventario:
        er.inventario.clear()
        avisos.append("Apuesta: pierdes todos los objetos")
    elif coste.pierde_powerup_aleatorio and er.inventario:
        rng = rng_partida(er, numero_pregunta * 23 + 8803)
        candidatos = [pid for pid, n in er.inventario.items() if n > 0]
        if candidatos:
            pid = rng.choice(candidatos)
            er.consumir_powerup(pid)
            avisos.append(f"Apuesta: pierdes {etiqueta_powerup(pid)}")
    return False, avisos


def procesar_turno_resistencia(
    estado: EstadoPartida,
    er: EstadoResistencia,
    p: Pregunta,
    resultado: ResultadoRespuesta,
    *,
    indice_pregunta: int,
) -> ResultadoTurnoResistencia:
    """Evalúa la respuesta del jugador. Las vidas solo bajan por fallo o tiempo agotado."""
    acierto = resultado.acierto and not resultado.tiempo_agotado
    fallo = not acierto
    mult_apuesta = 1
    if acierto and er.apuesta_activa:
        mult_apuesta = max(1, er.apuesta_activa.recompensa.mult_puntos)

    if fallo and er.escudo_activo:
        er.escudo_activo = False
        solucion = None
        if estado.reglas.mostrar_solucion_tras_fallo:
            from Comun.motor_nucleo import texto_solucion

            solucion = texto_solucion(p)
        return ResultadoTurnoResistencia(
            feedback=FeedbackRespuesta(
                mensaje="Escudo: el fallo no cuesta vida ni corta la racha.",
                solucion=solucion,
            ),
            reintentar_pregunta=True,
        )

    feedback = evaluar_respuesta(p, estado, resultado)

    _fin_apuesta, avisos_apuesta_fallo = _aplicar_penalizacion_apuesta(
        estado,
        er,
        fallo=fallo,
        numero_pregunta=indice_pregunta,
    )
    if fallo and (
        (estado.reglas.tiene_vidas() and (estado.vidas_restantes or 0) <= 0)
        or _fin_apuesta
    ):
        feedback = replace(feedback, sin_vidas=True)

    avisos_post: list[str] = list(avisos_apuesta_fallo)
    if acierto:
        er.registrar_acierto()
        avisos_post.extend(
            _aplicar_recompensa_apuesta_exito(
                estado, er, numero_pregunta=indice_pregunta
            )
        )
        for recompensa in tirar_recompensas_tras_acierto(er, numero_pregunta=indice_pregunta):
            aplicar_recompensa(estado, er, recompensa)
            avisos_post.append(formatear_aviso_recompensa(recompensa.etiqueta))
    elif fallo:
        er.registrar_fallo()

    avisos_post.extend(
        procesar_post_turno_resistencia(er, acierto=acierto, numero_pregunta=indice_pregunta)
    )

    if acierto and er.apuesta_activa:
        msg = feedback.mensaje
        if msg.startswith("Correcto"):
            extras_apuesta: list[str] = []
            if mult_apuesta > 1:
                extras_apuesta.append(f"×{mult_apuesta}")
            r = er.apuesta_activa.recompensa
            if r.delta_vidas > 0:
                extras_apuesta.append(f"+{r.delta_vidas} vida" + ("s" if r.delta_vidas > 1 else ""))
            if r.powerup_id or r.powerup_aleatorio:
                extras_apuesta.append("objeto")
            if extras_apuesta:
                feedback = replace(
                    feedback,
                    mensaje=f"{msg} (apuesta: {', '.join(extras_apuesta)})",
                )

    return ResultadoTurnoResistencia(
        feedback=feedback,
        avisos_extra=tuple(avisos_post),
        mult_apuesta=mult_apuesta if acierto else 1,
    )


__all__ = [
    "APUESTAS_DISPONIBLES",
    "ApuestaRiesgo",
    "BloqueFiltroActivo",
    "CosteApuesta",
    "CuotasBancoResistencia",
    "DesafioBloqueTiempoResistencia",
    "EMOJI_POWERUP",
    "EstadoResistencia",
    "EventoRecompensaResistencia",
    "FACTOR_EVENTO_BUENO_ESCALADA",
    "FACTOR_TIRADA_RECOMPENSA",
    "LETRAS_OPCION",
    "MaldicionActiva",
    "MAX_TIRADAS_RECOMPENSA_ACIERTO",
    "POWERUPS",
    "POWERUPS_LOOT",
    "PREGUNTA_MIN_DESAFIO_BLOQUE_RESISTENCIA",
    "PREGUNTA_MIN_EVENTOS_ALEATORIOS",
    "PREGUNTAS_HASTA_EXTREMO_PROB",
    "PRESION_RACHA_UMBRAL",
    "PROB_BUENA_FINAL",
    "PROB_BUENA_INICIAL",
    "PROB_MALA_FINAL",
    "PROB_MALA_INICIAL",
    "RecompensaApuesta",
    "ResultadoTurnoResistencia",
    "VIDAS_MAX_ABSOLUTO",
    "VIDAS_MAX_INICIAL",
    "VIDAS_MIN_CAP",
    "aplicar_bonificaciones_puntos_resistencia",
    "aplicar_efectos_maldicion",
    "aplicar_modificadores_visuales_escalada",
    "aplicar_presion_racha_modificadores",
    "aplicar_recompensa",
    "aviso_apuesta_activa",
    "bonificacion_puntos_racha",
    "configurar_partida_resistencia",
    "consumir_bloque_filtro",
    "crear_estado_resistencia",
    "cuotas_banco_resistencia",
    "descripcion_evento_etiqueta",
    "descripcion_powerup",
    "desafio_bloque_expirado",
    "emoji_aviso_exclusiva",
    "emoji_evento_etiqueta",
    "emoji_powerup",
    "emoji_recompensa_etiqueta",
    "etiqueta_powerup",
    "etiqueta_powerup_con_emoji",
    "exceso_presion_racha",
    "factor_bueno_resistencia",
    "factor_malo_resistencia",
    "factor_progreso_banco_resistencia",
    "factor_progreso_resistencia",
    "finalizar_partida_por_desafio_bloque",
    "formatear_aviso_desafio_bloque",
    "formatear_aviso_apuesta",
    "formatear_aviso_bloque",
    "formatear_aviso_evento",
    "formatear_aviso_maldicion",
    "formatear_aviso_presion_racha",
    "formatear_aviso_recompensa",
    "intensidad_presion_racha",
    "letras_ocultas_bomba",
    "letras_ocultas_fifty_fifty",
    "letras_ocultas_por_cantidad",
    "oferta_apuesta_para_pregunta",
    "preparar_eventos_nuevo_turno",
    "preparar_presion_racha_turno",
    "presion_racha_umbral",
    "probabilidad_buena_resistencia",
    "probabilidad_desafio_bloque_resistencia",
    "probabilidad_evento_bueno_escalada",
    "probabilidad_mala_resistencia",
    "procesar_post_turno_resistencia",
    "procesar_turno_resistencia",
    "progreso_probabilidad_resistencia",
    "params_desafio_bloque_resistencia",
    "pregunta_compatible_bloque",
    "prefijar_emoji",
    "rng_partida",
    "separar_emoji_mensaje",
    "texto_pregunta_para_turno",
    "texto_pregunta_visible",
    "texto_progreso_resistencia",
    "texto_segmento_desafio_bloque",
    "tiempo_pregunta_efectivo",
    "tirar_recompensas_tras_acierto",
    "usar_powerup",
]
