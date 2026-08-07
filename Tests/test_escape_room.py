#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas del modo escape room."""

from __future__ import annotations

import unittest
from dataclasses import replace

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.semillas import RngPartida  # noqa: E402
from Comun.escape_partida import (  # noqa: E402
    BonificacionCompletarEscape,
    aplicar_bonificacion_completar,
    asegurar_puerta_viable,
    bonificacion_completar_escape,
    combinar_criterios_seleccion_pool,
    construir_pool_escape,
    criterios_pool_puerta,
    filtro_contenido_evento,
    filtro_pool_escalada,
    materias_del_pool,
    materias_viables_sala,
    puerta_es_jefe,
    reglas_juego_desafio,
    reglas_partida_desde_desafio,
    seleccionar_preguntas_desafio,
)
from Comun.reglas import preset_escape  # noqa: E402
from Comun.escape_room import (  # noqa: E402
    PUERTAS_POR_SALA,
    SALAS_DEFECTO,
    PuertaEscape,
    config_escape_room,
    es_preset_escape_room,
    generar_puertas_sala,
    total_preguntas_escape,
)
from Comun.eventos_partida import (  # noqa: E402
    EventoContenidoInstanciado,
    ModificadoresPuerta,
    PityPuertasEspecialesEscape,
    RolEscape,
    SALAS_HARD_PITY_DESCANSO_ESCAPE,
    SALAS_HARD_PITY_TIENDA_ESCAPE,
    SALAS_HARD_PITY_BOTIN_ESCAPE,
    actualizar_pity_tras_sala,
    combinar_modificadores_puerta,
    debe_garantizar_botin_escape,
    debe_garantizar_descanso_escape,
    debe_garantizar_tienda_escape,
    elegir_botin_para_sala,
    evento_por_id,
    eventos_contenido_escape_para_sala,
    eventos_puerta_escape_para_sala,
    generar_modificadores_puerta,
    instanciar_evento_contenido,
    prob_puerta_especial_con_pity,
    RASGOS_BOTIN_ESCAPE,
    RASGOS_BOTIN_POWERUP_ESCAPE,
    RASGOS_MALDICION_ESCAPE,
    SALA_MIN_MALDICION_ESCAPE,
    SALAS_HARD_PITY_MALDICION_ESCAPE,
    debe_garantizar_maldicion_escape,
)
from Comun.presets_historia import aplicar_preset, buscar_preset  # noqa: E402
from Comun.motor_nucleo import EstadoPartida  # noqa: E402
from Comun.reglas import ContextoPartida  # noqa: E402
from Comun.rutas import PATH_PREGUNTAS, resolver_listado_materias  # noqa: E402


def _rng(semilla: int) -> RngPartida:
    """Generador reproducible alineado con ``RngPartida`` del juego."""
    return RngPartida.desde_semilla(semilla)


