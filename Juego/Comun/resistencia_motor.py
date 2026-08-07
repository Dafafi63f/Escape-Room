"""Motor del modo resistencia: probabilidades, estado, powerups, iconos, mecánicas y turnos."""

from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from Comun.config_historia import GRUPOS_TEMATICOS, descripcion_ambito_curso_semestre, etiqueta_grupo_tematico

if TYPE_CHECKING:
    from Comun.maldiciones_partida import PityMaldicionesResistencia
    from Comun.pity_variedad_resistencia import PityVariedadResistencia
    from Comun.resistencia_partida import EscaladaResistencia, PityEventosResistencia
from Comun.emojis_escape import EMOJI_NIEBLA_OPCIONES
from Comun.emojis_partida import EMOJI_BLOQUE_FILTRO_RESISTENCIA
from Comun.modelos import Pregunta
from Comun.motor_nucleo import EstadoPartida, FeedbackRespuesta, ResultadoRespuesta, evaluar_respuesta
from Comun.pool_libre import EstadoSeleccionPool
from Comun.reglas import sumar_puntos_arcade
from Comun.objetos_partida import (
    EMOJI_POWERUP,
    LETRAS_OPCION,
    MENSAJE_POWERUP_YA_USADO,
    POWERUPS,
    POWERUPS_INCOMPATIBLES_EN_PREGUNTA,
    POWERUPS_LOOT,
    descripcion_powerup,
    emoji_powerup,
    etiqueta_powerup,
    elegir_powerup_loot,
    letras_ocultas_bomba,
    letras_ocultas_comodin,
    letras_ocultas_descarte_inteligente,
    letras_ocultas_fifty_fifty,
    letras_ocultas_por_cantidad,
    puede_usar_powerup_en_pregunta,
    revocar_powerup_usado,
    segundos_pregunta_restantes,
    tiempo_pregunta_agotado,
)
from Comun.semillas import RngPartida, crear_rng_partida, semilla_partida_aleatoria

if TYPE_CHECKING:
    from Comun.eventos_partida import ApuestaRiesgo, EventoSiNo


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

# Catálogo de maldiciones de resistencia: ver ``maldiciones_partida``.

from Comun.maldiciones_partida import (
    DesafioBloqueTiempoResistencia,
    DesafioMaldicionTiempo,
    ModoFinMaldicion,
    PREGUNTA_MIN_MALDICION_DESAFIO_TIEMPO_RESISTENCIA,
    formatear_aviso_maldicion_desafio,
    instanciar_maldicion_desafio_tiempo,
    maldicion_desafio_expirada,
    maldicion_tiene_desafio_tiempo,
    maldicion_usa_duracion_preguntas,
    mensaje_fin_partida_maldicion_desafio,
    params_maldicion_desafio_tiempo,
    texto_segmento_maldicion_desafio,
    tick_maldicion_desafio_tras_acierto,
)

# Alias histórico.
PREGUNTA_MIN_DESAFIO_BLOQUE_RESISTENCIA = PREGUNTA_MIN_MALDICION_DESAFIO_TIEMPO_RESISTENCIA
# Presión por racha alta: la pregunta actual se vuelve más exigente (sin castigos automáticos).
PRESION_RACHA_UMBRAL = 25
_PRESION_RACHA_ESCALA = 30.0


def probabilidad_maldicion_desafio_tiempo_resistencia(numero_pregunta: int) -> float:
    if numero_pregunta < PREGUNTA_MIN_MALDICION_DESAFIO_TIEMPO_RESISTENCIA:
        return 0.0
    t = factor_progreso_resistencia(numero_pregunta)
    if t < 0.5:
        return 0.0
    return 0.06 + 0.14 * min(1.0, (t - 0.5) * 2.0)


def probabilidad_desafio_bloque_resistencia(numero_pregunta: int) -> float:
    return probabilidad_maldicion_desafio_tiempo_resistencia(numero_pregunta)


def params_desafio_bloque_resistencia(numero_pregunta: int) -> tuple[int, int]:
    return params_maldicion_desafio_tiempo(numero_pregunta)


def formatear_aviso_desafio_bloque(desafio: DesafioMaldicionTiempo) -> str:
    return formatear_aviso_maldicion_desafio(desafio)


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
    solo_revisadas: bool = False
    es_jefe: bool = False
    dificultad_jefe: str | None = None
    preguntas_totales: int = 0


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
        return f"de {', '.join(materias[:2])}{resto}"
    return f"de {etiqueta_grupo_tematico(grupo)}"


def _descripcion_tipo(tipo: str) -> str:
    etiqueta = _ETIQUETA_TIPO.get(tipo, tipo)
    if tipo in _ETIQUETA_TIPO:
        return f"de {etiqueta}"
    return f"de tipo {etiqueta}"


def _descripcion_tipo_bloque(tipo: str) -> str:
    """Etiqueta de bloque por tipo: deja claro que no es una materia concreta."""
    etiqueta = _ETIQUETA_TIPO.get(tipo, tipo)
    return f"de tipo {etiqueta} (cualquier materia)"


def _descripcion_curso(curso: str) -> str:
    return descripcion_ambito_curso_semestre(curso, None)


def _descripcion_semestre(curso: str, semestre: str) -> str:
    return descripcion_ambito_curso_semestre(curso, semestre)


@dataclass
class MaldicionActiva:
    id: str
    etiqueta: str
    modo_fin: ModoFinMaldicion = ModoFinMaldicion.DURACION
    preguntas_restantes: int = 1
    multiplicador_puntos: float = 1.0
    fin_partida_si_fallo: bool = False
    desafio: DesafioMaldicionTiempo | None = None


# --- Estado ---

VIDAS_MAX_INICIAL = 3
VIDAS_MAX_ABSOLUTO = 9
VIDAS_MIN_CAP = 2


def _pity_maldiciones_resistencia_nuevo():
    from Comun.maldiciones_partida import PityMaldicionesResistencia

    return PityMaldicionesResistencia()


def _pity_eventos_resistencia_nuevo():
    from Comun.resistencia_partida import PityEventosResistencia

    return PityEventosResistencia()


