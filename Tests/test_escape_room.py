#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas del modo escape room."""

from __future__ import annotations

import unittest
from dataclasses import replace

from Tests.support import ensure_juego_path

ensure_juego_path()

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
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
from Comun.reglas_partida import preset_escape  # noqa: E402
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
)
from Comun.presets_historia import aplicar_preset, buscar_preset  # noqa: E402
from Comun.motor_nucleo import EstadoPartida  # noqa: E402
from Comun.politica_reglas import ContextoPartida  # noqa: E402
from Comun.rutas import PATH_PREGUNTAS, resolver_listado_materias  # noqa: E402


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
            semilla=42,
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
        for idx in range(5):
            puertas, _ = generar_puertas_sala(
                self.config.salas[idx],
                idx,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                semilla=99,
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
                    semilla=semilla,
                    n_salas=self.config.n_salas,
                )
                firmas = [firma_puerta_escape(p) for p in puertas]
                self.assertEqual(
                    len(firmas),
                    len(set(firmas)),
                    msg=f"sala={idx + 1} semilla={semilla} firmas={firmas}",
                )

    def test_catalogo_contenido_tres_tipos_principales(self) -> None:
        ids = {e.id for e in eventos_contenido_escape_para_sala(1)}
        self.assertEqual(ids, {"puerta_materia"})
        ids_s6 = {e.id for e in eventos_contenido_escape_para_sala(6)}
        self.assertEqual(ids_s6, {"puerta_materia", "puerta_grupo"})
        self.assertNotIn("materia_sorpresa", ids)
        self.assertNotIn("asignatura", ids)

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
                        semilla=semilla,
                        indice_puerta=indice,
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
                numero_sala=25, semilla=7, indice_puerta=i
            ).rasgos == ("Clásica",)
        )
        self.assertLess(clasicas, 20)

    def test_iconos_efecto_puerta_orden_y_tooltips(self) -> None:
        from Comun.eventos_partida import (
            EMOJI_NIEBLA_OPCIONES,
            EMOJI_PUERTA_MATERIA,
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
        )
        self.assertEqual(len(iconos), 4)
        self.assertEqual(iconos[0].emoji, "⏱️")
        self.assertEqual(iconos[1].emoji, EMOJI_NIEBLA_OPCIONES)
        self.assertEqual(iconos[2].emoji, EMOJI_PUERTA_MATERIA)
        self.assertEqual(iconos[3].emoji, "🟢")
        self.assertIn("28 s", iconos[0].tooltip)
        self.assertIn("al azar", iconos[1].tooltip.lower())
        self.assertIn("materia concreta", iconos[2].tooltip)
        self.assertIn("fáciles", iconos[3].tooltip)
        self.assertNotIn("fácil", iconos[2].tooltip.lower())

    def test_iconos_efecto_puerta_maximo_cinco(self) -> None:
        from Comun.emojis_escape import CapaIconoEscape
        from Comun.eventos_partida import EMOJI_BOTIN_ESCAPE, EMOJI_PUERTA_MATERIA, iconos_efecto_puerta

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
            semilla=42,
        )
        self.assertLessEqual(len(iconos), 5)
        self.assertEqual(len(iconos), 5)
        capas = {ic.capa for ic in iconos}
        self.assertIn(CapaIconoEscape.TIPO_PUERTA, capas)
        self.assertIn(CapaIconoEscape.DIFICULTAD, capas)
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
                semilla=semilla,
            )
            self.assertLessEqual(len(iconos), 5, msg=f"semilla={semilla}")
            for capa in (
                CapaIconoEscape.TIPO_PUERTA,
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
                evento_por_id("botin"),
            )
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=4,
            semilla=1,
        )
        self.assertEqual(len(iconos), 5)
        self.assertNotIn(CapaIconoEscape.TIPO_PREGUNTA, {ic.capa for ic in iconos})
        self.assertIn(CapaIconoEscape.TIEMPO, {ic.capa for ic in iconos})
        self.assertIn(CapaIconoEscape.NIEBLA, {ic.capa for ic in iconos})

    def test_iconos_capas_contenido_puerta(self) -> None:
        from Comun.eventos_partida import (
            EMOJI_DIF_BALANCEADO,
            EMOJI_DIF_FACIL,
            EMOJI_MIX_MATERIA,
            EMOJI_PUERTA_GRUPO,
            EMOJI_PUERTA_MATERIA,
            EMOJI_TIPO_CALCULO,
            EMOJI_TIPO_TEORIA,
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
        self.assertEqual([i.emoji for i in facil], [EMOJI_PUERTA_MATERIA, EMOJI_DIF_FACIL])
        self.assertIn("fáciles", facil[1].tooltip)
        self.assertNotIn("fácil", facil[0].tooltip.lower())

        balanceado = iconos("pregunta_unica", perfil_id="balanceado")
        self.assertEqual(balanceado[1].emoji, EMOJI_DIF_BALANCEADO)

        mix = iconos("mix_facil_media", perfil_id="mix_facil_media")
        self.assertEqual(mix[1].emoji, EMOJI_MIX_MATERIA)
        self.assertEqual(mix[1].tooltip, TOOLTIP_MIX_MATERIA)

        teoria = iconos("solo_teoria", perfil_id="teoria")
        self.assertEqual(
            [i.emoji for i in teoria],
            [EMOJI_PUERTA_MATERIA, EMOJI_DIF_BALANCEADO, EMOJI_TIPO_TEORIA],
        )

        calculo = iconos("solo_calculo", perfil_id="calculo")
        self.assertEqual(calculo[-1].emoji, EMOJI_TIPO_CALCULO)

        grupo = iconos("bloque_grupo", perfil_id="facil")
        self.assertEqual(
            [i.emoji for i in grupo],
            [EMOJI_PUERTA_GRUPO, EMOJI_DIF_FACIL],
        )

    def test_plantilla_grupo_lleva_perfil_contenido(self) -> None:
        from Comun.eventos_partida import elegir_plantillas_contenido_escape
        import random

        rng = random.Random(42)
        plantillas = elegir_plantillas_contenido_escape(3, numero_sala=20, rng=rng)
        grupos = [(p, pid) for p, pid in plantillas if p.id == "puerta_grupo"]
        self.assertTrue(grupos)
        for plantilla, perfil_id in grupos:
            self.assertIsNotNone(perfil_id)
            self.assertIsNotNone(plantilla.modificadores.dificultades_permitidas or plantilla.contenido_escape.tipos_permitidos or perfil_id == "balanceado")

    def test_seleccion_preguntas_desafio(self) -> None:
        viables = materias_viables_sala(
            self.pool, self.materias_pool, numero_sala=1, n_salas=30
        )
        materia = viables[0]
        evento = instanciar_evento_contenido(
            evento_por_id("pregunta_unica"),
            materias_pool=(materia,),
            grupos_pool=(),
            semilla=1,
            indice_puerta=0,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=3,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        lote = seleccionar_preguntas_desafio(
            self.pool, puerta, numero_sala=1, n_salas=30, semilla=42
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
                pool, puerta, numero_sala=1, n_salas=30, semilla=semilla
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
                pool, puerta, numero_sala=1, n_salas=30, semilla=semilla
            )
            self.assertEqual(len(lote), 3)
            self.assertEqual(
                {p.dificultad for p in lote},
                {"Facil", "Media"},
                msg=f"semilla={semilla}",
            )

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
            self.pool, puerta, numero_sala=15, n_salas=30, semilla=7
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
            semilla=42,
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
                semilla=99,
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
            self.pool, puerta, numero_sala=15, n_salas=30, semilla=11
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
        )
        self.assertTrue(puerta_es_jefe(puerta))
        bonus = bonificacion_completar_escape(puerta)
        self.assertEqual(bonus.delta_vidas, 2)

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
        )
        self.assertEqual(iconos[-1].emoji, "🎁")
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
        self.assertEqual(mods.rasgos, ("Descanso", "Botín"))

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
                        semilla=semilla,
                        indice_puerta=indice,
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
        from Comun.reglas_partida import preset_escape

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
        from Comun.reglas_partida import preset_escape

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

        arts = seleccionar_articulos_tienda_visita(10, semilla=42)
        self.assertEqual(len(arts), ARTICULOS_POR_VISITA_TIENDA)
        presentes = [a for a in arts if a is not None]
        self.assertEqual(len({a.id for a in presentes}), len(presentes))
        otra = seleccionar_articulos_tienda_visita(10, semilla=99)
        self.assertNotEqual(
            [a.id if a else None for a in arts],
            [a.id if a else None for a in otra],
        )

    def test_tienda_visita_garantiza_articulo_asequible(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas_partida import preset_resistencia
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
                semilla=semilla,
                estado=estado,
                vidas_max=3,
            )
            asequibles = [a for a in arts if a is not None and a.precio <= 15]
            self.assertTrue(asequibles, msg=f"semilla={semilla}")

    def test_tienda_no_visitable_sin_puntos(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas_partida import preset_resistencia
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
            5, semilla=1, estado=estado, vidas_max=3
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
        from Comun.reglas_partida import preset_resistencia
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
                semilla=semilla,
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
        from Comun.reglas_partida import preset_resistencia
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
            semilla=4242,
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
        for intento in range(100):
            puertas, _ = generar_puertas_sala(
                sala,
                9,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                semilla=8000 + intento,
                n_salas=self.config.n_salas,
                pity=pity,
                estado=rico,
                vidas_max=3,
            )
            if any(puerta_es_tienda(p) for p in puertas):
                return
        self.fail("Hard pity no insertó tienda cuando el jugador tenía puntos")

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
            for art in seleccionar_articulos_tienda_visita(10, semilla=semilla):
                if art is not None:
                    contador[art.id] += 1
        powerups = sum(contador[i] for i in IDS_POWERUP)
        bonifs = sum(contador[i] for i in IDS_BONIFICACION)
        self.assertGreater(powerups, bonifs)

    def test_tienda_catalogo_y_economia(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas_partida import ReglasPartida
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
        from Comun.reglas_partida import ReglasPartida
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
        self.assertIsNone(
            comprar_articulo(estado, inv, "amuleto_puntos")
        )
        self.assertEqual(inv.bonus_proximo_acierto, 20)
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
                semilla=semilla,
                estado=lleno,
                vidas_max=3,
            )
            for art in arts:
                if art is None:
                    continue
                self.assertNotEqual(art.id, "vida_refuerzo")
                self.assertIsNone(
                    articulo_comprable_tienda_escape(
                        art.id, lleno, vidas_max=3
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
                semilla=semilla,
                indice_puerta=0,
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
                semilla=semilla,
                indice_puerta=0,
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
                semilla=777 + idx,
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
                semilla=5000 + intento * 31,
                n_salas=self.config.n_salas,
                pity=pity,
            )
            if any("descanso" in p.modificadores.eventos_ids for p in puertas):
                return
        self.fail("Hard pity no insertó descanso en sala 5")

    def test_hard_pity_garantiza_tienda_sala_10(self) -> None:
        sala = self.config.salas[9]
        pity = PityPuertasEspecialesEscape(salas_sin_tienda=8)
        for intento in range(200):
            puertas, _ = generar_puertas_sala(
                sala,
                9,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                semilla=9000 + intento * 31,
                n_salas=self.config.n_salas,
                pity=pity,
            )
            if any("tienda" in p.modificadores.eventos_ids for p in puertas):
                return
        self.fail("Hard pity no insertó tienda en sala 10")

    def test_hard_pity_umbral_botin(self) -> None:
        pity_corto = PityPuertasEspecialesEscape(salas_sin_botin=1)
        self.assertFalse(debe_garantizar_botin_escape(pity_corto, 3))
        pity_ok = PityPuertasEspecialesEscape(salas_sin_botin=2)
        self.assertTrue(debe_garantizar_botin_escape(pity_ok, 3))
        self.assertEqual(SALAS_HARD_PITY_BOTIN_ESCAPE, 3)

    def test_hard_pity_garantiza_botin_sala_3(self) -> None:
        sala = self.config.salas[2]
        pity = PityPuertasEspecialesEscape(salas_sin_botin=2)
        for intento in range(200):
            puertas, _ = generar_puertas_sala(
                sala,
                2,
                materias_pool=self.materias_pool,
                pool_preguntas=self.pool,
                semilla=3000 + intento * 31,
                n_salas=self.config.n_salas,
                pity=pity,
            )
            if any(
                any(eid in RASGOS_BOTIN_ESCAPE for eid in p.modificadores.eventos_ids)
                for p in puertas
            ):
                return
        self.fail("Hard pity no insertó botín en sala 3")

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

        rng = random.Random(42)
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
                semilla=1,
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
        )
        self.assertTrue(any(ic.capa == CapaIconoEscape.BOTIN for ic in iconos))

    def test_generar_puede_incluir_tienda(self) -> None:
        from Comun.eventos_partida import generar_modificadores_puerta

        visto = False
        for semilla in range(500):
            mods = generar_modificadores_puerta(
                numero_sala=10,
                semilla=semilla,
                indice_puerta=0,
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

    def test_bomba_y_tiempo_extra_compatibles_escape(self) -> None:
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
        self.assertIsNone(usar_objeto("tiempo_extra", inv, p))
        self.assertEqual(inv.tiempo_extra_seg, 20)


if __name__ == "__main__":
    unittest.main()