class TestEscapeRoom(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = config_escape_room()
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.pool = construir_pool_escape(
            cargar_preguntas(PATH_PREGUNTAS, cls.materias_meta)
        )
        cls.materias_pool = materias_del_pool(cls.pool)
        cls.preset = buscar_preset("escape_room")

    def test_catalogo_comun_separa_roles(self) -> None:
        puerta_ids = {e.id for e in eventos_puerta_escape_para_sala(30)}
        contenido_ids = {e.id for e in eventos_contenido_escape_para_sala(30)}
        self.assertIn("cronometro_pregunta", puerta_ids)
        self.assertIn("descanso", puerta_ids)
        self.assertIn("tienda", puerta_ids)
        self.assertIn("puerta_materia", contenido_ids)
        self.assertIn("puerta_grupo", contenido_ids)
        self.assertIn("puerta_curso", contenido_ids)
        self.assertIn("puerta_semestre", contenido_ids)
        self.assertIn("puerta_periodo", contenido_ids)
        self.assertNotIn("relampago", puerta_ids)
        self.assertNotIn("relampago", contenido_ids)
        self.assertNotIn("puerta_materia", puerta_ids)
        self.assertIsNone(evento_por_id("relampago").rol_escape)
        self.assertIsNotNone(evento_por_id("puerta_materia").rol_escape)

    def test_config_tiene_30_salas(self) -> None:
        self.assertEqual(self.config.n_salas, SALAS_DEFECTO)
        self.assertEqual(len(self.config.salas), 30)
        self.assertEqual(self.config.puertas_por_sala, PUERTAS_POR_SALA)

    def test_generar_tres_puertas_distintas(self) -> None:
        sala = self.config.salas[0]
        puertas, _ = generar_puertas_sala(
            sala,
            0,
            materias_pool=self.materias_pool,
            pool_preguntas=self.pool,
            rng=_rng(42),
            n_salas=self.config.n_salas,
        )
        self.assertEqual(len(puertas), 3)
        from Comun.escape_room import firma_puerta_escape

        firmas = [firma_puerta_escape(p) for p in puertas]
        self.assertEqual(len(firmas), len(set(firmas)))
        con_preguntas = [p for p in puertas if not p.modificadores.sin_pregunta]
        self.assertGreaterEqual(len(con_preguntas), 2)
        firmas_contenido = [firma_puerta_escape(p) for p in con_preguntas]
        self.assertEqual(len(firmas_contenido), len(set(firmas_contenido)))
        materias = {p.evento.materia for p in con_preguntas if p.evento.materia}
        self.assertEqual(len(materias), len(con_preguntas))

    def test_salas_distintas_con_misma_semilla_base(self) -> None:
        firmas: set[tuple] = set()
        rng = _rng(99)
        for idx in range(5):
            puertas, _ = generar_puertas_sala(
                self.config.salas[idx],
                idx,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                rng=rng,
                n_salas=self.config.n_salas,
            )
            firma = tuple(
                (p.evento.id, p.n_preguntas, p.modificadores.rasgos, p.evento.materia)
                for p in puertas
            )
            firmas.add(firma)
        self.assertGreaterEqual(len(firmas), 4)

    def test_puertas_distintas_en_cada_sala(self) -> None:
        from Comun.escape_room import firma_puerta_escape

        for idx in range(self.config.n_salas):
            for semilla in (42, 99, 7, 1234):
                puertas, _ = generar_puertas_sala(
                    self.config.salas[idx],
                    idx,
                    materias_pool=self.materias_pool,
                    pool_preguntas=self.pool,
                    rng=_rng(semilla),
                    n_salas=self.config.n_salas,
                )
                firmas = [firma_puerta_escape(p) for p in puertas]
                self.assertEqual(
                    len(firmas),
                    len(set(firmas)),
                    msg=f"sala={idx + 1} semilla={semilla} firmas={firmas}",
                )

    def test_cinco_tipos_principales_puerta(self) -> None:
        from Comun.eventos_partida import plantilla_lleva_perfil_materia, tipo_filtro_evento
        from Comun.escape_room import tipo_puerta_principal_escape
        from Comun.filtros_bloque import TipoPuertaPrincipalEscape, familia_puerta_contenido_escape

        ids = {e.id for e in eventos_contenido_escape_para_sala(1)}
        self.assertEqual(ids, {"puerta_materia"})
        ids_s6 = {e.id for e in eventos_contenido_escape_para_sala(6)}
        self.assertEqual(ids_s6, {"puerta_materia", "puerta_grupo"})
        ids_s14 = {e.id for e in eventos_contenido_escape_para_sala(14)}
        self.assertNotIn("puerta_tipo_teoria", ids_s14)
        self.assertNotIn("puerta_tipo_calculo", ids_s14)

        evento_materia = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia=self.materias_pool[0],
            perfil_id="facil",
        )
        self.assertEqual(
            familia_puerta_contenido_escape(tipo_filtro_evento(evento_materia)),
            TipoPuertaPrincipalEscape.MATERIA,
        )
        evento_bloque = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_curso"),
            curso="1",
        )
        self.assertEqual(
            familia_puerta_contenido_escape(tipo_filtro_evento(evento_bloque)),
            TipoPuertaPrincipalEscape.BLOQUE,
        )
        self.assertTrue(plantilla_lleva_perfil_materia(evento_por_id("puerta_materia")))
        self.assertFalse(plantilla_lleva_perfil_materia(evento_por_id("puerta_grupo")))

        reposo = PuertaEscape(
            indice=0,
            n_preguntas=0,
            modificadores=combinar_modificadores_puerta((evento_por_id("descanso"),)),
            evento=EventoContenidoInstanciado(
                definicion=evento_por_id("puerta_materia"),
                materia=self.materias_pool[0],
            ),
        )
        self.assertEqual(tipo_puerta_principal_escape(reposo), TipoPuertaPrincipalEscape.REPOSO)
        self.assertEqual(evento_por_id("descanso").nombre, "Reposo")

    def test_emoji_barra_coincide_con_iconos_contenido(self) -> None:
        from Comun.eventos_partida import emoji_tipo_puerta_escape, iconos_contenido_puerta

        casos = [
            EventoContenidoInstanciado(
                definicion=evento_por_id("solo_facil"),
                materia=self.materias_pool[0],
                perfil_id="facil",
            ),
            EventoContenidoInstanciado(
                definicion=evento_por_id("puerta_grupo"),
                grupo=next(p.grupo for p in self.pool if p.grupo),
            ),
            EventoContenidoInstanciado(
                definicion=evento_por_id("solo_teoria"),
                materia=self.materias_pool[0],
                perfil_id="teoria",
            ),
        ]
        for evento in casos:
            esperado = "".join(ic.emoji for ic in iconos_contenido_puerta(evento))
            self.assertEqual(emoji_tipo_puerta_escape(evento), esperado, msg=evento.id)

    def test_rasgos_tiempo_puerta_escape(self) -> None:
        from Comun.eventos_partida import (
            RASGOS_TIEMPO_PUERTA_ESCAPE,
            eventos_puerta_escape_para_sala,
            params_tiempo_escape,
        )

        ids_sala_30 = {e.id for e in eventos_puerta_escape_para_sala(30)}
        self.assertLessEqual(RASGOS_TIEMPO_PUERTA_ESCAPE, ids_sala_30)
        for eid in RASGOS_TIEMPO_PUERTA_ESCAPE:
            ev = evento_por_id(eid)
            self.assertEqual(ev.rol_escape, RolEscape.PUERTA)
            p = params_tiempo_escape(eid, 20)
            self.assertTrue(
                p.tiempo_pregunta_seg is not None or p.tiempo_puerta_seg is not None,
                msg=eid,
            )
        ids_sala_3 = {e.id for e in eventos_puerta_escape_para_sala(3)}
        self.assertNotIn("cronometro_pregunta", ids_sala_3)

    def test_rasgos_niebla_solo_salas_avanzadas(self) -> None:
        from Comun.eventos_partida import (
            RASGOS_NIEBLA,
            eventos_puerta_escape_para_sala,
        )

        ids_temprano = {e.id for e in eventos_puerta_escape_para_sala(17)}
        self.assertFalse(RASGOS_NIEBLA & ids_temprano)
        ids_sala_18 = {e.id for e in eventos_puerta_escape_para_sala(18)}
        self.assertIn("niebla_opciones", ids_sala_18)
        self.assertEqual(RASGOS_NIEBLA, frozenset({"niebla_opciones"}))

    def test_rasgos_puerta_desde_catalogo_comun(self) -> None:
        cronometro = evento_por_id("cronometro_pregunta")
        niebla = evento_por_id("niebla_opciones")
        self.assertEqual(cronometro.rol_escape, RolEscape.PUERTA)
        mods = combinar_modificadores_puerta((cronometro, niebla), numero_sala=18)
        self.assertEqual(mods.tiempo_pregunta_seg, 28)
        self.assertEqual(mods.opciones_ocultas, 1)

    def test_generar_puerta_rasgos_exclusivos_no_se_combinan(self) -> None:
        from Comun.eventos_partida import (
            RASGOS_MULTIPLICADOR_PUERTA_ESCAPE,
            RASGOS_NIEBLA_PUERTA_ESCAPE,
            RASGOS_TIEMPO_PUERTA_ESCAPE,
            generar_modificadores_puerta,
        )

        familias = (
            RASGOS_TIEMPO_PUERTA_ESCAPE,
            RASGOS_MULTIPLICADOR_PUERTA_ESCAPE,
            RASGOS_NIEBLA_PUERTA_ESCAPE,
        )
        for sala in range(5, 31):
            for semilla in range(200):
                for indice in range(3):
                    mods = generar_modificadores_puerta(
                        numero_sala=sala,
                        rng=_rng(semilla),
                    )
                    ids = set(mods.eventos_ids)
                    for familia in familias:
                        self.assertLessEqual(
                            len(ids & familia),
                            1,
                            msg=f"sala={sala} semilla={semilla} indice={indice} ids={mods.eventos_ids}",
                        )

    def test_combinar_rasgos_exclusivos_conserva_el_primero(self) -> None:
        mods = combinar_modificadores_puerta(
            (
                evento_por_id("doble_puntos"),
                evento_por_id("triple_puntos"),
            )
        )
        self.assertEqual(mods.eventos_ids, ("doble_puntos",))

        mods = combinar_modificadores_puerta(
            (
                evento_por_id("cronometro_pregunta"),
                evento_por_id("cronometro_bloque"),
            )
        )
        self.assertEqual(mods.eventos_ids, ("cronometro_pregunta",))

    def test_combinar_rasgos_compatibles_en_familias_distintas(self) -> None:
        mods = combinar_modificadores_puerta(
            (
                evento_por_id("cronometro_pregunta"),
                evento_por_id("niebla_opciones"),
                evento_por_id("doble_puntos"),
            )
        )
        self.assertEqual(
            set(mods.eventos_ids),
            {"cronometro_pregunta", "niebla_opciones", "doble_puntos"},
        )

    def test_rasgos_puerta_mas_frecuentes_en_salas_altas(self) -> None:
        from Comun.eventos_partida import generar_modificadores_puerta

        clasicas = sum(
            1
            for i in range(30)
            if generar_modificadores_puerta(
                numero_sala=25, rng=_rng(7)
            ).rasgos == ("Clásica",)
        )
        self.assertLess(clasicas, 20)

    def test_iconos_efecto_puerta_orden_y_tooltips(self) -> None:
        from Comun.emojis_escape import EMOJI_DIF_FACIL
        from Comun.eventos_partida import (
            EMOJI_NIEBLA_OPCIONES,
            iconos_efecto_puerta,
        )

        materia = self.materias_pool[0]
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia=materia,
            perfil_id="facil",
        )
        mods = combinar_modificadores_puerta(
            (evento_por_id("cronometro_pregunta"), evento_por_id("niebla_opciones")),
            numero_sala=18,
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=4,
            rng=_rng(0),
        )
        self.assertEqual(len(iconos), 3)
        self.assertEqual(iconos[0].emoji, "⏱️")
        self.assertEqual(iconos[1].emoji, EMOJI_NIEBLA_OPCIONES)
        self.assertEqual(iconos[2].emoji, EMOJI_DIF_FACIL)
        self.assertIn("28 s", iconos[0].tooltip)
        self.assertIn("al azar", iconos[1].tooltip.lower())
        self.assertIn("fáciles", iconos[2].tooltip)

    def test_icono_bloque_puerta_tres_o_cinco(self) -> None:
        from Comun.emojis_escape import (
            EMOJI_BLOQUE_PUERTA,
            EMOJI_BLOQUE_SUBTIPO_GRUPO,
            EMOJI_JEFE,
            CapaIconoEscape,
        )
        from Comun.eventos_partida import iconos_efecto_puerta

        materia = self.materias_pool[0]
        evento_materia = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia=materia,
            perfil_id="facil",
        )
        mods = combinar_modificadores_puerta((), numero_sala=5)
        iconos_materia = iconos_efecto_puerta(
            evento=evento_materia,
            modificadores=mods,
            n_preguntas=3,
            rng=_rng(1),
        )
        self.assertEqual(
            [ic.emoji for ic in iconos_materia if ic.capa == CapaIconoEscape.BLOQUE],
            [],
        )

        grupo = next(p.grupo for p in self.pool if p.grupo)
        evento_grupo = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_grupo"),
            grupo=grupo,
            perfil_id="facil",
        )
        iconos_grupo = iconos_efecto_puerta(
            evento=evento_grupo,
            modificadores=mods,
            n_preguntas=3,
            rng=_rng(1),
        )
        self.assertEqual(
            [ic.emoji for ic in iconos_grupo if ic.capa == CapaIconoEscape.BLOQUE],
            [],
        )
        self.assertEqual(
            [ic.emoji for ic in iconos_grupo if ic.capa == CapaIconoEscape.TIPO_PUERTA],
            [EMOJI_BLOQUE_SUBTIPO_GRUPO],
        )

        iconos_jefe = iconos_efecto_puerta(
            evento=evento_grupo,
            modificadores=mods,
            n_preguntas=10,
            rng=_rng(2),
        )
        self.assertEqual(
            [ic.emoji for ic in iconos_jefe if ic.capa == CapaIconoEscape.BLOQUE],
            [],
        )
        self.assertIn(EMOJI_JEFE, [ic.emoji for ic in iconos_jefe])
        corona = next(ic for ic in iconos_jefe if ic.emoji == EMOJI_JEFE)
        self.assertIn("10 preguntas", corona.tooltip)

    def test_icono_bloque_puerta_curso(self) -> None:
        from Comun.emojis_escape import (
            EMOJI_BLOQUE_PUERTA,
            EMOJI_PUERTA_CURSO,
            CapaIconoEscape,
        )
        from Comun.eventos_partida import TOOLTIP_PUERTA_CURSO, iconos_efecto_puerta

        curso = next(p.curso for p in self.pool if p.curso)
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_curso"),
            curso=curso,
        )
        mods = combinar_modificadores_puerta((), numero_sala=12)
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=5,
            rng=_rng(3),
        )
        emojis = [ic.emoji for ic in iconos]
        self.assertNotIn(EMOJI_BLOQUE_PUERTA, emojis)
        self.assertIn(EMOJI_PUERTA_CURSO, emojis)
        curso_ic = next(ic for ic in iconos if ic.capa == CapaIconoEscape.TIPO_PUERTA)
        self.assertEqual(curso_ic.tooltip, TOOLTIP_PUERTA_CURSO)
        self.assertNotIn(curso, curso_ic.tooltip)

    def test_iconos_efecto_puerta_maximo_cinco(self) -> None:
        from Comun.emojis_escape import CapaIconoEscape
        from Comun.eventos_partida import EMOJI_BOTIN_ESCAPE, iconos_efecto_puerta

        materia = self.materias_pool[0]
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_teoria"),
            materia=materia,
            perfil_id="teoria",
        )
        mods = combinar_modificadores_puerta(
            (
                evento_por_id("cronometro_pregunta"),
                evento_por_id("niebla_opciones"),
                evento_por_id("botin"),
            )
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=4,
            rng=_rng(42),
        )
        self.assertLessEqual(len(iconos), 5)
        self.assertEqual(len(iconos), 5)
        capas = {ic.capa for ic in iconos}
        self.assertIn(CapaIconoEscape.DIFICULTAD, capas)
        self.assertIn(CapaIconoEscape.TIPO_PREGUNTA, capas)
        self.assertIn(CapaIconoEscape.BOTIN, capas)
        self.assertEqual(iconos[-1].capa, CapaIconoEscape.BOTIN)
        self.assertEqual(iconos[-1].emoji, EMOJI_BOTIN_ESCAPE)

    def test_iconos_protegidos_permanecen_al_recortar(self) -> None:
        from Comun.emojis_escape import CAPAS_ICONO_PROTEGIDO_ESCAPE, CapaIconoEscape
        from Comun.eventos_partida import iconos_efecto_puerta

        materia = self.materias_pool[0]
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_teoria"),
            materia=materia,
            perfil_id="teoria",
        )
        mods = combinar_modificadores_puerta(
            (
                evento_por_id("cronometro_pregunta"),
                evento_por_id("niebla_opciones"),
                evento_por_id("doble_puntos"),
                evento_por_id("botin"),
            )
        )
        for semilla in range(30):
            iconos = iconos_efecto_puerta(
                evento=evento,
                modificadores=mods,
                n_preguntas=4,
                rng=_rng(semilla),
            )
            self.assertLessEqual(len(iconos), 5, msg=f"semilla={semilla}")
            for capa in (
                CapaIconoEscape.DIFICULTAD,
                CapaIconoEscape.BOTIN,
            ):
                self.assertIn(capa, {ic.capa for ic in iconos}, msg=f"semilla={semilla}")
            self.assertTrue(
                all(ic.capa in CAPAS_ICONO_PROTEGIDO_ESCAPE or len(iconos) <= 5 for ic in iconos)
            )

    def test_recorte_iconos_quita_tipo_pregunta_antes_que_rasgos(self) -> None:
        from Comun.emojis_escape import CapaIconoEscape
        from Comun.eventos_partida import iconos_efecto_puerta

        materia = self.materias_pool[0]
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_teoria"),
            materia=materia,
            perfil_id="teoria",
        )
        mods = combinar_modificadores_puerta(
            (
                evento_por_id("cronometro_pregunta"),
                evento_por_id("niebla_opciones"),
                evento_por_id("doble_puntos"),
                evento_por_id("botin"),
            )
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=4,
            rng=_rng(1),
        )
        self.assertEqual(len(iconos), 5)
        self.assertNotIn(CapaIconoEscape.TIPO_PREGUNTA, {ic.capa for ic in iconos})
        self.assertIn(CapaIconoEscape.TIEMPO, {ic.capa for ic in iconos})
        self.assertIn(CapaIconoEscape.NIEBLA, {ic.capa for ic in iconos})

    def test_iconos_capas_contenido_puerta(self) -> None:
        from Comun.emojis_escape import (
            EMOJI_DIF_BALANCEADO,
            EMOJI_DIF_FACIL,
            EMOJI_MIX_MATERIA,
            EMOJI_PUERTA_GRUPO,
            EMOJI_TIPO_CALCULO,
            EMOJI_TIPO_TEORIA,
        )
        from Comun.eventos_partida import (
            TOOLTIP_MIX_MATERIA,
            iconos_contenido_puerta,
        )

        materia = self.materias_pool[0]

        def iconos(ev_id: str, *, perfil_id: str | None = None):
            return iconos_contenido_puerta(
                EventoContenidoInstanciado(
                    definicion=evento_por_id(ev_id),
                    materia=materia,
                    perfil_id=perfil_id,
                )
            )

        facil = iconos("solo_facil", perfil_id="facil")
        self.assertEqual([i.emoji for i in facil], [EMOJI_DIF_FACIL])
        self.assertIn("fáciles", facil[0].tooltip)

        balanceado = iconos("pregunta_unica", perfil_id="balanceado")
        self.assertEqual(balanceado[0].emoji, EMOJI_DIF_BALANCEADO)

        mix = iconos("mix_facil_media", perfil_id="mix_facil_media")
        self.assertEqual(mix[0].emoji, EMOJI_MIX_MATERIA)
        self.assertEqual(mix[0].tooltip, TOOLTIP_MIX_MATERIA)

        teoria = iconos("solo_teoria", perfil_id="teoria")
        self.assertEqual(
            [i.emoji for i in teoria],
            [EMOJI_DIF_BALANCEADO, EMOJI_TIPO_TEORIA],
        )

        calculo = iconos("solo_calculo", perfil_id="calculo")
        self.assertEqual(calculo[-1].emoji, EMOJI_TIPO_CALCULO)

        grupo = iconos("bloque_grupo", perfil_id="facil")
        self.assertEqual([i.emoji for i in grupo], [EMOJI_PUERTA_GRUPO])

    def test_plantilla_grupo_sin_perfil_materia(self) -> None:
        from Comun.eventos_partida import elegir_plantillas_contenido_escape
        import random

        rng = _rng(42)
        plantillas = elegir_plantillas_contenido_escape(3, numero_sala=20, rng=rng)
        grupos = [(p, pid) for p, pid in plantillas if p.id == "puerta_grupo"]
        self.assertTrue(grupos)
        for plantilla, perfil_id in grupos:
            self.assertIsNone(perfil_id)
            self.assertIsNone(plantilla.modificadores.dificultades_permitidas)
            opts = plantilla.contenido_escape
            self.assertIsNotNone(opts)
            self.assertIsNone(opts.tipos_permitidos)

    def test_seleccion_preguntas_desafio(self) -> None:
        viables = materias_viables_sala(
            self.pool, self.materias_pool, numero_sala=1, n_salas=30
        )
        materia = viables[0]
        evento = instanciar_evento_contenido(
            evento_por_id("pregunta_unica"),
            materias_pool=(materia,),
            grupos_pool=(),
            rng=_rng(1),
            indice_puerta=0,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        lote = seleccionar_preguntas_desafio(
            self.pool, puerta, numero_sala=1, n_salas=30, rng=_rng(42)
        )
        self.assertEqual(len(lote), 3)
        self.assertEqual(lote[0].materia, materia)

    def test_seleccion_balanceado_cubre_todas_las_dificultades(self) -> None:
        from Comun.modelos import Pregunta

        materia = "MateriaBalanceoTest"
        pool: list[Pregunta] = []
        for dif in ("Facil", "Media", "Dificil"):
            for k in range(4):
                pool.append(
                    Pregunta(
                        texto=f"{dif}-{k}",
                        materia=materia,
                        tematica="t",
                        dificultad=dif,
                        tipo="Teoria",
                        grupo="1",
                        nivel="1",
                        curso="1",
                        semestre="1",
                        opciones={"A": "a"},
                        correcta="A",
                    )
                )
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=materia,
            perfil_id="balanceado",
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        for semilla in range(20):
            lote = seleccionar_preguntas_desafio(
                pool, puerta, numero_sala=1, n_salas=30, rng=_rng(semilla)
            )
            self.assertEqual(len(lote), 3)
            self.assertEqual(
                {p.dificultad for p in lote},
                {"Facil", "Media", "Dificil"},
                msg=f"semilla={semilla}",
            )

    def test_seleccion_mix_cubre_dificultades_del_perfil(self) -> None:
        from Comun.modelos import Pregunta

        materia = "MateriaMixTest"
        pool: list[Pregunta] = []
        for dif in ("Facil", "Media"):
            for k in range(4):
                pool.append(
                    Pregunta(
                        texto=f"{dif}-{k}",
                        materia=materia,
                        tematica="t",
                        dificultad=dif,
                        tipo="Teoria",
                        grupo="1",
                        nivel="1",
                        curso="1",
                        semestre="1",
                        opciones={"A": "a"},
                        correcta="A",
                    )
                )
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("mix_facil_media"),
            materia=materia,
            perfil_id="mix_facil_media",
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        for semilla in range(20):
            lote = seleccionar_preguntas_desafio(
                pool, puerta, numero_sala=1, n_salas=30, rng=_rng(semilla)
            )
            self.assertEqual(len(lote), 3)
            self.assertEqual(
                {p.dificultad for p in lote},
                {"Facil", "Media"},
                msg=f"semilla={semilla}",
            )
            orden = [p.dificultad for p in lote]
            self.assertEqual(orden, sorted(orden, key={"Facil": 0, "Media": 1}.get))

    def test_seleccion_materia_tardia_en_sala_1(self) -> None:
        materia = "Informació Quàntica"
        if materia not in self.materias_pool:
            self.skipTest(f"{materia!r} no está en el pool de pruebas")
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=materia,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        lote = seleccionar_preguntas_desafio(
            self.pool, puerta, numero_sala=15, n_salas=30, rng=_rng(7)
        )
        self.assertEqual(len(lote), 3)
        self.assertTrue(all(p.materia == materia for p in lote))

    def test_escalada_complejidad_por_fases(self) -> None:
        f1 = filtro_pool_escalada(1, n_salas=30, pool=self.pool)
        f15 = filtro_pool_escalada(15, n_salas=30, pool=self.pool)
        f30 = filtro_pool_escalada(30, n_salas=30, pool=self.pool)
        self.assertEqual(f1.min_complejidad, f1.max_complejidad)
        self.assertLess(f15.min_complejidad, f15.max_complejidad)
        self.assertGreater(f30.min_complejidad, f1.min_complejidad)

    def test_generar_puertas_son_viables(self) -> None:
        puertas, _ = generar_puertas_sala(
            self.config.salas[0],
            0,
            materias_pool=self.materias_pool,
            pool_preguntas=self.pool,
            rng=_rng(42),
            n_salas=self.config.n_salas,
        )
        for puerta in puertas:
            if puerta.modificadores.sin_pregunta:
                continue
            lote = seleccionar_preguntas_desafio(
                self.pool,
                puerta,
                numero_sala=1,
                n_salas=self.config.n_salas,
                rng=_rng(99),
            )
            self.assertEqual(len(lote), puerta.n_preguntas)

    def test_puerta_grupo_usa_todas_las_materias(self) -> None:
        from Comun.escape_partida import grupos_viables_sala, materias_del_grupo

        grupos = grupos_viables_sala(
            self.pool, ("2",), numero_sala=15, n_salas=30, min_preguntas=5
        )
        if not grupos:
            self.skipTest("grupo 2 no viable en sala 15")
        grupo = grupos[0]
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("bloque_grupo"),
            grupo=grupo,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=5,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        lote = seleccionar_preguntas_desafio(
            self.pool, puerta, numero_sala=15, n_salas=30, rng=_rng(11)
        )
        self.assertEqual(len(lote), 5)
        mats_grupo = set(materias_del_grupo(self.pool, grupo))
        self.assertTrue(mats_grupo)
        self.assertTrue({p.materia for p in lote}.issubset(mats_grupo))
        if len(mats_grupo) >= 2:
            self.assertGreater(len({p.materia for p in lote}), 1)

    def test_puerta_y_evento_roles_separados(self) -> None:
        materia = self.materias_pool[0]
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia=materia,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=combinar_modificadores_puerta(
                (evento_por_id("cronometro_pregunta"),),
                numero_sala=20,
            ),
            evento=evento,
        )
        criterios = combinar_criterios_seleccion_pool(
            criterios_pool_puerta(puerta),
            filtro_pool_escalada(20, n_salas=30, pool=self.pool),
            filtro_contenido_evento(evento),
        )
        self.assertEqual(criterios.materia, materia)
        reglas = reglas_juego_desafio(puerta, numero_sala=20, n_salas=30)
        self.assertEqual(reglas.tiempo_pregunta_seg, 28)

    def test_tiempo_escape_por_defecto_sala_final(self) -> None:
        from Comun.escape_partida import (
            TIEMPO_PREGUNTA_MIN_ESCAPE,
            acotar_tiempo_pregunta_escape,
            tiempo_pregunta_escape_por_defecto,
        )
        from Comun.resistencia_partida import escalada_para_pregunta

        self.assertIsNone(tiempo_pregunta_escape_por_defecto(5, 30))
        self.assertEqual(tiempo_pregunta_escape_por_defecto(15, 30), 50)
        self.assertEqual(tiempo_pregunta_escape_por_defecto(24, 30), 35)
        self.assertEqual(
            tiempo_pregunta_escape_por_defecto(30, 30),
            TIEMPO_PREGUNTA_MIN_ESCAPE,
        )
        self.assertEqual(acotar_tiempo_pregunta_escape(12), TIEMPO_PREGUNTA_MIN_ESCAPE)
        self.assertEqual(acotar_tiempo_pregunta_escape(35), 35)
        extrema = escalada_para_pregunta(750).tiempo_pregunta_seg
        self.assertIsNotNone(extrema)
        self.assertLess(extrema, TIEMPO_PREGUNTA_MIN_ESCAPE)
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=4,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        reglas = reglas_juego_desafio(puerta, numero_sala=30, n_salas=30)
        self.assertEqual(reglas.tiempo_pregunta_seg, TIEMPO_PREGUNTA_MIN_ESCAPE)

    def test_bonificacion_puerta_normal_sin_botin(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=5,
            modificadores=combinar_modificadores_puerta(
                (evento_por_id("cronometro_pregunta"),)
            ),
            evento=evento,
        )
        self.assertEqual(bonificacion_completar_escape(puerta).delta_vidas, 0)

    def test_puntos_mult_desafio(self) -> None:
        from Comun.escape_partida import mensaje_acierto_desafio, puntos_extra_mult_desafio

        self.assertEqual(puntos_extra_mult_desafio(20, acierto=True, mult=2), 20)
        self.assertEqual(puntos_extra_mult_desafio(20, acierto=False, mult=2), 0)
        self.assertIn("×2", mensaje_acierto_desafio(20, mult=2))

    def test_reglas_juego_doble_puntos(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=combinar_modificadores_puerta((evento_por_id("doble_puntos"),)),
            evento=evento,
        )
        reglas = reglas_juego_desafio(puerta, numero_sala=10)
        self.assertEqual(reglas.multiplicador_puntos, 2)

    def test_cronometro_pregunta_explicito(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=4,
            modificadores=combinar_modificadores_puerta(
                (evento_por_id("cronometro_pregunta"),),
                numero_sala=20,
            ),
            evento=evento,
        )
        reglas = reglas_juego_desafio(puerta, numero_sala=20, n_salas=30)
        self.assertEqual(reglas.tiempo_pregunta_seg, 28)
        partida = reglas_partida_desde_desafio(preset_escape(), reglas)
        self.assertEqual(partida.tiempo_por_pregunta_seg, 28)
        self.assertIsNone(partida.tiempo_total_seg)

    def test_cronometro_doble_ambos_limites(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        mods = combinar_modificadores_puerta((evento_por_id("cronometro_doble"),))
        self.assertEqual(mods.tiempo_puerta_seg, 150)
        self.assertEqual(mods.tiempo_pregunta_seg, 28)
        puerta = PuertaEscape(indice=0, n_preguntas=6, modificadores=mods, evento=evento)
        reglas = reglas_juego_desafio(puerta, numero_sala=12, n_salas=30)
        self.assertEqual(reglas.tiempo_puerta_seg, 150)
        self.assertEqual(reglas.tiempo_pregunta_seg, 28)
        partida = reglas_partida_desde_desafio(preset_escape(), reglas)
        self.assertEqual(partida.tiempo_total_seg, 150)
        self.assertEqual(partida.tiempo_por_pregunta_seg, 28)

    def test_cronometro_bloque_solo_tiempo_puerta(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        mods = combinar_modificadores_puerta((evento_por_id("cronometro_bloque"),))
        puerta = PuertaEscape(indice=0, n_preguntas=5, modificadores=mods, evento=evento)
        reglas = reglas_juego_desafio(puerta, numero_sala=10, n_salas=30)
        self.assertEqual(reglas.tiempo_puerta_seg, 120)
        self.assertIsNone(reglas.tiempo_pregunta_seg)
        partida = reglas_partida_desde_desafio(preset_escape(), reglas)
        self.assertEqual(partida.tiempo_total_seg, 120)
        self.assertIsNone(partida.tiempo_por_pregunta_seg)

    def test_escape_sin_cronometro_global_en_preset(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=4,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        reglas = reglas_juego_desafio(puerta, numero_sala=30, n_salas=30)
        partida = reglas_partida_desde_desafio(preset_escape(), reglas)
        self.assertIsNone(partida.tiempo_total_seg)
        self.assertIsNone(aplicar_preset(self.preset, None).tiempo_total_seg)

    def test_escape_barra_cronometro_puerta_si_aplica(self) -> None:
        from Comun.linea_estado_ui import segmentos_linea_estado

        reglas = preset_escape()
        reglas = replace(reglas, tiempo_total_seg=150, tiempo_por_pregunta_seg=28)
        estado = EstadoPartida(nombre="Test", reglas=reglas, vidas_restantes=3)
        segs = segmentos_linea_estado(
            estado,
            "",
            progreso_sala="1/30",
            progreso_puerta="2/5",
            segundos_pregunta_restantes=18,
            mostrar_tiempo_activo=True,
            vidas_max=3,
        )
        ids = [s.id for s in segs]
        self.assertEqual(ids[0], "sala_escape")
        self.assertIn("pregunta_puerta", ids)
        self.assertIn("tiempo_total", ids)
        self.assertIn("tiempo_preg", ids)
        self.assertIn("tiempo_total", ids)
        self.assertIn("tiempo_preg", ids)

    def test_escape_barra_sin_cronometro_global(self) -> None:
        from Comun.linea_estado_ui import segmentos_linea_estado

        estado = EstadoPartida(
            nombre="Test",
            reglas=preset_escape(),
            vidas_restantes=3,
        )
        segs = segmentos_linea_estado(
            estado,
            "",
            progreso_sala="1/30",
            progreso_puerta="2/5",
            segundos_pregunta_restantes=18,
            mostrar_tiempo_activo=False,
            vidas_max=3,
        )
        ids = [s.id for s in segs]
        self.assertIn("sala_escape", ids)
        self.assertNotIn("progreso", ids)
        self.assertNotIn("tiempo_total", ids)
        self.assertIn("tiempo_preg", ids)
        self.assertIn("pregunta_puerta", ids)

    def test_bonificacion_puerta_jefe(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_dificil"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=10,
            modificadores=ModificadoresPuerta(),
            evento=evento,
            es_jefe=True,
        )
        self.assertTrue(puerta_es_jefe(puerta))
        bonus = bonificacion_completar_escape(puerta)
        self.assertEqual(bonus.delta_vidas, 2)

    def test_vidas_fallo_puerta_normal_y_jefe(self) -> None:
        from Comun.escape_partida import (
            aplicar_penalizacion_extra_fallo_puerta,
            vidas_perdidas_fallo_puerta,
        )

        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_materia"),
            materia=self.materias_pool[0],
        )
        normal = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        jefe = PuertaEscape(
            indice=1,
            n_preguntas=10,
            modificadores=ModificadoresPuerta(),
            evento=evento,
            es_jefe=True,
        )
        self.assertEqual(vidas_perdidas_fallo_puerta(normal), 1)
        self.assertEqual(vidas_perdidas_fallo_puerta(jefe), 2)
        estado = EstadoPartida(
            nombre="t",
            reglas=preset_escape(),
            vidas_restantes=2,
        )
        self.assertEqual(aplicar_penalizacion_extra_fallo_puerta(estado, normal), 0)
        self.assertEqual(estado.vidas_restantes, 2)
        self.assertEqual(aplicar_penalizacion_extra_fallo_puerta(estado, jefe), 1)
        self.assertEqual(estado.vidas_restantes, 1)

    def test_abandonar_puerta_si_pierdes_vida(self) -> None:
        from Comun.escape_partida import debe_abandonar_puerta_por_perdida_vida

        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_materia"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        self.assertTrue(
            debe_abandonar_puerta_por_perdida_vida(
                puerta, vidas_antes=3, vidas_despues=2, reintentar=False
            )
        )
        self.assertTrue(
            debe_abandonar_puerta_por_perdida_vida(
                PuertaEscape(
                    indice=1,
                    n_preguntas=10,
                    modificadores=ModificadoresPuerta(),
                    evento=evento,
                    es_jefe=True,
                ),
                vidas_antes=3,
                vidas_despues=1,
                reintentar=False,
            )
        )
        self.assertFalse(
            debe_abandonar_puerta_por_perdida_vida(
                puerta, vidas_antes=3, vidas_despues=2, reintentar=True
            )
        )
        descanso = PuertaEscape(
            indice=2,
            n_preguntas=0,
            modificadores=combinar_modificadores_puerta((evento_por_id("descanso"),)),
            evento=evento,
        )
        self.assertFalse(
            debe_abandonar_puerta_por_perdida_vida(
                descanso, vidas_antes=3, vidas_despues=2, reintentar=False
            )
        )

    def test_bonificacion_botin_corazon_max(self) -> None:
        from Comun.eventos_partida import iconos_efecto_puerta, lineas_botin_puerta

        mods = combinar_modificadores_puerta((evento_por_id("botin_corazon_max"),))
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=mods,
            evento=evento,
        )
        bonus = bonificacion_completar_escape(puerta)
        self.assertEqual(bonus.delta_vidas_max, 1)
        self.assertEqual(bonus.delta_vidas, 0)
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=puerta.n_preguntas,
            rng=_rng(0),
        )
        self.assertEqual(iconos[-1].emoji, "💰")
        from Comun.emojis_escape import TOOLTIP_BOTIN

        self.assertEqual(iconos[-1].tooltip, TOOLTIP_BOTIN)
        lineas = lineas_botin_puerta(mods)
        self.assertEqual(len(lineas), 1)
        self.assertTrue(lineas[0].startswith("💖 Recompensa:"))

    def test_bonificacion_botin_en_modificadores(self) -> None:
        mods = combinar_modificadores_puerta(
            (evento_por_id("cronometro_pregunta"), evento_por_id("botin"))
        )
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=5,
            modificadores=mods,
            evento=evento,
        )
        bonus = bonificacion_completar_escape(puerta)
        self.assertEqual(bonus.delta_vidas, 1)

    def test_feedback_puerta_con_botin_mensaje_unico_al_completar(self) -> None:
        """El acierto de la última pregunta y el botín deben ir en un solo feedback."""
        from Comun.escape_partida import mensaje_acierto_desafio

        mods = combinar_modificadores_puerta(
            (evento_por_id("cronometro_pregunta"), evento_por_id("botin"))
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=mods,
            evento=EventoContenidoInstanciado(
                definicion=evento_por_id("pregunta_unica"),
                materia=self.materias_pool[0],
            ),
        )
        acierto = mensaje_acierto_desafio(12, mult=1)
        bonus = bonificacion_completar_escape(puerta)
        combinado = f"{acierto} {bonus.mensaje}"
        self.assertIn("Correcto", combinado)
        self.assertIn("Botín", combinado)
        self.assertNotIn("Botín", acierto)
        self.assertNotIn("Recompensa", acierto)

    def test_combinar_descanso_solo_admite_botin(self) -> None:
        mods = combinar_modificadores_puerta(
            (
                evento_por_id("descanso"),
                evento_por_id("cronometro_pregunta"),
                evento_por_id("botin"),
            )
        )
        self.assertTrue(mods.sin_pregunta)
        self.assertEqual(set(mods.eventos_ids), {"descanso", "botin"})
        self.assertEqual(mods.rasgos, ("Reposo", "Botín"))

        mods_solo = combinar_modificadores_puerta((evento_por_id("descanso"),))
        self.assertEqual(mods_solo.eventos_ids, ("descanso",))

        mods_niebla = combinar_modificadores_puerta(
            (evento_por_id("descanso"), evento_por_id("niebla_opciones"))
        )
        self.assertEqual(mods_niebla.eventos_ids, ("descanso",))
        self.assertEqual(mods_niebla.opciones_ocultas, 0)

    def test_generar_puerta_sin_pregunta_solo_pausa_y_botin(self) -> None:
        from Comun.eventos_partida import (
            RASGOS_EXTRA_PUERTA_SIN_PREGUNTA_ESCAPE,
            RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE,
            generar_modificadores_puerta,
        )

        permitidos = RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE | RASGOS_EXTRA_PUERTA_SIN_PREGUNTA_ESCAPE
        for sala in range(1, 31):
            for semilla in range(300):
                for indice in range(3):
                    mods = generar_modificadores_puerta(
                        numero_sala=sala,
                        rng=_rng(semilla),
                    )
                    if not mods.sin_pregunta:
                        continue
                    self.assertTrue(
                        set(mods.eventos_ids) <= permitidos,
                        msg=f"ids={mods.eventos_ids} sala={sala} semilla={semilla}",
                    )
                    self.assertFalse(
                        set(mods.eventos_ids) & {
                            "niebla_opciones",
                            "cronometro_pregunta",
                            "doble_puntos",
                        },
                    )

    def test_catalogo_solo_niebla_opciones(self) -> None:
        from Comun.eventos_partida import RASGOS_NIEBLA

        self.assertEqual(RASGOS_NIEBLA, frozenset({"niebla_opciones"}))

    def test_descanso_con_botin_tooltip_y_linea(self) -> None:
        from Comun.emojis_escape import TOOLTIP_BOTIN_DESCANSO
        from Comun.eventos_partida import iconos_efecto_puerta, lineas_botin_puerta

        mods = combinar_modificadores_puerta(
            (evento_por_id("descanso"), evento_por_id("botin"))
        )
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=0,
            modificadores=mods,
            evento=evento,
        )
        iconos = iconos_efecto_puerta(
            evento=puerta.evento,
            modificadores=puerta.modificadores,
            n_preguntas=0,
            rng=_rng(0),
        )
        self.assertEqual(iconos[-1].tooltip, TOOLTIP_BOTIN_DESCANSO)
        lineas = lineas_botin_puerta(mods)
        self.assertEqual(lineas, ("❤️ Recompensa: +1 vida (tope 3)",))

    def test_descanso_con_botin_bonificacion_al_cerrar(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        mods = combinar_modificadores_puerta(
            (evento_por_id("descanso"), evento_por_id("botin"))
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=0,
            modificadores=mods,
            evento=evento,
        )
        self.assertEqual(bonificacion_completar_escape(puerta).delta_vidas, 1)

    def test_feedback_descanso_con_botin_no_repite_preview(self) -> None:
        from Comun.escape_partida import mensaje_feedback_puerta_sin_pregunta

        mods = combinar_modificadores_puerta(
            (evento_por_id("descanso"), evento_por_id("botin"))
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=0,
            modificadores=mods,
            evento=EventoContenidoInstanciado(
                definicion=evento_por_id("pregunta_unica"),
                materia=self.materias_pool[0],
            ),
        )
        msg = mensaje_feedback_puerta_sin_pregunta(puerta)
        self.assertIn("Reposo", msg)
        self.assertIn("avanzas sin preguntas", msg)
        self.assertNotIn("Recompensa", msg)
        self.assertNotIn("Botín", msg)
        bonus = bonificacion_completar_escape(puerta)
        self.assertIn("Botín", bonus.mensaje)

    def test_descanso_sin_vida_ni_bonificacion(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=0,
            modificadores=combinar_modificadores_puerta((evento_por_id("descanso"),)),
            evento=evento,
        )
        self.assertEqual(bonificacion_completar_escape(puerta).delta_vidas, 0)

    def test_descanso_sin_bonificacion_al_completar(self) -> None:
        """Alias de test_descanso_sin_vida_ni_bonificacion (compatibilidad)."""
        self.test_descanso_sin_vida_ni_bonificacion()

    def test_aplicar_bonificacion_respeta_tope(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_escape

        estado = EstadoPartida(
            nombre="t",
            reglas=preset_escape(),
            vidas_restantes=3,
        )
        ganadas, vidas_max = aplicar_bonificacion_completar(
            estado,
            BonificacionCompletarEscape(delta_vidas=2),
            vidas_max=3,
        )
        self.assertEqual(ganadas, 0)
        self.assertEqual(estado.vidas_restantes, 3)
        self.assertEqual(vidas_max, 3)

    def test_aplicar_bonificacion_corazon_max(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_escape

        estado = EstadoPartida(
            nombre="t",
            reglas=preset_escape(),
            vidas_restantes=3,
        )
        ganadas, vidas_max = aplicar_bonificacion_completar(
            estado,
            BonificacionCompletarEscape(delta_vidas_max=1),
            vidas_max=3,
        )
        self.assertEqual(ganadas, 0)
        self.assertEqual(vidas_max, 4)
        self.assertEqual(estado.vidas_restantes, 3)

        ganadas, vidas_max = aplicar_bonificacion_completar(
            estado,
            BonificacionCompletarEscape(delta_vidas=2),
            vidas_max=vidas_max,
        )
        self.assertEqual(ganadas, 1)
        self.assertEqual(estado.vidas_restantes, 4)


    def test_pool_beta_ampliado(self) -> None:
        from Comun.modelos import BancoPreguntas
        from Comun.rutas import resolver_plantillas

        pool_beta = construir_pool_escape(
            cargar_preguntas(PATH_PREGUNTAS, self.materias_meta),
            banco=BancoPreguntas.PLANTILLAS_TODO,
            path_csv=PATH_PREGUNTAS,
            path_plantillas=resolver_plantillas(),
            materias_meta=self.materias_meta,
        )
        self.assertGreater(len(pool_beta), len(self.pool))

    def test_aplicar_preset_escape_sin_config_historia(self) -> None:
        from Comun.presets_historia import aplicar_preset, cargar_presets_especiales
        from Comun.rutas import resolver_presets

        preset = next(
            p for p in cargar_presets_especiales(resolver_presets()) if p.id == "escape_room"
        )
        reglas = aplicar_preset(preset, None)
        self.assertIsNotNone(reglas.vidas)

    def test_config_salas_personalizadas(self) -> None:
        from Comun.escape_room import SALAS_MAX, SALAS_MIN, normalizar_n_salas_escape

        cfg = config_escape_room(n_salas=15)
        self.assertEqual(cfg.n_salas, 15)
        self.assertEqual(len(cfg.salas), 15)
        self.assertEqual(normalizar_n_salas_escape(47), 45)
        self.assertEqual(normalizar_n_salas_escape(3), SALAS_MIN)
        self.assertEqual(normalizar_n_salas_escape(99), SALAS_MAX)

    def test_tienda_tres_articulos_por_visita(self) -> None:
        from Comun.tienda_escape import (
            ARTICULOS_POR_VISITA_TIENDA,
            seleccionar_articulos_tienda_visita,
        )

        arts = seleccionar_articulos_tienda_visita(10, rng=_rng(42))
        self.assertEqual(len(arts), ARTICULOS_POR_VISITA_TIENDA)
        presentes = [a for a in arts if a is not None]
        self.assertEqual(len({a.articulo.id for a in presentes}), len(presentes))
        otra = seleccionar_articulos_tienda_visita(10, rng=_rng(99))
        self.assertNotEqual(
            [a.articulo.id if a else None for a in arts],
            [a.articulo.id if a else None for a in otra],
        )

    def test_tienda_visita_garantiza_articulo_asequible(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia
        from Comun.tienda_escape import seleccionar_articulos_tienda_visita

        estado = EstadoPartida(
            nombre="t",
            reglas=preset_resistencia(),
            vidas_restantes=3,
            puntos_arcade=15,
        )
        for semilla in range(80):
            arts = seleccionar_articulos_tienda_visita(
                3,
                rng=_rng(semilla),
                estado=estado,
                vidas_max=3,
            )
            asequibles = [
                a for a in arts if a is not None and a.precio_efectivo <= 15
            ]
            self.assertTrue(asequibles, msg=f"semilla={semilla}")

    def test_tienda_no_visitable_sin_puntos(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia
        from Comun.tienda_escape import (
            puede_visitar_tienda_escape,
            seleccionar_articulos_tienda_visita,
        )

        estado = EstadoPartida(
            nombre="t",
            reglas=preset_resistencia(),
            vidas_restantes=3,
            puntos_arcade=0,
        )
        self.assertFalse(puede_visitar_tienda_escape(5, estado, vidas_max=3))
        arts = seleccionar_articulos_tienda_visita(
            5, rng=_rng(1), estado=estado, vidas_max=3
        )
        self.assertEqual(arts, (None, None, None))

    def test_tienda_puerta_sustituida_si_no_hay_compras(self) -> None:
        from Comun.eventos_partida import (
            PityPuertasEspecialesEscape,
            SALAS_HARD_PITY_TIENDA_ESCAPE,
            actualizar_pity_tras_sala,
            evento_por_id,
        )
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia
        from Comun.tienda_escape import puerta_es_tienda

        sala = self.config.salas[9]
        estado = EstadoPartida(
            nombre="t",
            reglas=preset_resistencia(),
            vidas_restantes=3,
            puntos_arcade=0,
        )
        pity = PityPuertasEspecialesEscape(salas_sin_tienda=20)
        umbral = SALAS_HARD_PITY_TIENDA_ESCAPE - evento_por_id("tienda").nivel_min_sala_escape
        for semilla in range(30):
            puertas, pity_nuevo = generar_puertas_sala(
                sala,
                9,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                rng=_rng(semilla),
                n_salas=self.config.n_salas,
                pity=pity,
                estado=estado,
                vidas_max=3,
            )
            self.assertFalse(any(puerta_es_tienda(p) for p in puertas))
            self.assertGreaterEqual(pity_nuevo.salas_sin_tienda, umbral)

    def test_hard_pity_tienda_pospone_hasta_tener_puntos(self) -> None:
        from Comun.eventos_partida import PityPuertasEspecialesEscape
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia
        from Comun.tienda_escape import precio_minimo_tienda_escape, puerta_es_tienda

        sala = self.config.salas[9]
        min_precio = precio_minimo_tienda_escape(10)
        self.assertIsNotNone(min_precio)
        broke = EstadoPartida(
            nombre="t",
            reglas=preset_resistencia(),
            vidas_restantes=3,
            puntos_arcade=0,
        )
        pity = PityPuertasEspecialesEscape(salas_sin_tienda=8)
        puertas_broke, pity = generar_puertas_sala(
            sala,
            9,
            materias_pool=self.materias_pool,
            pool_preguntas=self.pool,
            rng=_rng(4242),
            n_salas=self.config.n_salas,
            pity=pity,
            estado=broke,
            vidas_max=3,
        )
        self.assertFalse(any(puerta_es_tienda(p) for p in puertas_broke))
        self.assertGreaterEqual(pity.salas_sin_tienda, 8)

        rico = EstadoPartida(
            nombre="t",
            reglas=preset_resistencia(),
            vidas_restantes=3,
            puntos_arcade=min_precio,
        )
        sala_11 = self.config.salas[10]
        for intento in range(100):
            puertas, _ = generar_puertas_sala(
                sala_11,
                10,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                rng=_rng(8000 + intento),
                n_salas=self.config.n_salas,
                pity=pity,
                estado=rico,
                vidas_max=3,
            )
            if any(puerta_es_tienda(p) for p in puertas):
                return
        self.fail("Hard pity no insertó tienda en sala 11 cuando el jugador tenía puntos")

    def test_tienda_powerups_mas_probables_que_bonificaciones(self) -> None:
        from collections import Counter

        from Comun.tienda_escape import (
            IDS_BONIFICACION,
            IDS_POWERUP,
            PESO_BONIFICACION,
            PESO_POWERUP,
            es_bonificacion,
            peso_articulo,
            seleccionar_articulos_tienda_visita,
        )

        self.assertGreater(PESO_POWERUP, PESO_BONIFICACION)
        self.assertTrue(es_bonificacion("amuleto_puntos"))
        self.assertEqual(peso_articulo("bomba"), PESO_POWERUP)
        self.assertEqual(peso_articulo("amuleto_puntos"), PESO_BONIFICACION)

        contador: Counter[str] = Counter()
        for semilla in range(500):
            for oferta in seleccionar_articulos_tienda_visita(10, rng=_rng(semilla)):
                if oferta is not None:
                    contador[oferta.articulo.id] += 1
        powerups = sum(contador[i] for i in IDS_POWERUP)
        bonifs = sum(contador[i] for i in IDS_BONIFICACION)
        self.assertGreater(powerups, bonifs)

    def test_tienda_catalogo_y_economia(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import ReglasPartida
        from Comun.tienda_escape import (
            CATALOGO_TIENDA_ESCAPE,
            EstadoInventarioEscape,
            articulos_tienda_para_sala,
            comprar_articulo,
        )

        self.assertGreaterEqual(len(CATALOGO_TIENDA_ESCAPE), 8)
        sala1 = articulos_tienda_para_sala(1)
        sala5 = articulos_tienda_para_sala(5)
        self.assertLess(len(sala1), len(sala5))
        estado = EstadoPartida(
            nombre="t",
            reglas=ReglasPartida(),
            puntos_arcade=100,
            vidas_restantes=3,
        )
        inv = EstadoInventarioEscape()
        self.assertIsNone(comprar_articulo(estado, inv, "bomba"))
        self.assertEqual(inv.cantidad("bomba"), 1)
        bomba = next(a for a in CATALOGO_TIENDA_ESCAPE if a.id == "bomba")
        ff = next(a for a in CATALOGO_TIENDA_ESCAPE if a.id == "fifty_fifty")
        self.assertIn("1", bomba.descripcion)
        self.assertIn("2", ff.descripcion)
        self.assertNotEqual(bomba.descripcion, ff.descripcion)
        self.assertIsNone(comprar_articulo(estado, inv, "bomba"))
        self.assertEqual(inv.cantidad("bomba"), 2)

        visita: set[str] = set()
        inv_visita = EstadoInventarioEscape()
        estado_visita = EstadoPartida(
            nombre="t",
            reglas=ReglasPartida(),
            puntos_arcade=100,
            vidas_restantes=3,
        )
        self.assertIsNone(
            comprar_articulo(
                estado_visita,
                inv_visita,
                "bomba",
                comprados_en_visita=visita,
            )
        )
        visita.add("bomba")
        err_visita = comprar_articulo(
            estado_visita,
            inv_visita,
            "bomba",
            comprados_en_visita=visita,
        )
        self.assertIsNotNone(err_visita)
        self.assertEqual(inv_visita.cantidad("bomba"), 1)
        self.assertIsNone(
            comprar_articulo(
                estado_visita,
                inv_visita,
                "fifty_fifty",
                comprados_en_visita=visita,
            )
        )
        self.assertEqual(inv_visita.cantidad("fifty_fifty"), 1)

        estado_broke = EstadoPartida(
            nombre="t",
            reglas=ReglasPartida(),
            puntos_arcade=5,
            vidas_restantes=3,
        )
        err = comprar_articulo(estado_broke, inv, "bomba")
        self.assertIsNotNone(err)
        self.assertEqual(inv.cantidad("bomba"), 2)

    def test_bonificacion_tienda_efecto_instantaneo(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import ReglasPartida
        from Comun.tienda_escape import (
            EstadoInventarioEscape,
            articulo_comprable_tienda_escape,
            comprar_articulo,
            seleccionar_articulos_tienda_visita,
        )

        estado = EstadoPartida(
            nombre="t",
            reglas=ReglasPartida(),
            puntos_arcade=200,
            vidas_restantes=2,
        )
        inv = EstadoInventarioEscape()
        self.assertIsNone(
            comprar_articulo(estado, inv, "vida_refuerzo", vidas_max=3)
        )
        self.assertEqual(estado.vidas_restantes, 3)
        self.assertEqual(inv.cantidad("vida_refuerzo"), 0)
        from Comun.economia_partida import bonus_amuleto_tras_compra

        self.assertIsNone(
            comprar_articulo(estado, inv, "amuleto_puntos", numero_sala=1)
        )
        self.assertEqual(
            inv.bonus_proximo_acierto,
            bonus_amuleto_tras_compra(35, numero_sala=1),
        )
        self.assertEqual(inv.cantidad("amuleto_puntos"), 0)

        lleno = EstadoPartida(
            nombre="t",
            reglas=ReglasPartida(),
            puntos_arcade=200,
            vidas_restantes=3,
        )
        err = comprar_articulo(lleno, inv, "vida_refuerzo", vidas_max=3)
        self.assertIsNotNone(err)

        for semilla in range(200):
            arts = seleccionar_articulos_tienda_visita(
                10,
                rng=_rng(semilla),
                estado=lleno,
                vidas_max=3,
            )
            for art in arts:
                if art is None:
                    continue
                self.assertNotEqual(art.articulo.id, "vida_refuerzo")
                self.assertIsNone(
                    articulo_comprable_tienda_escape(
                        art.articulo.id, lleno, vidas_max=3
                    )
                )

    def test_precio_resistencia_escala_con_progreso(self) -> None:
        from Comun.tienda_escape import (
            precio_base_articulo,
            precio_resistencia_articulo,
            precio_resistencia_escalado,
        )

        base_bomba = precio_base_articulo("bomba")
        self.assertEqual(precio_resistencia_escalado(base_bomba, 1), base_bomba)
        self.assertEqual(precio_resistencia_articulo("bomba", 5), base_bomba)
        tarde = precio_resistencia_articulo("bomba", 200)
        self.assertGreater(tarde, base_bomba)
        self.assertLessEqual(tarde, base_bomba * 2)

    def test_combinar_tienda_sin_modificadores(self) -> None:
        from Comun.eventos_partida import combinar_modificadores_puerta, evento_por_id

        mods = combinar_modificadores_puerta(
            (
                evento_por_id("tienda"),
                evento_por_id("botin"),
            )
        )
        self.assertTrue(mods.sin_pregunta)
        self.assertEqual(mods.eventos_ids, ("tienda",))
        mods_niebla = combinar_modificadores_puerta(
            (evento_por_id("tienda"), evento_por_id("niebla_opciones"))
        )
        self.assertEqual(mods_niebla.eventos_ids, ("tienda",))

    def test_tienda_generada_sin_botin(self) -> None:
        from Comun.eventos_partida import generar_modificadores_puerta

        for semilla in range(800):
            mods = generar_modificadores_puerta(
                numero_sala=10,
                rng=_rng(semilla),
            )
            if "tienda" not in mods.eventos_ids:
                continue
            self.assertEqual(
                set(mods.eventos_ids),
                {"tienda"},
                msg=f"semilla {semilla}: {mods.eventos_ids}",
            )
            return
        self.fail("No se generó ninguna tienda en 800 intentos")

    def test_pity_dual_prob_base_descanso_mayor_que_tienda(self) -> None:
        prob_descanso = prob_puerta_especial_con_pity(
            prob_base=0.06,
            salas_sin_ver=0,
            incremento_por_sala=0.04,
        )
        prob_tienda = prob_puerta_especial_con_pity(
            prob_base=0.03,
            salas_sin_ver=0,
            incremento_por_sala=0.05,
        )
        self.assertGreater(prob_descanso, prob_tienda)

    def test_pity_dual_incrementa_y_resetea(self) -> None:
        pity = PityPuertasEspecialesEscape()
        mods_descanso = combinar_modificadores_puerta(
            (evento_por_id("descanso"),), numero_sala=3
        )
        mods_tienda = combinar_modificadores_puerta(
            (evento_por_id("tienda"),), numero_sala=5
        )
        pity = actualizar_pity_tras_sala(
            pity, (mods_descanso, mods_descanso, mods_descanso), numero_sala=3
        )
        self.assertEqual(pity.salas_sin_descanso, 0)
        self.assertEqual(pity.salas_sin_tienda, 1)
        pity = actualizar_pity_tras_sala(
            pity, (mods_tienda, mods_tienda, mods_tienda), numero_sala=5
        )
        self.assertEqual(pity.salas_sin_descanso, 1)
        self.assertEqual(pity.salas_sin_tienda, 0)

    def test_pity_tienda_alto_tras_varias_salas_sin_ver(self) -> None:
        pity = PityPuertasEspecialesEscape(salas_sin_tienda=8)
        visto = False
        for semilla in range(80):
            mods = generar_modificadores_puerta(
                numero_sala=10,
                rng=_rng(semilla),
                pity=pity,
            )
            if "tienda" in mods.eventos_ids:
                visto = True
                break
        self.assertTrue(visto)

    def test_pity_persiste_entre_salas_en_generacion(self) -> None:
        pity = PityPuertasEspecialesEscape()
        for idx in range(4):
            _, pity = generar_puertas_sala(
                self.config.salas[idx],
                idx,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                rng=_rng(777 + idx),
                n_salas=self.config.n_salas,
                pity=pity,
            )
        self.assertGreaterEqual(pity.salas_sin_tienda, 0)
        self.assertGreaterEqual(pity.salas_sin_descanso, 0)

    def test_hard_pity_umbral_descanso_y_tienda(self) -> None:
        pity_descanso = PityPuertasEspecialesEscape(salas_sin_descanso=3)
        self.assertFalse(debe_garantizar_descanso_escape(pity_descanso, 5))
        pity_descanso_ok = PityPuertasEspecialesEscape(salas_sin_descanso=4)
        self.assertTrue(debe_garantizar_descanso_escape(pity_descanso_ok, 5))
        pity_tienda = PityPuertasEspecialesEscape(salas_sin_tienda=7)
        self.assertFalse(debe_garantizar_tienda_escape(pity_tienda, 10))
        pity_tienda_ok = PityPuertasEspecialesEscape(salas_sin_tienda=8)
        self.assertTrue(debe_garantizar_tienda_escape(pity_tienda_ok, 10))
        self.assertEqual(SALAS_HARD_PITY_DESCANSO_ESCAPE, 5)
        self.assertEqual(SALAS_HARD_PITY_TIENDA_ESCAPE, 10)

    def test_hard_pity_garantiza_descanso_sala_5(self) -> None:
        sala = self.config.salas[4]
        pity = PityPuertasEspecialesEscape(salas_sin_descanso=4)
        for intento in range(200):
            puertas, _ = generar_puertas_sala(
                sala,
                4,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                rng=_rng(5000 + intento * 31),
                n_salas=self.config.n_salas,
                pity=pity,
            )
            if any("descanso" in p.modificadores.eventos_ids for p in puertas):
                return
        self.fail("Hard pity no insertó descanso en sala 5")

    def test_hard_pity_garantiza_tienda_sala_11_tras_milestone(self) -> None:
        sala = self.config.salas[10]
        pity = PityPuertasEspecialesEscape(salas_sin_tienda=8)
        for intento in range(200):
            puertas, _ = generar_puertas_sala(
                sala,
                10,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                rng=_rng(9000 + intento * 31),
                n_salas=self.config.n_salas,
                pity=pity,
            )
            if any("tienda" in p.modificadores.eventos_ids for p in puertas):
                return
        self.fail("Hard pity no insertó tienda en sala 11 (pity acumulado tras milestone)")

    def test_hard_pity_umbral_botin(self) -> None:
        pity_corto = PityPuertasEspecialesEscape(salas_sin_botin=1)
        self.assertFalse(debe_garantizar_botin_escape(pity_corto, 3))
        pity_ok = PityPuertasEspecialesEscape(salas_sin_botin=2)
        self.assertTrue(debe_garantizar_botin_escape(pity_ok, 3))
        self.assertEqual(SALAS_HARD_PITY_BOTIN_ESCAPE, 3)

    def test_sin_maldicion_escape_antes_sala_min(self) -> None:
        for intento in range(80):
            mods = generar_modificadores_puerta(
                numero_sala=SALA_MIN_MALDICION_ESCAPE - 1,
                rng=_rng(4100 + intento),
            )
            self.assertFalse(
                any(eid in RASGOS_MALDICION_ESCAPE for eid in mods.eventos_ids),
                mods.eventos_ids,
            )

    def test_hard_pity_maldicion_escape(self) -> None:
        pity_corto = PityPuertasEspecialesEscape(
            salas_sin_maldicion=SALAS_HARD_PITY_MALDICION_ESCAPE - 2,
        )
        self.assertFalse(
            debe_garantizar_maldicion_escape(
                pity_corto, SALA_MIN_MALDICION_ESCAPE
            )
        )
        pity_ok = PityPuertasEspecialesEscape(
            salas_sin_maldicion=SALAS_HARD_PITY_MALDICION_ESCAPE - 1,
        )
        self.assertTrue(
            debe_garantizar_maldicion_escape(pity_ok, SALA_MIN_MALDICION_ESCAPE)
        )
        desafios = [
            e
            for e in eventos_puerta_escape_para_sala(SALA_MIN_MALDICION_ESCAPE)
            if not e.exclusivo_puerta_escape
            and e.id not in RASGOS_BOTIN_ESCAPE
        ]
        self.assertTrue(
            any(e.id in RASGOS_MALDICION_ESCAPE for e in desafios),
            "Pool de desafíos sin rasgos de maldición elegibles",
        )
        for intento in range(120):
            mods = generar_modificadores_puerta(
                numero_sala=SALA_MIN_MALDICION_ESCAPE,
                rng=_rng(4200 + intento * 17),
                pity=pity_ok,
            )
            if any(eid in RASGOS_MALDICION_ESCAPE for eid in mods.eventos_ids):
                return
        self.fail("Hard pity no insertó maldición en sala elegible")

    def test_pity_maldicion_escape_actualiza_contadores(self) -> None:
        pity = PityPuertasEspecialesEscape(salas_sin_maldicion=3)
        puertas_solo_crono = (
            PuertaEscape(
                indice=0,
                n_preguntas=3,
                modificadores=combinar_modificadores_puerta(
                    (evento_por_id("cronometro_bloque"),),
                    numero_sala=12,
                ),
                evento=instanciar_evento_contenido(
                    evento_por_id("puerta_materia"),
                    materias_pool=self.materias_pool,
                    grupos_pool=(),
                    rng=_rng(1),
                    indice_puerta=0,
                ),
            ),
        )
        sin_maldicion = actualizar_pity_tras_sala(pity, puertas_solo_crono, numero_sala=12)
        self.assertEqual(sin_maldicion.salas_sin_maldicion, 4)
        self.assertGreater(sin_maldicion.maldiciones_sin_por_id.get("puerta_maldita", 0), 0)

        puertas_maldita = (
            PuertaEscape(
                indice=0,
                n_preguntas=3,
                modificadores=combinar_modificadores_puerta(
                    (evento_por_id("puerta_maldita"), evento_por_id("cronometro_bloque")),
                    numero_sala=12,
                ),
                evento=instanciar_evento_contenido(
                    evento_por_id("puerta_materia"),
                    materias_pool=self.materias_pool,
                    grupos_pool=(),
                    rng=_rng(2),
                    indice_puerta=0,
                ),
            ),
        )
        nuevo = actualizar_pity_tras_sala(pity, puertas_maldita, numero_sala=12)
        self.assertEqual(nuevo.salas_sin_maldicion, 0)
        self.assertEqual(nuevo.maldiciones_sin_por_id.get("puerta_maldita"), 0)

    def test_hard_pity_garantiza_botin_sala_3(self) -> None:
        sala = self.config.salas[2]
        pity = PityPuertasEspecialesEscape(salas_sin_botin=2)
        for intento in range(200):
            puertas, _ = generar_puertas_sala(
                sala,
                2,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                rng=_rng(3000 + intento * 31),
                n_salas=self.config.n_salas,
                pity=pity,
            )
            if any(
                any(eid in RASGOS_BOTIN_ESCAPE for eid in p.modificadores.eventos_ids)
                for p in puertas
            ):
                return
        self.fail("Hard pity no insertó botín en sala 3")

    def test_hard_pity_botin_nunca_en_tienda(self) -> None:
        import random

        from Comun.escape_room import _insertar_botin_en_puerta_escape
        from Comun.tienda_escape import puerta_es_tienda

        evento = instanciar_evento_contenido(
            evento_por_id("puerta_materia"),
            materias_pool=self.materias_pool,
            grupos_pool=(),
            rng=_rng(1),
            indice_puerta=0,
        )
        puertas = [
            PuertaEscape(
                indice=0,
                n_preguntas=3,
                modificadores=combinar_modificadores_puerta((), numero_sala=10),
                evento=evento,
            ),
            PuertaEscape(
                indice=1,
                n_preguntas=0,
                modificadores=combinar_modificadores_puerta(
                    (evento_por_id("descanso"),), numero_sala=10
                ),
                evento=evento,
            ),
            PuertaEscape(
                indice=2,
                n_preguntas=0,
                modificadores=combinar_modificadores_puerta(
                    (evento_por_id("tienda"),), numero_sala=10
                ),
                evento=evento,
            ),
        ]
        _insertar_botin_en_puerta_escape(
            puertas, numero_sala=10, rng=random.Random(0), sala_idx=9
        )
        self.assertTrue(puerta_es_tienda(puertas[2]))
        self.assertFalse(
            any(eid in RASGOS_BOTIN_ESCAPE for eid in puertas[2].modificadores.eventos_ids)
        )
        con_botin = [
            p
            for p in puertas
            if any(eid in RASGOS_BOTIN_ESCAPE for eid in p.modificadores.eventos_ids)
        ]
        self.assertEqual(len(con_botin), 1)
        self.assertIn(con_botin[0].indice, (0, 1))

    def test_hard_pity_botin_puede_caer_en_descanso(self) -> None:
        import random

        from Comun.escape_room import _insertar_botin_en_puerta_escape

        evento = instanciar_evento_contenido(
            evento_por_id("puerta_materia"),
            materias_pool=self.materias_pool,
            grupos_pool=(),
            rng=_rng(2),
            indice_puerta=0,
        )
        for semilla in range(80):
            puertas = [
                PuertaEscape(
                    indice=0,
                    n_preguntas=3,
                    modificadores=combinar_modificadores_puerta((), numero_sala=8),
                    evento=evento,
                ),
                PuertaEscape(
                    indice=1,
                    n_preguntas=0,
                    modificadores=combinar_modificadores_puerta(
                        (evento_por_id("descanso"),), numero_sala=8
                    ),
                    evento=evento,
                ),
            ]
            _insertar_botin_en_puerta_escape(
                puertas, numero_sala=8, rng=random.Random(semilla), sala_idx=7
            )
            descanso = puertas[1]
            if any(
                eid in RASGOS_BOTIN_ESCAPE for eid in descanso.modificadores.eventos_ids
            ):
                self.assertIn("descanso", descanso.modificadores.eventos_ids)
                return
        self.fail("Hard pity no insertó botín en puerta de descanso en ningún intento")

    def test_pity_botin_incrementa_y_resetea(self) -> None:
        import random

        pity = PityPuertasEspecialesEscape()
        mods_botin = combinar_modificadores_puerta(
            (evento_por_id("botin_bomba"),), numero_sala=3
        )
        pity = actualizar_pity_tras_sala(
            pity, (mods_botin, mods_botin, mods_botin), numero_sala=3
        )
        self.assertEqual(pity.salas_sin_botin, 0)
        pity = actualizar_pity_tras_sala(
            pity,
            (combinar_modificadores_puerta((), numero_sala=4),) * 3,
            numero_sala=4,
        )
        self.assertEqual(pity.salas_sin_botin, 1)

    def test_elegir_botin_powerup_sala_baja(self) -> None:
        import random

        rng = _rng(42)
        botin = elegir_botin_para_sala(3, rng)
        self.assertIsNotNone(botin)
        assert botin is not None
        self.assertIn(botin.id, RASGOS_BOTIN_POWERUP_ESCAPE)

    def test_bonificacion_botin_powerup(self) -> None:
        from Comun.emojis_escape import CapaIconoEscape
        from Comun.eventos_partida import iconos_efecto_puerta, lineas_botin_puerta

        mods = combinar_modificadores_puerta(
            (evento_por_id("botin_bomba"),), numero_sala=5
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=mods,
            evento=instanciar_evento_contenido(
                evento_por_id("puerta_materia"),
                materias_pool=self.materias_pool,
                grupos_pool=(),
                rng=_rng(1),
                indice_puerta=0,
            ),
        )
        bonus = bonificacion_completar_escape(puerta)
        self.assertTrue(bonus.tiene_recompensa)
        self.assertEqual(bonus.powerups, (("bomba", 1),))
        lineas = lineas_botin_puerta(mods)
        self.assertEqual(len(lineas), 1)
        iconos = iconos_efecto_puerta(
            evento=puerta.evento,
            modificadores=mods,
            n_preguntas=3,
            rng=_rng(0),
        )
        self.assertTrue(any(ic.capa == CapaIconoEscape.BOTIN for ic in iconos))

    def test_generar_puede_incluir_tienda(self) -> None:
        from Comun.eventos_partida import generar_modificadores_puerta

        visto = False
        for semilla in range(500):
            mods = generar_modificadores_puerta(
                numero_sala=10,
                rng=_rng(semilla),
            )
            if "tienda" in mods.eventos_ids:
                visto = True
                break
        self.assertTrue(visto)

    def test_bomba_y_fifty_incompatibles_escape(self) -> None:
        from Comun.modelos import Pregunta
        from Comun.tienda_escape import EstadoInventarioEscape, usar_objeto

        inv = EstadoInventarioEscape()
        inv.agregar("bomba")
        inv.agregar("fifty_fifty")
        p = Pregunta(
            texto="?",
            materia="M",
            tematica="",
            dificultad="Facil",
            tipo="test",
            grupo="",
            nivel="",
            curso="1",
            semestre="1",
            opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
            correcta="B",
        )
        self.assertIsNone(usar_objeto("bomba", inv, p))
        self.assertIsNotNone(usar_objeto("fifty_fifty", inv, p))
        inv.reiniciar_slot_pregunta()
        self.assertIsNone(usar_objeto("fifty_fifty", inv, p))

    def test_bomba_y_tiempo_extra_un_solo_slot_escape(self) -> None:
        from Comun.modelos import Pregunta
        from Comun.tienda_escape import EstadoInventarioEscape, usar_objeto

        inv = EstadoInventarioEscape()
        inv.agregar("bomba")
        inv.agregar("tiempo_extra")
        p = Pregunta(
            texto="?",
            materia="M",
            tematica="",
            dificultad="Facil",
            tipo="test",
            grupo="",
            nivel="",
            curso="1",
            semestre="1",
            opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
            correcta="B",
        )
        self.assertIsNone(usar_objeto("bomba", inv, p))
        self.assertIsNotNone(usar_objeto("tiempo_extra", inv, p))
        self.assertEqual(inv.tiempo_extra_seg, 0)

    def test_puerta_maldita_modificadores_y_compatibilidad(self) -> None:
        from Comun.eventos_partida import (
            RASGO_PUERTA_MALDITA,
            RASGOS_MALDICION_ESCAPE,
            _compatible_con_rasgos_puerta,
            combinar_modificadores_puerta,
            evento_por_id,
        )

        self.assertEqual(
            RASGOS_MALDICION_ESCAPE,
            frozenset({"puerta_maldita"}),
        )
        self.assertNotIn("niebla_opciones", RASGOS_MALDICION_ESCAPE)
        self.assertNotIn("relampago", RASGOS_MALDICION_ESCAPE)
        self.assertNotIn("cronometro_bloque", RASGOS_MALDICION_ESCAPE)
        self.assertNotIn("cronometro_doble", RASGOS_MALDICION_ESCAPE)

        maldita = evento_por_id(RASGO_PUERTA_MALDITA)
        cronometro_bloque = evento_por_id("cronometro_bloque")
        cronometro_pregunta = evento_por_id("cronometro_pregunta")
        cronometro_doble = evento_por_id("cronometro_doble")
        self.assertTrue(
            _compatible_con_rasgos_puerta(cronometro_bloque, (maldita,)),
            "Maldición mortal y cronómetro de puerta deben poder combinarse",
        )
        self.assertTrue(
            _compatible_con_rasgos_puerta(cronometro_pregunta, (maldita,)),
            "Maldición mortal y cronómetro por pregunta deben poder combinarse",
        )
        self.assertTrue(
            _compatible_con_rasgos_puerta(cronometro_doble, (maldita,)),
            "Maldición mortal y cronómetro doble deben poder combinarse",
        )
        mods_combo = combinar_modificadores_puerta(
            (maldita, cronometro_bloque), numero_sala=15
        )
        self.assertTrue(mods_combo.fin_partida_si_fallo)
        self.assertIsNotNone(mods_combo.tiempo_puerta_seg)
        mods_combo_preg = combinar_modificadores_puerta(
            (maldita, cronometro_pregunta), numero_sala=15
        )
        self.assertTrue(mods_combo_preg.fin_partida_si_fallo)
        self.assertIsNotNone(mods_combo_preg.tiempo_pregunta_seg)
        mods_combo_doble = combinar_modificadores_puerta(
            (maldita, cronometro_doble), numero_sala=15
        )
        self.assertTrue(mods_combo_doble.fin_partida_si_fallo)
        self.assertIsNotNone(mods_combo_doble.tiempo_puerta_seg)
        self.assertIsNotNone(mods_combo_doble.tiempo_pregunta_seg)

        mods = combinar_modificadores_puerta((maldita,), numero_sala=15)
        self.assertTrue(mods.fin_partida_si_fallo)
        self.assertIn(RASGO_PUERTA_MALDITA, mods.eventos_ids)

        descanso = evento_por_id("descanso")
        mods_pausa = combinar_modificadores_puerta((descanso,), numero_sala=10)
        self.assertFalse(mods_pausa.fin_partida_si_fallo)
        self.assertTrue(mods_pausa.sin_pregunta)

        mods_mix = combinar_modificadores_puerta(
            (descanso, maldita), numero_sala=10
        )
        self.assertTrue(mods_mix.sin_pregunta)
        self.assertFalse(mods_mix.fin_partida_si_fallo)

    def test_fallo_puerta_maldita_sin_sello(self) -> None:
        from Comun.escape_partida import (
            procesar_fallo_puerta_maldita,
            puerta_es_maldita,
        )
        from Comun.escape_room import PuertaEscape
        from Comun.eventos_partida import (
            combinar_modificadores_puerta,
            evento_por_id,
            instanciar_evento_contenido,
        )

        mods = combinar_modificadores_puerta(
            (evento_por_id("puerta_maldita"),), numero_sala=12
        )
        evento = instanciar_evento_contenido(
            evento_por_id("puerta_materia"),
            materias_pool=self.materias_pool[:1],
            grupos_pool=(),
            rng=_rng(3),
            indice_puerta=0,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=mods,
            evento=evento,
        )
        self.assertTrue(puerta_es_maldita(puerta))

        mortal = procesar_fallo_puerta_maldita(puerta, proteccion_activa=False)
        self.assertIsNotNone(mortal)
        assert mortal is not None
        self.assertTrue(mortal.fin_partida)

    def test_alcance_powerup_sala_no_gasta_slot_pregunta(self) -> None:
        from Comun.escape_room import PuertaEscape
        from Comun.eventos_partida import (
            combinar_modificadores_puerta,
            evento_por_id,
            instanciar_evento_contenido,
        )
        from Comun.objetos_partida import MENSAJE_POWERUP_YA_USADO_ESCAPE
        from Comun.powerups_puerta_escape import (
            AlcancePowerupEscape,
            alcance_powerup_escape,
            puede_usar_powerup_escape,
            registrar_uso_powerup_escape,
        )
        from Comun.tienda_escape import EstadoInventarioEscape

        self.assertEqual(
            alcance_powerup_escape("reroll_puertas"), AlcancePowerupEscape.SALA
        )
        self.assertEqual(
            alcance_powerup_escape("bomba"), AlcancePowerupEscape.PREGUNTA
        )

        inv = EstadoInventarioEscape()
        inv.agregar("reroll_puertas")
        inv.agregar("bomba")
        inv.agregar("tiempo_extra")

        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=combinar_modificadores_puerta((), numero_sala=5),
            evento=instanciar_evento_contenido(
                evento_por_id("puerta_materia"),
                materias_pool=self.materias_pool[:1],
                grupos_pool=(),
                rng=_rng(4),
                indice_puerta=0,
            ),
        )

        self.assertIsNone(
            puede_usar_powerup_escape(
                "reroll_puertas",
                inv,
                puerta,
                pregunta_idx=0,
                modo="sala",
                puertas_sala=(puerta,),
            )
        )
        self.assertIsNone(
            puede_usar_powerup_escape("bomba", inv, puerta, pregunta_idx=0, modo="pregunta")
        )
        registrar_uso_powerup_escape(inv, "bomba")
        self.assertEqual(
            puede_usar_powerup_escape(
                "tiempo_extra", inv, puerta, pregunta_idx=0, modo="pregunta"
            ),
            MENSAJE_POWERUP_YA_USADO_ESCAPE,
        )
        self.assertEqual(
            puede_usar_powerup_escape(
                "reroll_puertas",
                inv,
                puerta,
                pregunta_idx=0,
                modo="pregunta",
            ),
            "Este objeto es del inventario de sala (úsalo al elegir puerta).",
        )

    def test_escape_un_powerup_bloquea_skip_y_cambio(self) -> None:
        from Comun.escape_room import PuertaEscape
        from Comun.eventos_partida import (
            combinar_modificadores_puerta,
            evento_por_id,
            instanciar_evento_contenido,
        )
        from Comun.objetos_partida import MENSAJE_POWERUP_YA_USADO_ESCAPE
        from Comun.powerups_puerta_escape import puede_usar_powerup_escape
        from Comun.tienda_escape import EstadoInventarioEscape

        inv = EstadoInventarioEscape()
        inv.agregar("comodin")
        inv.agregar("skip")
        inv.agregar("cambio")
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=combinar_modificadores_puerta((), numero_sala=5),
            evento=instanciar_evento_contenido(
                evento_por_id("puerta_materia"),
                materias_pool=self.materias_pool[:1],
                grupos_pool=(),
                rng=_rng(2),
                indice_puerta=0,
            ),
        )
        kwargs = dict(puerta=puerta, pregunta_idx=0, modo="pregunta")
        inv.powerups_usados_en_pregunta.add("comodin")
        self.assertEqual(
            puede_usar_powerup_escape("skip", inv, **kwargs),
            MENSAJE_POWERUP_YA_USADO_ESCAPE,
        )
        self.assertEqual(
            puede_usar_powerup_escape("cambio", inv, **kwargs),
            MENSAJE_POWERUP_YA_USADO_ESCAPE,
        )
        inv.powerups_usados_en_pregunta.clear()
        self.assertIsNone(puede_usar_powerup_escape("skip", inv, **kwargs))
        self.assertIsNone(puede_usar_powerup_escape("cambio", inv, **kwargs))

    def test_dos_inventarios_separados(self) -> None:
        from Comun.objetos_partida import POWERUPS_SOLO_RESISTENCIA
        from Comun.powerups_puerta_escape import es_powerup_inventario_puerta_escape
        from Comun.tienda_escape import EstadoInventarioEscape

        inv = EstadoInventarioEscape()
        inv.agregar("bomba", 2)
        inv.agregar("limpieza_maldiciones", 1)
        inv.agregar("sello_purga", 1)
        self.assertEqual(inv.cantidad_pregunta("bomba"), 2)
        self.assertEqual(inv.cantidad_puerta("limpieza_maldiciones"), 1)
        self.assertEqual(inv.cantidad_pregunta("limpieza_maldiciones"), 0)
        self.assertEqual(inv.cantidad_pregunta("sello_purga"), 1)
        self.assertEqual(inv.cantidad_puerta("sello_purga"), 0)
        self.assertTrue(es_powerup_inventario_puerta_escape("limpieza_maldiciones"))
        self.assertFalse(es_powerup_inventario_puerta_escape("bomba"))
        self.assertFalse(es_powerup_inventario_puerta_escape("sello_purga"))
        self.assertIn("sello_purga", POWERUPS_SOLO_RESISTENCIA)
        self.assertTrue(inv.tiene_items_puerta())
        inv.consumir("limpieza_maldiciones")
        self.assertFalse(inv.tiene_items_puerta())
        self.assertEqual(inv.cantidad_pregunta("bomba"), 2)

    def test_powerups_sala_ids_distintos_y_routing(self) -> None:
        from Comun.objetos_partida import (
            POWERUPS_LOOT_ESCAPE,
            POWERUPS_PREGUNTA,
            POWERUPS_SOLO_RESISTENCIA,
            POWERUPS_SOLO_SALA_ESCAPE,
        )
        from Comun.powerups_puerta_escape import es_powerup_sala_escape
        from Comun.tienda_escape import EstadoInventarioEscape

        self.assertFalse(POWERUPS_PREGUNTA.keys() & POWERUPS_SOLO_SALA_ESCAPE)
        self.assertFalse(POWERUPS_SOLO_RESISTENCIA & POWERUPS_SOLO_SALA_ESCAPE)
        self.assertNotIn("sello_purga", POWERUPS_LOOT_ESCAPE)
        self.assertIn("skip", POWERUPS_PREGUNTA)
        self.assertIn("salto_sala", POWERUPS_SOLO_SALA_ESCAPE)
        self.assertTrue(es_powerup_sala_escape("reroll_puertas"))

        inv = EstadoInventarioEscape()
        inv.agregar("reroll_puertas", 1)
        self.assertTrue(inv.tiene_items_puerta())
        self.assertFalse(inv.tiene_items_preparacion_puerta())

    def test_limpieza_maldiciones_y_reroll_puertas(self) -> None:
        from Comun.escape_room import (
            PuertaEscape,
            quitar_maldicion_puertas_sala,
            regenerar_puertas_sala_escape,
        )
        from Comun.eventos_partida import (
            combinar_modificadores_puerta,
            evento_por_id,
            instanciar_evento_contenido,
        )
        from Comun.powerups_puerta_escape import puede_usar_powerup_escape
        from Comun.tienda_escape import EstadoInventarioEscape

        mods = combinar_modificadores_puerta(
            (evento_por_id("puerta_maldita"),), numero_sala=12
        )
        evento = instanciar_evento_contenido(
            evento_por_id("puerta_materia"),
            materias_pool=self.materias_pool[:1],
            grupos_pool=(),
            rng=_rng(7),
            indice_puerta=0,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=mods,
            evento=evento,
        )
        limpias = quitar_maldicion_puertas_sala((puerta,), numero_sala=12)
        self.assertFalse(limpias[0].modificadores.fin_partida_si_fallo)

        inv = EstadoInventarioEscape()
        inv.agregar("limpieza_maldiciones")
        self.assertIsNone(
            puede_usar_powerup_escape(
                "limpieza_maldiciones",
                inv,
                None,
                pregunta_idx=0,
                modo="sala",
                puertas_sala=(puerta,),
            )
        )
        mods_ok = combinar_modificadores_puerta((), numero_sala=5)
        puerta_ok = PuertaEscape(
            indice=0,
            n_preguntas=2,
            modificadores=mods_ok,
            evento=evento,
        )
        self.assertEqual(
            puede_usar_powerup_escape(
                "limpieza_maldiciones",
                inv,
                None,
                pregunta_idx=0,
                modo="sala",
                puertas_sala=(puerta_ok,),
            ),
            "No hay puertas malditas en esta sala.",
        )

        cfg = config_escape_room(n_salas=3)
        sala = cfg.salas[0]
        antes = regenerar_puertas_sala_escape(
            sala,
            0,
            materias_pool=self.materias_pool,
            pool_preguntas=self.pool,
            rng=_rng(11),
            puertas_por_sala=cfg.puertas_por_sala,
            n_salas=cfg.n_salas,
        )
        despues = regenerar_puertas_sala_escape(
            sala,
            0,
            materias_pool=self.materias_pool,
            pool_preguntas=self.pool,
            rng=_rng(12),
            puertas_por_sala=cfg.puertas_por_sala,
            n_salas=cfg.n_salas,
            pity=PityPuertasEspecialesEscape(salas_sin_descanso=10),
        )
        self.assertEqual(len(antes), len(despues))
        self.assertEqual(len(antes), cfg.puertas_por_sala)

    def test_salto_sala_modo_sala(self) -> None:
        from Comun.powerups_puerta_escape import puede_usar_powerup_escape
        from Comun.tienda_escape import EstadoInventarioEscape

        inv = EstadoInventarioEscape()
        inv.agregar("salto_sala")
        self.assertIsNone(
            puede_usar_powerup_escape(
                "salto_sala",
                inv,
                None,
                pregunta_idx=0,
                modo="sala",
                puertas_sala=(),
            )
        )
        self.assertEqual(
            puede_usar_powerup_escape(
                "salto_sala",
                inv,
                None,
                pregunta_idx=0,
                modo="pregunta",
            ),
            "Este objeto es del inventario de sala (úsalo al elegir puerta).",
        )


class TestLayoutInventarioEscape(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.pool = construir_pool_escape(
            cargar_preguntas(PATH_PREGUNTAS, cls.materias_meta)
        )
        cls.materias_pool = materias_del_pool(cls.pool)

    def test_empaquetar_seis_botones_anchos_en_dos_filas(self) -> None:
        from Grafico.pantallas_escape import empaquetar_filas_inventario
        from Grafico.tema import ANCHO, MARGEN

        ancho_disp = ANCHO - 2 * MARGEN
        filas = empaquetar_filas_inventario(
            [156] * 6,
            ancho_disponible=ancho_disp,
        )
        self.assertGreaterEqual(len(filas), 2)
        for fila in filas:
            ancho_fila = sum(fila) + max(0, len(fila) - 1) * 8
            self.assertLessEqual(ancho_fila, ancho_disp)

    def test_botones_inventario_no_salen_de_pantalla(self) -> None:
        from Comun.objetos_partida import POWERUPS_LOOT_ESCAPE
        from Comun.presets_historia import aplicar_preset, buscar_preset
        from Grafico.pantallas_escape import PartidaEscapeRoom
        from Grafico.tema import ANCHO, MARGEN
        from Tests.Fixtures.helpers_navegacion_grafico import configurar_pygame_tests

        configurar_pygame_tests()
        preset = buscar_preset("escape_room")
        config = config_escape_room()
        partida = PartidaEscapeRoom(
            nombre="Test",
            preset=preset,
            config=config,
            pool=self.pool,
            materias_pool=self.materias_pool,
            reglas=aplicar_preset(preset, None),
            semilla=42,
            total_previsto=total_preguntas_escape(config),
            ir_a=lambda _p: None,
            datos=None,
            salir_app=lambda: None,
        )
        partida._elegir_puerta(1)
        for pid in POWERUPS_LOOT_ESCAPE:
            partida.inventario_escape.agregar(pid)
        partida._reconstruir_inventario_botones()
        self.assertGreaterEqual(len(partida.botones_inventario), 6)
        for boton in partida.botones_inventario:
            self.assertGreaterEqual(boton.rect.x, MARGEN)
            self.assertLessEqual(boton.rect.right, ANCHO - MARGEN)
            self.assertLessEqual(boton.rect.bottom, 720)


if __name__ == "__main__":
    unittest.main()