@dataclass
class EstadoResistencia:
    """Racha de aciertos seguidos (se corta al fallar); vidas e inventario aparte."""

    racha: int = 0
    mejor_racha: int = 0  # récord de la partida; solo resumen/estadísticas, no afecta al juego
    vidas_max: int = VIDAS_MAX_INICIAL
    inventario: dict[str, int] = field(default_factory=dict)
    letras_ocultas: frozenset[str] = field(default_factory=frozenset)  # bomba / 50-50: sin botón
    letras_niebla: frozenset[str] = field(default_factory=frozenset)  # niebla: botón con «???»
    tiempo_extra_seg: int = 0
    factor_velocidad_tiempo: float = 1.0
    segunda_oportunidad_activa: bool = False
    doble_o_nada_activo: bool = False
    skip_sin_cortar_racha: int = 0
    relampago_forzado_seg: int | None = None
    escudo_activo: bool = False
    bonus_proximo_acierto: int = 0
    ultimo_evento: str = ""
    semilla_partida: int | None = None
    rng: RngPartida | None = field(default=None, repr=False)
    bloque_filtro: BloqueFiltroActivo | None = None
    evento_si_no: EventoSiNo | None = None
    apuesta_activa: ApuestaRiesgo | None = None
    preguntas_sin_evento_si_no: int = 0
    preguntas_sin_jefe: int = 0
    preguntas_sin_desafio_bloque: int = 0
    preguntas_sin_bloque: int = 0
    tipos_evento_si_no_vistos: set[str] = field(default_factory=set)
    kinds_bloque_vistos: set[str] = field(default_factory=set)
    variedad_vista: set[str] = field(default_factory=set)
    pity_variedad: PityVariedadResistencia | None = None
    pregunta_final_jefe: bool = False
    maldicion: MaldicionActiva | None = None
    ventana_resultados: list[bool] = field(default_factory=list)
    tiradas_recompensa: int = 0
    objetos_bloqueados: bool = False
    powerups_usados_en_pregunta: set[str] = field(default_factory=set)
    banco_resistencia: object | None = None
    sin_escalada_dificultad: bool = False
    presion_racha_intensidad: float = 0.0
    pity_eventos: PityEventosResistencia = field(default_factory=lambda: _pity_eventos_resistencia_nuevo())
    pity_maldiciones: PityMaldicionesResistencia = field(
        default_factory=lambda: _pity_maldiciones_resistencia_nuevo()
    )

    def reset_pregunta(self) -> None:
        self.letras_ocultas = frozenset()
        self.letras_niebla = frozenset()
        self.tiempo_extra_seg = 0
        self.factor_velocidad_tiempo = 1.0
        self.segunda_oportunidad_activa = False
        self.doble_o_nada_activo = False
        self.relampago_forzado_seg = None
        self.ultimo_evento = ""
        self.presion_racha_intensidad = 0.0
        self.objetos_bloqueados = False
        self.powerups_usados_en_pregunta.clear()
        from Comun.maldiciones_partida import reaplicar_efectos_maldicion_persistente

        reaplicar_efectos_maldicion_persistente(self)

    def reiniciar_slot_pregunta(self) -> None:
        """Nueva pregunta en el mismo turno (cambio): limpia ayudas de la anterior."""
        self.letras_ocultas = frozenset()
        self.tiempo_extra_seg = 0
        self.factor_velocidad_tiempo = 1.0
        self.segunda_oportunidad_activa = False
        self.doble_o_nada_activo = False
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
    return texto_segmento_maldicion_desafio(er.maldicion)


def desafio_bloque_expirado(er: EstadoResistencia) -> bool:
    return maldicion_desafio_expirada(er.maldicion)


def _intentar_activar_maldicion_desafio_tiempo(
    er: EstadoResistencia,
    numero_pregunta: int,
) -> str | None:
    from Comun.maldiciones_partida import (
        actualizar_pity_maldiciones_resistencia,
        probabilidad_activar_maldicion_desafio_resistencia,
    )

    if er.maldicion is not None:
        return None
    er.preguntas_sin_desafio_bloque += 1
    prob_base = probabilidad_maldicion_desafio_tiempo_resistencia(numero_pregunta)
    prob_base += min(0.35, er.preguntas_sin_desafio_bloque * 0.012)
    prob = probabilidad_activar_maldicion_desafio_resistencia(
        numero_pregunta,
        er.pity_maldiciones,
        prob_base=prob_base,
        pity_variedad=er.pity_variedad,
    )
    if prob <= 0.0:
        return None
    rng = rng_partida(er)
    if rng.random() > prob:
        return None
    er.preguntas_sin_desafio_bloque = 0
    maldicion = instanciar_maldicion_desafio_tiempo(numero_pregunta)
    er.maldicion = maldicion
    actualizar_pity_maldiciones_resistencia(
        er.pity_maldiciones,
        numero_pregunta=numero_pregunta,
        maldicion_id_activada=maldicion.id,
    )
    from Comun.pity_variedad_resistencia import registrar_variedad_resistencia

    registrar_variedad_resistencia(er, "maldicion")
    desafio = maldicion.desafio
    assert desafio is not None
    return formatear_aviso_maldicion_desafio(desafio)


def _intentar_activar_desafio_bloque(
    er: EstadoResistencia,
    numero_pregunta: int,
) -> str | None:
    return _intentar_activar_maldicion_desafio_tiempo(er, numero_pregunta)


def finalizar_partida_por_desafio_bloque(estado: EstadoPartida, er: EstadoResistencia) -> str:
    from Comun.maldiciones_partida import limpiar_efectos_maldicion_resistencia

    er.maldicion = None
    limpiar_efectos_maldicion_resistencia(er)
    if estado.vidas_restantes is not None:
        estado.vidas_restantes = 0
    return mensaje_fin_partida_maldicion_desafio()


_RE_TOTAL_BLOQUE_FILTRO = re.compile(r"(?:Bloque|Jefe):\s*(\d+)\s*preguntas", re.I)


def _preguntas_totales_bloque_filtro(bf: BloqueFiltroActivo) -> int:
    if bf.preguntas_totales > 0:
        return bf.preguntas_totales
    coincidencia = _RE_TOTAL_BLOQUE_FILTRO.search(bf.etiqueta)
    if coincidencia:
        return int(coincidencia.group(1))
    return max(1, bf.preguntas_restantes)


def _descripcion_corta_bloque_filtro(bf: BloqueFiltroActivo) -> str:
    prefijo = "Jefe: " if bf.es_jefe else "Bloque: "
    resto = bf.etiqueta.removeprefix(prefijo) if bf.etiqueta.startswith(prefijo) else bf.etiqueta
    if " preguntas " in resto:
        corta = resto.split(" preguntas ", 1)[1]
    else:
        corta = resto.strip()
    return corta.removeprefix("de ").strip()


def segmento_bloque_filtro_barra(er: EstadoResistencia) -> str | None:
    """Texto compacto del bloque/jefe activo para la barra superior."""
    bf = er.bloque_filtro
    if bf is None or bf.preguntas_restantes <= 0:
        return None
    from Comun.jefe_partida import tamano_coherente_bloque_o_jefe

    total = _preguntas_totales_bloque_filtro(bf)
    if not tamano_coherente_bloque_o_jefe(total, es_jefe=bf.es_jefe):
        return None
    actual = total - bf.preguntas_restantes + 1
    progreso = f"{actual}/{total}"
    if bf.es_jefe:
        return f"Jefe {progreso}"
    return progreso


def texto_bloque_filtro_extra(er: EstadoResistencia) -> str | None:
    """Línea persistente bajo la barra mientras dura un bloque o jefe."""
    bf = er.bloque_filtro
    if bf is None or bf.preguntas_restantes <= 0:
        return None
    segmento = segmento_bloque_filtro_barra(er)
    if segmento is None:
        return None
    desc = _descripcion_corta_bloque_filtro(bf)
    if bf.es_jefe:
        from Comun.emojis_escape import EMOJI_JEFE

        return prefijar_emoji(f"Jefe activo: {desc} ({segmento})", EMOJI_JEFE)
    return prefijar_emoji(
        f"Bloque activo: {desc} ({segmento})",
        EMOJI_BLOQUE_FILTRO_RESISTENCIA,
    )


_PREF_BOTIN_JEFE = "Botín de jefe: "
_ETIQUETA_ENFRENTAMIENTO_JEFE = "Enfrentamiento con jefe"
_PREF_JEFE = "Jefe:"
_ETIQUETA_RELAMPAGO = "Relámpago"
_PREF_NIEBLA = "Niebla:"
_ETIQUETA_DOBLE_PUNTOS = "Doble puntos"
_ETIQUETA_TRIPLE_PUNTOS = "Triple puntos"
_ETIQUETA_PREGUNTA_DIFICIL = "Pregunta difícil"
_ETIQUETA_PREGUNTA_EXTRA_DIFICIL = "Pregunta extra difícil"


def formatear_aviso_jefe(etiqueta: str) -> str:
    """Popup al empezar un jefe (10 preguntas, botín al completarlo)."""
    from Comun.emojis_escape import EMOJI_JEFE

    resto = etiqueta.removeprefix(f"{_PREF_JEFE} ").strip()
    texto = (
        f"¡{_ETIQUETA_ENFRENTAMIENTO_JEFE}! {resto}. "
        "Derrotarlo al completar las preguntas da botín especial."
    )
    return prefijar_emoji(texto, EMOJI_JEFE)


def _resumen_premio_jefe(recompensa: EventoRecompensaResistencia) -> str:
    if recompensa.delta_vidas > 0:
        return "+1 vida"
    if recompensa.delta_vidas_max > 0:
        return "corazón máximo +1"
    if recompensa.powerup_id:
        return etiqueta_powerup(recompensa.powerup_id)
    if recompensa.bonus_proximo_acierto > 0:
        from Comun.economia_partida import texto_bonus_amuleto

        return texto_bonus_amuleto(recompensa.bonus_proximo_acierto)
    premio = recompensa.etiqueta.removeprefix(_PREF_BOTIN_JEFE).strip()
    return premio or recompensa.etiqueta


def formatear_aviso_botin_jefe_resistencia(
    recompensas: list[EventoRecompensaResistencia],
) -> str:
    """Un solo aviso con todo el botín del jefe (evita 3–4 popups sueltos)."""
    from Comun.emojis_escape import EMOJI_JEFE

    premios = ", ".join(_resumen_premio_jefe(r) for r in recompensas)
    texto = f"¡Jefe derrotado! Botín: {premios}."
    return prefijar_emoji(texto, EMOJI_JEFE)


# --- Powerups (catálogo en objetos_partida) ---

# Escala la prob. de premio por tirada (la curva buena va de ~90 % a ~3 %).
FACTOR_TIRADA_RECOMPENSA = 0.20
# Cupo de tiradas de recompensa tras cada acierto (independiente de eventos/popups).
MAX_TIRADAS_RECOMPENSA_ACIERTO = 2


@dataclass(frozen=True)
class EventoRecompensaResistencia:
    etiqueta: str
    delta_vidas: int = 0
    delta_vidas_max: int = 0
    powerup_id: str | None = None
    cantidad_powerup: int = 1
    bonus_proximo_acierto: int = 0


def _familia_recompensa_resistencia(evento: EventoRecompensaResistencia) -> str:
    if evento.delta_vidas > 0:
        return "vida"
    if evento.delta_vidas_max > 0:
        return "vida_max_mas"
    if evento.delta_vidas_max < 0:
        return "vida_max_menos"
    if evento.bonus_proximo_acierto:
        return "amuleto"
    if evento.powerup_id:
        return f"objeto:{evento.powerup_id}"
    return evento.etiqueta


_MAX_INTENTOS_RECOMPENSA_ALEATORIA = 12


@dataclass
class _ContextoRecompensaTurno:
    vidas: int | None
    vidas_max: int
    bonus_proximo: int
    familias_otorgadas: set[str]

    @classmethod
    def desde(
        cls,
        estado: EstadoPartida,
        er: EstadoResistencia,
        familias_otorgadas: set[str] | None = None,
    ) -> _ContextoRecompensaTurno:
        return cls(
            estado.vidas_restantes,
            er.vidas_max,
            er.bonus_proximo_acierto,
            set(familias_otorgadas or ()),
        )

    def _util(self, evento: EventoRecompensaResistencia) -> bool:
        if evento.delta_vidas > 0:
            if self.vidas is None:
                return False
            return self.vidas < self.vidas_max
        if evento.delta_vidas_max > 0:
            return self.vidas_max < VIDAS_MAX_ABSOLUTO
        if evento.delta_vidas_max < 0:
            return self.vidas_max > VIDAS_MIN_CAP
        if evento.bonus_proximo_acierto:
            return self.bonus_proximo <= 0
        return True

    def puede_otorgar(self, evento: EventoRecompensaResistencia) -> bool:
        if not self._util(evento):
            return False
        return _familia_recompensa_resistencia(evento) not in self.familias_otorgadas

    def registrar(self, evento: EventoRecompensaResistencia) -> None:
        if evento.delta_vidas_max:
            self.vidas_max = max(
                VIDAS_MIN_CAP,
                min(VIDAS_MAX_ABSOLUTO, self.vidas_max + evento.delta_vidas_max),
            )
            if self.vidas is not None and self.vidas > self.vidas_max:
                self.vidas = self.vidas_max
        if evento.delta_vidas and self.vidas is not None:
            self.vidas = max(0, min(self.vidas_max, self.vidas + evento.delta_vidas))
        if evento.bonus_proximo_acierto:
            self.bonus_proximo = evento.bonus_proximo_acierto
        self.familias_otorgadas.add(_familia_recompensa_resistencia(evento))


def _recompensa_resistencia_util(
    estado: EstadoPartida,
    er: EstadoResistencia,
    evento: EventoRecompensaResistencia,
) -> bool:
    return _ContextoRecompensaTurno.desde(estado, er)._util(evento)


def _otorgar_recompensa_resistencia(
    estado: EstadoPartida,
    er: EstadoResistencia,
    evento: EventoRecompensaResistencia,
    familias_otorgadas: set[str],
) -> bool:
    ctx = _ContextoRecompensaTurno.desde(estado, er, familias_otorgadas)
    if not ctx.puede_otorgar(evento):
        return False
    aplicar_recompensa(estado, er, evento)
    ctx.registrar(evento)
    familias_otorgadas.clear()
    familias_otorgadas.update(ctx.familias_otorgadas)
    return True


def letras_ocultas_niebla(
    p: Pregunta,
    cantidad: int = 1,
    *,
    rng: random.Random,
) -> frozenset[str]:
    """Oculta respuestas al azar (correcta o incorrecta); como máximo 1 en niebla."""
    if cantidad <= 0:
        return frozenset()
    letras = list(p.opciones.keys())
    rng.shuffle(letras)
    return frozenset(letras[: min(cantidad, len(letras), 1)])


def _generar_recompensa_aleatoria(
    rng: random.Random,
    *,
    numero_pregunta: int,
    er: EstadoResistencia,
    estado: EstadoPartida,
    ctx: _ContextoRecompensaTurno | None = None,
) -> EventoRecompensaResistencia:

    factor_bueno = max(0.08, factor_bueno_resistencia(numero_pregunta))
    factor_malo = max(0.08, factor_malo_resistencia(numero_pregunta))
    vidas = ctx.vidas if ctx is not None else estado.vidas_restantes
    vidas_max = ctx.vidas_max if ctx is not None else er.vidas_max
    bonus_proximo = ctx.bonus_proximo if ctx is not None else er.bonus_proximo_acierto
    opciones: list[tuple[float, EventoRecompensaResistencia]] = []

    if vidas is not None and vidas < vidas_max:
        opciones.append(
            (
                0.20 * factor_bueno,
                EventoRecompensaResistencia("¡Vida extra!", delta_vidas=1),
            )
        )
    if vidas_max < VIDAS_MAX_ABSOLUTO:
        opciones.append(
            (
                0.10 * factor_bueno,
                EventoRecompensaResistencia("Corazón máximo +1", delta_vidas_max=1),
            )
        )
    if vidas_max > VIDAS_MIN_CAP:
        opciones.append(
            (
                0.14 * factor_malo,
                EventoRecompensaResistencia("Corazón máximo −1", delta_vidas_max=-1),
            )
        )
    if bonus_proximo <= 0:
        from Comun.economia_partida import bonus_amuleto_arcade

        bonus_am = bonus_amuleto_arcade(numero_pregunta=numero_pregunta)
        opciones.append(
            (
                0.06 * factor_bueno,
                EventoRecompensaResistencia(
                    "Amuleto arcade",
                    bonus_proximo_acierto=bonus_am,
                ),
            )
        )

    opciones = [
        (peso, ev)
        for peso, ev in opciones
        if (ctx.puede_otorgar(ev) if ctx is not None else _recompensa_resistencia_util(estado, er, ev))
    ]
    if not opciones:
        pid = elegir_powerup_loot(er.inventario, rng)
        return EventoRecompensaResistencia(
            f"Objeto: {etiqueta_powerup(pid)}",
            powerup_id=pid,
        )

    total = sum(p for p, _ in opciones)
    roll = rng.random() * total
    acum = 0.0
    for peso, evento in opciones:
        acum += peso
        if roll < acum:
            return evento
    pid = elegir_powerup_loot(er.inventario, rng)
    return EventoRecompensaResistencia(
        f"Objeto: {etiqueta_powerup(pid)}",
        powerup_id=pid,
    )


def tirar_recompensas_tras_acierto(
    er: EstadoResistencia,
    estado: EstadoPartida,
    *,
    numero_pregunta: int,
    familias_otorgadas: set[str] | None = None,
) -> list[EventoRecompensaResistencia]:
    """Bonificaciones tras acertar; más probables al inicio, raras al final."""

    prob_tirada = probabilidad_buena_resistencia(numero_pregunta) * FACTOR_TIRADA_RECOMPENSA
    resultados: list[EventoRecompensaResistencia] = []
    ctx = _ContextoRecompensaTurno.desde(estado, er, familias_otorgadas)
    for _ in range(MAX_TIRADAS_RECOMPENSA_ACIERTO):
        er.tiradas_recompensa += 1
        rng = rng_partida(er)
        if rng.random() > prob_tirada:
            continue
        recompensa: EventoRecompensaResistencia | None = None
        for _ in range(_MAX_INTENTOS_RECOMPENSA_ALEATORIA):
            candidato = _generar_recompensa_aleatoria(
                rng,
                numero_pregunta=numero_pregunta,
                er=er,
                estado=estado,
                ctx=ctx,
            )
            if not ctx.puede_otorgar(candidato):
                continue
            ctx.registrar(candidato)
            recompensa = candidato
            break
        if recompensa is not None:
            resultados.append(recompensa)
    if familias_otorgadas is not None:
        familias_otorgadas.update(ctx.familias_otorgadas)
    return resultados


def recompensas_completar_jefe_resistencia(
    er: EstadoResistencia,
    estado: EstadoPartida,
    *,
    numero_pregunta: int,
) -> list[EventoRecompensaResistencia]:
    """Botín garantizado al superar un jefe (mejor que las tiradas normales tras acierto)."""
    from Comun.economia_partida import bonus_amuleto_arcade

    rng = rng_partida(er)
    candidatos: list[EventoRecompensaResistencia] = []
    if estado.vidas_restantes is not None and estado.vidas_restantes < er.vidas_max:
        candidatos.append(
            EventoRecompensaResistencia("Botín de jefe: +1 vida", delta_vidas=1)
        )
    elif er.vidas_max < VIDAS_MAX_ABSOLUTO:
        candidatos.append(
            EventoRecompensaResistencia(
                "Botín de jefe: corazón máximo +1",
                delta_vidas_max=1,
            )
        )
    for _ in range(2):
        pid = elegir_powerup_loot(er.inventario, rng)
        candidatos.append(
            EventoRecompensaResistencia(
                f"{_PREF_BOTIN_JEFE}{etiqueta_powerup(pid)}",
                powerup_id=pid,
            )
        )
    if er.bonus_proximo_acierto <= 0:
        candidatos.append(
            EventoRecompensaResistencia(
                "Botín de jefe: amuleto arcade",
                bonus_proximo_acierto=bonus_amuleto_arcade(
                    numero_pregunta=numero_pregunta
                ),
            )
        )
    return candidatos

# --- Iconos ---

_SEPARADOR_EMOJI = "  "


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
    if etiqueta.startswith(_ETIQUETA_RELAMPAGO):
        return "⚡"
    if etiqueta.startswith(_PREF_NIEBLA):
        return EMOJI_NIEBLA_OPCIONES
    if etiqueta == _ETIQUETA_DOBLE_PUNTOS:
        return "✨"
    if etiqueta == _ETIQUETA_TRIPLE_PUNTOS:
        return "💎"
    if etiqueta == _ETIQUETA_PREGUNTA_DIFICIL:
        return "🔥"
    if etiqueta == _ETIQUETA_PREGUNTA_EXTRA_DIFICIL:
        return "☠️"
    if etiqueta.startswith("Bloque:"):
        return EMOJI_BLOQUE_FILTRO_RESISTENCIA
    if etiqueta.startswith(_PREF_JEFE) or _ETIQUETA_ENFRENTAMIENTO_JEFE in etiqueta:
        from Comun.emojis_escape import EMOJI_JEFE

        return EMOJI_JEFE
    if "Jefe derrotado" in etiqueta:
        from Comun.emojis_escape import EMOJI_JEFE

        return EMOJI_JEFE
    if "Maldición" in etiqueta:
        return "💀"
    if "Hito racha" in etiqueta:
        return "🏅"

    from Comun.eventos_partida import APUESTAS_DISPONIBLES

    if any(ap.etiqueta == etiqueta for ap in APUESTAS_DISPONIBLES):
        return "🎰"
    return "🎲"


def descripcion_evento_etiqueta(etiqueta: str) -> str:
    if etiqueta.startswith(_ETIQUETA_RELAMPAGO):
        seg = etiqueta.split(":")[-1].strip() if ":" in etiqueta else ""
        return f"Menos tiempo para responder{f' ({seg})' if seg else ''}."
    if etiqueta.startswith(_PREF_NIEBLA):
        return "Se ocultará 1 respuesta al azar (puede ser la correcta)."
    if etiqueta in {_ETIQUETA_DOBLE_PUNTOS, _ETIQUETA_TRIPLE_PUNTOS}:
        return f"Si aciertas, sumarás {etiqueta.lower()} en esta pregunta."
    if etiqueta == _ETIQUETA_PREGUNTA_DIFICIL:
        return "Esta pregunta será más difícil de lo habitual en esta fase."
    if etiqueta == _ETIQUETA_PREGUNTA_EXTRA_DIFICIL:
        return "Una pregunta muy exigente para esta fase de la partida."
    if etiqueta.startswith(_PREF_JEFE) or _ETIQUETA_ENFRENTAMIENTO_JEFE in etiqueta:
        return (
            "Bloque de 10 preguntas del mismo tema. "
            "Al completarlo recibes botín especial de jefe."
        )
    return etiqueta


def emoji_recompensa_etiqueta(etiqueta: str) -> str:
    from Comun.emojis_partida import emoji_recompensa_por_etiqueta

    return emoji_recompensa_por_etiqueta(etiqueta)


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
        texto = "La racha aprieta: puede ocultarse una respuesta."
    elif intensidad < 0.65:
        texto = "Presión de la racha: menos margen y niebla en opciones."
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
    if base >= 0.25:
        seg = max(5, int(14 - 8 * base))
        if er.relampago_forzado_seg is None or er.relampago_forzado_seg > seg:
            er.relampago_forzado_seg = seg
    if niebla_ok and base >= 0.4:
        er.letras_niebla = er.letras_niebla | letras_ocultas_niebla(
            p,
            1,
            rng=rng_partida(er),
        )
    if base >= 0.75:
        rng = rng_partida(er)
        if rng.random() < 0.35 + 0.4 * base:
            er.objetos_bloqueados = True

    if t <= 1.0:
        return

    exceso = t - 1.0
    seg_ext = max(3, int(6 - 2 * min(exceso, 1.5)))
    if er.relampago_forzado_seg is None or er.relampago_forzado_seg > seg_ext:
        er.relampago_forzado_seg = seg_ext
    if niebla_ok:
        er.letras_niebla = er.letras_niebla | letras_ocultas_niebla(
            p,
            1,
            rng=rng_partida(er),
        )
    er.objetos_bloqueados = True

def rng_partida(er: EstadoResistencia) -> RngPartida:
    if er.rng is None:
        if er.semilla_partida is None:
            er.semilla_partida = semilla_partida_aleatoria()
        er.rng = crear_rng_partida(er.semilla_partida)
    return er.rng


def configurar_partida_resistencia(
    er: EstadoResistencia,
    *,
    preset_id: str,
    sin_escalada_dificultad: bool = False,
) -> None:
    del preset_id
    er.sin_escalada_dificultad = sin_escalada_dificultad
    if er.semilla_partida is None:
        er.semilla_partida = semilla_partida_aleatoria()
    if er.rng is None:
        er.rng = crear_rng_partida(er.semilla_partida)
    if er.pity_variedad is None:
        from Comun.pity_variedad_resistencia import cargar_pity_variedad_resistencia

        er.pity_variedad = cargar_pity_variedad_resistencia()


def texto_progreso_resistencia(er: EstadoResistencia, numero_pregunta: int) -> str:
    return f"{numero_pregunta}  Racha {er.racha}"


def _pregunta_cumple_bloque(p: Pregunta, bloque: BloqueFiltroActivo) -> bool:
    if bloque.materia and p.materia != bloque.materia:
        return False
    if bloque.solo_revisadas and p.fuente != "dataset":
        return False
    if bloque.tipo and p.tipo != bloque.tipo:
        return False
    if bloque.grupo and p.grupo != bloque.grupo:
        return False
    if bloque.curso and p.curso != bloque.curso:
        return False
    if bloque.semestre and p.semestre != bloque.semestre:
        return False
    if bloque.dificultad_jefe:
        from Comun.jefe_partida import dificultades_permitidas_jefe

        permitidas = dificultades_permitidas_jefe(bloque.dificultad_jefe)
        if permitidas is not None and p.dificultad not in permitidas:
            return False
    return True


def _contar_preguntas_bloque(pool: list[Pregunta], bloque: BloqueFiltroActivo) -> int:
    return sum(1 for p in pool if _pregunta_cumple_bloque(p, bloque))


def _bloque_viable_en_pool(
    pool: list[Pregunta],
    bloque: BloqueFiltroActivo,
    *,
    minimo: int,
) -> bool:
    from Comun.jefe_partida import tamano_coherente_bloque_o_jefe

    total = bloque.preguntas_totales or bloque.preguntas_restantes
    if not tamano_coherente_bloque_o_jefe(total, es_jefe=bloque.es_jefe):
        return False
    return _contar_preguntas_bloque(pool, bloque) >= minimo


def _bloque_filtro_grupo(
    pool: list[Pregunta],
    grupo: str,
    n: int,
) -> BloqueFiltroActivo:
    clave = str(grupo).strip()
    if clave in GRUPOS_TEMATICOS:
        return BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, f"de {GRUPOS_TEMATICOS[clave]}"),
            preguntas_restantes=n,
            preguntas_totales=n,
            grupo=grupo,
        )
    materias = sorted({p.materia for p in pool if p.grupo == grupo and p.materia})
    if len(materias) == 1:
        materia = materias[0]
        return BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, f"de {materia}"),
            preguntas_restantes=n,
            preguntas_totales=n,
            materia=materia,
            solo_revisadas=True,
        )
    return BloqueFiltroActivo(
        etiqueta=_etiqueta_bloque(n, _descripcion_grupo_tematico(grupo, pool)),
        preguntas_restantes=n,
        preguntas_totales=n,
        grupo=grupo,
    )


def consumir_bloque_filtro(er: EstadoResistencia) -> None:
    """Avanza el filtro de bloque; al expirar vuelve al pool por defecto del momento."""
    if not er.bloque_filtro or er.bloque_filtro.preguntas_restantes <= 0:
        return
    era_jefe = er.bloque_filtro.es_jefe
    rest = er.bloque_filtro.preguntas_restantes - 1
    if rest <= 0:
        er.pregunta_final_jefe = era_jefe
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
        solo_revisadas=bf.solo_revisadas,
        es_jefe=bf.es_jefe,
        dificultad_jefe=bf.dificultad_jefe,
        preguntas_totales=bf.preguntas_totales or _preguntas_totales_bloque_filtro(bf),
    )


def _materias_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.materia for p in pool if p.materia})


def _grupos_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.grupo for p in pool if p.grupo})


def _cursos_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.curso for p in pool if p.curso})


def _pares_curso_semestre_en_pool(pool: list[Pregunta]) -> list[tuple[str, str]]:
    return sorted({(p.curso, p.semestre) for p in pool if p.curso and p.semestre})


def _intentar_activar_jefe_resistencia(
    pool: list[Pregunta],
    numero_pregunta: int,
    er: EstadoResistencia,
) -> str | None:
    from Comun.jefe_partida import (
        PREGUNTAS_POR_JEFE,
        elegir_dificultad_jefe_resistencia,
        etiqueta_jefe_grupo,
        prob_jefe_resistencia,
    )
    from Comun.pity_variedad_resistencia import (
        min_pregunta_jefe_resistencia,
        preguntas_hard_pity_jefe_resistencia,
        registrar_variedad_resistencia,
    )

    if er.bloque_filtro and er.bloque_filtro.preguntas_restantes > 0:
        return None
    min_jefe = min_pregunta_jefe_resistencia(er.pity_variedad)
    if numero_pregunta < min_jefe:
        return None

    er.preguntas_sin_jefe += 1
    rng = rng_partida(er)
    forzar = er.preguntas_sin_jefe >= preguntas_hard_pity_jefe_resistencia(
        er.pity_variedad
    )
    prob = prob_jefe_resistencia(er.preguntas_sin_jefe)
    if er.pity_variedad is not None:
        prob = min(0.98, prob + er.pity_variedad.boost_prob("jefe"))
    if not forzar and rng.random() > prob:
        return None

    grupos = _grupos_en_pool(pool)
    if not grupos:
        return None
    grupo = rng.choice(grupos)
    dif = elegir_dificultad_jefe_resistencia(numero_pregunta, rng)
    bloque = BloqueFiltroActivo(
        etiqueta=etiqueta_jefe_grupo(grupo, dificultad=dif, n=PREGUNTAS_POR_JEFE),
        preguntas_restantes=PREGUNTAS_POR_JEFE,
        preguntas_totales=PREGUNTAS_POR_JEFE,
        grupo=grupo,
        es_jefe=True,
        dificultad_jefe=dif,
    )
    if not _bloque_viable_en_pool(pool, bloque, minimo=PREGUNTAS_POR_JEFE):
        bloque = BloqueFiltroActivo(
            etiqueta=etiqueta_jefe_grupo(grupo, dificultad="equilibrado", n=PREGUNTAS_POR_JEFE),
            preguntas_restantes=PREGUNTAS_POR_JEFE,
            preguntas_totales=PREGUNTAS_POR_JEFE,
            grupo=grupo,
            es_jefe=True,
            dificultad_jefe="equilibrado",
        )
        if not _bloque_viable_en_pool(pool, bloque, minimo=PREGUNTAS_POR_JEFE):
            return None

    er.preguntas_sin_jefe = 0
    er.bloque_filtro = bloque
    registrar_variedad_resistencia(er, "jefe")
    return formatear_aviso_jefe(bloque.etiqueta)


def _semestres_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.semestre for p in pool if p.semestre})


def _kind_bloque_filtro(bloque: BloqueFiltroActivo) -> str:
    from Comun.filtros_bloque import clasificar_filtro_bloque, kind_filtro_bloque

    tipo = clasificar_filtro_bloque(
        materia=bloque.materia,
        tipo=bloque.tipo,
        grupo=bloque.grupo,
        curso=bloque.curso,
        semestre=bloque.semestre,
        es_jefe=bloque.es_jefe,
    )
    if tipo is None:
        return "otro"
    return kind_filtro_bloque(tipo)


def _generar_bloque_filtro(
    pool: list[Pregunta],
    numero_pregunta: int,
    er: EstadoResistencia,
) -> BloqueFiltroActivo | None:
    if er.bloque_filtro and er.bloque_filtro.preguntas_restantes > 0:
        return None
    if numero_pregunta < PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        return None
    from Comun.pity_variedad_resistencia import (
        debe_forzar_bloque_resistencia,
        registrar_variedad_resistencia,
    )

    er.preguntas_sin_bloque += 1
    rng = rng_partida(er)
    from Comun.jefe_partida import elegir_tamano_bloque_normal

    prob = probabilidad_buena_resistencia(numero_pregunta) * 0.42
    if er.pity_variedad is not None:
        prob = min(0.95, prob * er.pity_variedad.peso_boost("bloque"))
    forzar = debe_forzar_bloque_resistencia(er)
    if not forzar and rng.random() > prob:
        return None

    n = elegir_tamano_bloque_normal(rng)
    opciones: list[BloqueFiltroActivo] = []
    materias = _materias_en_pool(pool)
    grupos = _grupos_en_pool(pool)
    if materias:
        mat = rng.choice(materias)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, f"de {mat}"),
                preguntas_restantes=n,
                preguntas_totales=n,
                materia=mat,
                solo_revisadas=True,
            )
        )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, _descripcion_tipo_bloque("Calculo")),
            preguntas_restantes=n,
            preguntas_totales=n,
            tipo="Calculo",
        )
    )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, _descripcion_tipo_bloque("Teoria")),
            preguntas_restantes=n,
            preguntas_totales=n,
            tipo="Teoria",
        )
    )
    if grupos:
        g = rng.choice(grupos)
        opciones.append(_bloque_filtro_grupo(pool, g, n))
    cursos = _cursos_en_pool(pool)
    if cursos:
        curso = rng.choice(cursos)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, _descripcion_curso(curso)),
                preguntas_restantes=n,
                preguntas_totales=n,
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
                preguntas_totales=n,
                curso=curso,
                semestre=semestre,
            )
        )
    semestres = _semestres_en_pool(pool)
    if semestres:
        sem = rng.choice(semestres)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, f"del semestre {sem}"),
                preguntas_restantes=n,
                preguntas_totales=n,
                semestre=sem,
            )
        )
    viables = [
        bloque
        for bloque in opciones
        if _bloque_viable_en_pool(pool, bloque, minimo=n)
    ]
    if not viables:
        return None
    pesos = []
    for bloque in viables:
        kind = _kind_bloque_filtro(bloque)
        peso = 1.0
        if kind not in er.kinds_bloque_vistos:
            peso += 0.85
        pesos.append(peso)
    elegido = rng.choices(viables, weights=pesos, k=1)[0]
    er.preguntas_sin_bloque = 0
    er.kinds_bloque_vistos.add(_kind_bloque_filtro(elegido))
    registrar_variedad_resistencia(er, "bloque")
    return elegido


def preparar_eventos_nuevo_turno(
    er: EstadoResistencia,
    pool: list[Pregunta],
    numero_pregunta: int,
    estado: EstadoPartida,
) -> list[str]:
    """Eventos al cargar una pregunta nueva (presión de racha, bloque, evento sí/no)."""
    from Comun.eventos_partida import elegir_evento_si_no

    avisos: list[str] = []
    aviso_presion = preparar_presion_racha_turno(er, numero_pregunta)
    if aviso_presion:
        avisos.append(aviso_presion)
    if not er.sin_escalada_dificultad:
        aviso_jefe = _intentar_activar_jefe_resistencia(pool, numero_pregunta, er)
        if aviso_jefe:
            avisos.append(aviso_jefe)
        elif not er.bloque_filtro or er.bloque_filtro.preguntas_restantes <= 0:
            bloque = _generar_bloque_filtro(pool, numero_pregunta, er)
            if bloque:
                er.bloque_filtro = bloque
                avisos.append(formatear_aviso_bloque(bloque.etiqueta))
    if not er.evento_si_no:
        er.evento_si_no = elegir_evento_si_no(numero_pregunta, er, estado)
    if not er.sin_escalada_dificultad:
        aviso_bloque = _intentar_activar_desafio_bloque(er, numero_pregunta)
        if aviso_bloque:
            avisos.append(aviso_bloque)
    return avisos


def formatear_aviso_bloque(etiqueta: str) -> str:
    return prefijar_emoji(etiqueta, EMOJI_BLOQUE_FILTRO_RESISTENCIA)


def formatear_aviso_maldicion(etiqueta: str) -> str:
    return prefijar_emoji(etiqueta, "💀")


def _activar_maldicion(er: EstadoResistencia, numero_pregunta: int) -> MaldicionActiva | None:
    if er.maldicion is not None:
        return None
    fallos = sum(1 for ok in er.ventana_resultados if not ok)
    if len(er.ventana_resultados) < 3 or fallos < 2:
        return None
    from Comun.maldiciones_partida import (
        elegir_plantilla_maldicion_resistencia,
        instanciar_maldicion_resistencia,
        plantillas_maldicion_resistencia,
        probabilidad_activar_maldicion_fallo_resistencia,
    )

    prob = probabilidad_activar_maldicion_fallo_resistencia(
        numero_pregunta,
        er.pity_maldiciones,
        prob_base=probabilidad_mala_resistencia(numero_pregunta),
        pity_variedad=er.pity_variedad,
    )
    if prob <= 0.0:
        return None
    rng = rng_partida(er)
    if rng.random() > prob:
        return None
    candidatas = plantillas_maldicion_resistencia(numero_pregunta)
    if not candidatas:
        return None
    plantilla = elegir_plantilla_maldicion_resistencia(
        candidatas, er.pity_maldiciones, rng
    )
    return instanciar_maldicion_resistencia(plantilla, rng)


def aplicar_efectos_maldicion(
    er: EstadoResistencia,
    p: Pregunta | None = None,
    *,
    numero_pregunta: int = 0,
) -> None:
    del p, numero_pregunta
    if not er.maldicion:
        return
    from Comun.maldiciones_partida import plantilla_maldicion_resistencia

    plantilla = plantilla_maldicion_resistencia(er.maldicion.id)
    if plantilla is None:
        return
    if plantilla.efecto.bloquea_objetos:
        er.objetos_bloqueados = True


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
        from Comun.maldiciones_partida import (
            limpiar_efectos_maldicion_resistencia,
            maldicion_usa_duracion_preguntas,
        )

        if maldicion_tiene_desafio_tiempo(er.maldicion):
            avisos_desafio = tick_maldicion_desafio_tras_acierto(
                er.maldicion, acierto=acierto
            )
            if avisos_desafio:
                er.maldicion = None
                limpiar_efectos_maldicion_resistencia(er)
            avisos.extend(avisos_desafio)
        elif maldicion_usa_duracion_preguntas(er.maldicion):
            er.maldicion.preguntas_restantes -= 1
            if er.maldicion.preguntas_restantes <= 0:
                er.maldicion = None
                limpiar_efectos_maldicion_resistencia(er)

    nueva: MaldicionActiva | None = None
    if not acierto:
        nueva = _activar_maldicion(er, numero_pregunta)
        if nueva:
            er.maldicion = nueva
            avisos.append(formatear_aviso_maldicion(nueva.etiqueta))
            from Comun.maldiciones_partida import reaplicar_efectos_maldicion_persistente
            from Comun.pity_variedad_resistencia import registrar_variedad_resistencia

            reaplicar_efectos_maldicion_persistente(er)
            registrar_variedad_resistencia(er, "maldicion")

    from Comun.maldiciones_partida import actualizar_pity_maldiciones_resistencia

    actualizar_pity_maldiciones_resistencia(
        er.pity_maldiciones,
        numero_pregunta=numero_pregunta,
        maldicion_id_activada=nueva.id if nueva else None,
        maldicion_vigente=er.maldicion is not None and nueva is None,
    )

    er.apuesta_activa = None
    er.evento_si_no = None
    return avisos


def pregunta_compatible_bloque(p: Pregunta, er: EstadoResistencia) -> bool:
    """Sin bloque activo: todas las preguntas del pool del momento son válidas."""
    if not er.bloque_filtro or er.bloque_filtro.preguntas_restantes <= 0:
        return True
    return _pregunta_cumple_bloque(p, er.bloque_filtro)



def formatear_aviso_recompensa(
    etiqueta: str,
    *,
    bonus_proximo_acierto: int = 0,
) -> str:
    if etiqueta.startswith("Objeto: "):
        texto = f"¡Obtuviste {etiqueta.removeprefix('Objeto: ')}!"
    elif "Botín de jefe" in etiqueta:
        if etiqueta.startswith(_PREF_BOTIN_JEFE):
            premio = etiqueta.removeprefix(_PREF_BOTIN_JEFE)
            texto = f"¡Jefe derrotado! {premio}."
        else:
            texto = etiqueta
    elif "Amuleto arcade" in etiqueta:
        from Comun.economia_partida import bonus_amuleto_arcade, texto_bonus_amuleto

        bonus = bonus_proximo_acierto or bonus_amuleto_arcade()
        texto = f"¡Amuleto activado! {texto_bonus_amuleto(bonus)}."
    elif "Vida extra" in etiqueta:
        texto = "¡Recompensa! +1 vida."
    elif "máximo +1" in etiqueta or "maximo +1" in etiqueta.lower():
        texto = "¡Recompensa! Corazón máximo +1."
    elif "máximo −1" in etiqueta or ("maximo" in etiqueta.lower() and "−1" in etiqueta):
        texto = "¡Recompensa! Corazón máximo −1."
    else:
        texto = etiqueta
    return prefijar_emoji(texto, emoji_recompensa_etiqueta(etiqueta))


def formatear_aviso_evento(etiqueta: str) -> str:
    if etiqueta.startswith(_ETIQUETA_RELAMPAGO):
        seg = etiqueta.split(":")[-1].strip() if ":" in etiqueta else ""
        texto = f"¡Pregunta relámpago!{f' {seg}' if seg else ''}"
    elif etiqueta in {_ETIQUETA_DOBLE_PUNTOS, _ETIQUETA_TRIPLE_PUNTOS}:
        texto = f"¡{etiqueta} en esta pregunta!"
    elif etiqueta.startswith(_PREF_NIEBLA):
        texto = f"¡{etiqueta}!"
    elif etiqueta in {_ETIQUETA_PREGUNTA_DIFICIL, _ETIQUETA_PREGUNTA_EXTRA_DIFICIL}:
        texto = f"¡{etiqueta}!"
    elif etiqueta.startswith(_PREF_JEFE) or _ETIQUETA_ENFRENTAMIENTO_JEFE in etiqueta:
        if _ETIQUETA_ENFRENTAMIENTO_JEFE in etiqueta:
            return etiqueta
        return formatear_aviso_jefe(etiqueta)
    else:
        texto = f"Ahora: {etiqueta}"
    return prefijar_emoji(texto, emoji_evento_etiqueta(etiqueta))



# --- Motor turnos ---
def aviso_apuesta_activa(er: EstadoResistencia) -> str | None:
    if not er.apuesta_activa:
        return None
    from Comun.eventos_partida import formatear_aviso_apuesta

    return formatear_aviso_apuesta(er.apuesta_activa)


@dataclass(frozen=True)
class ResultadoTurnoResistencia:
    feedback: FeedbackRespuesta
    reintentar_pregunta: bool = False
    avisos_extra: tuple[str, ...] = ()
    mult_apuesta: int = 1


def crear_estado_resistencia(vidas_iniciales: int) -> EstadoResistencia:
    er = EstadoResistencia()
    er.vidas_max = vidas_iniciales
    return er


def aplicar_modificadores_visuales_escalada(
    er: EstadoResistencia,
    escalada: EscaladaResistencia,
    p: Pregunta,
    numero_pregunta: int,
) -> None:
    """Oculta respuestas según eventos de la escalada (niebla solo en opciones)."""
    if escalada.opciones_ocultas > 0:
        ocultas = letras_ocultas_niebla(
            p,
            min(escalada.opciones_ocultas, 1),
            rng=rng_partida(er),
        )
        er.letras_niebla = er.letras_niebla | ocultas
    aplicar_presion_racha_modificadores(er, p, numero_pregunta)
    aplicar_efectos_maldicion(er)


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
    if evento.bonus_proximo_acierto:
        er.bonus_proximo_acierto = evento.bonus_proximo_acierto
    if evento.powerup_id:
        er.agregar_powerup(evento.powerup_id, evento.cantidad_powerup)
    er.ultimo_evento = evento.etiqueta


def _aplicar_efecto_powerup_uso(
    powerup_id: str,
    er: EstadoResistencia,
    p: Pregunta,
) -> str | None:
    """Aplica el efecto del powerup; devuelve mensaje de error o None si OK."""
    if powerup_id == "fifty_fifty":
        er.letras_ocultas = letras_ocultas_fifty_fifty(p)
    elif powerup_id == "bomba":
        ocultas = letras_ocultas_bomba(p)
        er.letras_ocultas = er.letras_ocultas | ocultas
    elif powerup_id == "comodin":
        er.letras_ocultas = er.letras_ocultas | letras_ocultas_comodin(p)
    elif powerup_id == "descarte_inteligente":
        er.letras_ocultas = letras_ocultas_descarte_inteligente(p)
    elif powerup_id == "tiempo_extra":
        er.tiempo_extra_seg += 20
    elif powerup_id == "tiempo_lento":
        er.factor_velocidad_tiempo = 0.5
    elif powerup_id == "escudo":
        er.escudo_activo = True
    elif powerup_id == "sello_purga":
        if er.maldicion is None:
            er.agregar_powerup(powerup_id)
            return "No hay maldición activa."
        from Comun.maldiciones_partida import limpiar_efectos_maldicion_resistencia

        er.maldicion = None
        limpiar_efectos_maldicion_resistencia(er)
    elif powerup_id == "segunda_oportunidad":
        er.segunda_oportunidad_activa = True
    elif powerup_id == "doble_o_nada":
        er.doble_o_nada_activo = True
    elif powerup_id == "racha_congelada":
        er.skip_sin_cortar_racha += 1
    elif powerup_id not in {"skip", "cambio"}:
        er.agregar_powerup(powerup_id)
        return f"Objeto desconocido: {powerup_id}"
    return None


def usar_powerup(
    powerup_id: str,
    er: EstadoResistencia,
    p: Pregunta,
) -> str | None:
    """Consume un powerup almacenable; devuelve mensaje de error o None si OK."""
    from Comun.maldiciones_partida import objetos_bloqueados_efectivo_resistencia

    if objetos_bloqueados_efectivo_resistencia(er):
        return "Maldición activa: no puedes usar objetos."
    err_uso = puede_usar_powerup_en_pregunta(powerup_id, er.powerups_usados_en_pregunta)
    if err_uso:
        return err_uso
    if not er.consumir_powerup(powerup_id):
        return "No tienes ese objeto."
    err_efecto = _aplicar_efecto_powerup_uso(powerup_id, er, p)
    if err_efecto:
        return err_efecto
    from Comun.objetos_partida import POWERUPS_MULTI_USO_PREGUNTA

    if powerup_id not in POWERUPS_MULTI_USO_PREGUNTA:
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
    mult_maldicion: float = 1.0,
) -> None:
    """Aplica multiplicadores de escalada, racha, apuesta, maldición y pregunta exclusiva."""
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
    if mult_maldicion < 1.0:
        estado.puntos_arcade, aplicado = sumar_puntos_arcade(
            estado.puntos_arcade, int(delta * (mult_maldicion - 1.0))
        )
        del aplicado
    if extra > 0:
        estado.puntos_arcade, _ = sumar_puntos_arcade(estado.puntos_arcade, int(extra))


def _aplicar_recompensa_apuesta_exito(
    estado: EstadoPartida,
    er: EstadoResistencia,
) -> list[str]:
    if not er.apuesta_activa:
        return []
    recompensa = er.apuesta_activa.recompensa
    avisos: list[str] = []
    if recompensa.delta_vidas and (
        estado.vidas_restantes is not None
        and estado.vidas_restantes < er.vidas_max
    ):
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
        avisos.append(f"Recompensa de apuesta: {nom}")
    elif recompensa.powerup_aleatorio:
        from Comun.objetos_partida import POWERUPS_LOOT_APUESTA

        rng = rng_partida(er)
        pid = elegir_powerup_loot(
            er.inventario, rng, pool=POWERUPS_LOOT_APUESTA
        )
        er.agregar_powerup(pid, 1)
        avisos.append(f"Recompensa de apuesta: {etiqueta_powerup(pid)}")
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
        from Comun.economia_partida import puntos_penalizacion_escalados

        penal = puntos_penalizacion_escalados(coste.puntos_perdidos, numero_pregunta)
        estado.puntos_arcade, aplicado = sumar_puntos_arcade(
            estado.puntos_arcade, -penal
        )
        if aplicado < 0:
            avisos.append(f"Apuesta: {aplicado} puntos")
    if coste.pierde_todos_objetos and er.inventario:
        er.inventario.clear()
        avisos.append("Apuesta: pierdes todos los objetos")
    elif coste.pierde_powerup_aleatorio and er.inventario:
        rng = rng_partida(er)
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

    if fallo and er.segunda_oportunidad_activa:
        er.segunda_oportunidad_activa = False
        solucion = None
        if estado.reglas.mostrar_solucion_tras_fallo:
            from Comun.motor_nucleo import texto_solucion

            solucion = texto_solucion(p)
        return ResultadoTurnoResistencia(
            feedback=FeedbackRespuesta(
                mensaje="Segunda oportunidad: inténtalo otra vez.",
                solucion=solucion,
            ),
            reintentar_pregunta=True,
        )

    from Comun.maldiciones_partida import maldicion_es_fatal, mensaje_fallo_maldicion_fatal

    if fallo and maldicion_es_fatal(er.maldicion):
        feedback = evaluar_respuesta(p, estado, resultado)
        if estado.vidas_restantes is not None:
            estado.vidas_restantes = 0
        feedback = replace(
            feedback,
            sin_vidas=True,
            mensaje=f"{feedback.mensaje}{mensaje_fallo_maldicion_fatal()}",
        )
        avisos_fatal = list(
            procesar_post_turno_resistencia(
                er, acierto=False, numero_pregunta=indice_pregunta
            )
        )
        return ResultadoTurnoResistencia(
            feedback=feedback,
            avisos_extra=tuple(avisos_fatal),
        )

    feedback = evaluar_respuesta(p, estado, resultado)

    puntos_prev = estado.puntos_arcade
    doble_o_nada = er.doble_o_nada_activo
    if doble_o_nada:
        er.doble_o_nada_activo = False

    if acierto and doble_o_nada:
        delta = estado.puntos_arcade - puntos_prev
        if delta > 0:
            estado.puntos_arcade, _ = sumar_puntos_arcade(
                estado.puntos_arcade, delta
            )

    if fallo and doble_o_nada and estado.vidas_restantes is not None:
        estado.vidas_restantes = max(0, estado.vidas_restantes - 1)

    if acierto and er.bonus_proximo_acierto:
        bonus = er.bonus_proximo_acierto
        estado.puntos_arcade, _ = sumar_puntos_arcade(estado.puntos_arcade, bonus)
        er.bonus_proximo_acierto = 0

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
    familias_recompensa: set[str] = set()
    if acierto:
        er.registrar_acierto()
        for aviso in _aplicar_recompensa_apuesta_exito(estado, er):
            avisos_post.append(aviso)
            if "vida" in aviso.lower():
                familias_recompensa.add("vida")
        for recompensa in tirar_recompensas_tras_acierto(
            er,
            estado,
            numero_pregunta=indice_pregunta,
            familias_otorgadas=familias_recompensa,
        ):
            aplicar_recompensa(estado, er, recompensa)
            avisos_post.append(
                formatear_aviso_recompensa(
                    recompensa.etiqueta,
                    bonus_proximo_acierto=recompensa.bonus_proximo_acierto,
                )
            )
        if er.pregunta_final_jefe:
            er.pregunta_final_jefe = False
            candidatas = recompensas_completar_jefe_resistencia(
                er, estado, numero_pregunta=indice_pregunta
            )
            otorgadas: list[EventoRecompensaResistencia] = []
            for recompensa in candidatas:
                if _otorgar_recompensa_resistencia(
                    estado, er, recompensa, familias_recompensa
                ):
                    otorgadas.append(recompensa)
            if otorgadas:
                avisos_post.append(formatear_aviso_botin_jefe_resistencia(otorgadas))
    elif fallo:
        er.registrar_fallo()
        if er.pregunta_final_jefe:
            er.pregunta_final_jefe = False

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
    "BloqueFiltroActivo",
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
    "formatear_aviso_bloque",
    "formatear_aviso_evento",
    "formatear_aviso_jefe",
    "formatear_aviso_botin_jefe_resistencia",
    "formatear_aviso_maldicion",
    "formatear_aviso_presion_racha",
    "formatear_aviso_recompensa",
    "intensidad_presion_racha",
    "letras_ocultas_bomba",
    "letras_ocultas_fifty_fifty",
    "letras_ocultas_niebla",
    "letras_ocultas_por_cantidad",
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
    "texto_progreso_resistencia",
    "segmento_bloque_filtro_barra",
    "texto_bloque_filtro_extra",
    "texto_segmento_desafio_bloque",
    "tiempo_pregunta_efectivo",
    "tirar_recompensas_tras_acierto",
    "usar_powerup",
]
