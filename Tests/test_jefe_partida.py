#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jefes en escape y resistencia."""

from __future__ import annotations

import random
import unittest

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()


class TestJefePartida(unittest.TestCase):
    def test_tamano_bloque_o_jefe(self) -> None:
        from Comun.jefe_partida import (
            PREGUNTAS_POR_JEFE,
            TAMANOS_BLOQUE_NORMAL,
            elegir_tamano_bloque_normal,
            tamano_coherente_bloque_o_jefe,
        )

        rng = random.Random(0)
        for _ in range(50):
            self.assertIn(elegir_tamano_bloque_normal(rng), TAMANOS_BLOQUE_NORMAL)
        self.assertTrue(tamano_coherente_bloque_o_jefe(3, es_jefe=False))
        self.assertTrue(tamano_coherente_bloque_o_jefe(5, es_jefe=False))
        self.assertFalse(tamano_coherente_bloque_o_jefe(4, es_jefe=False))
        self.assertTrue(tamano_coherente_bloque_o_jefe(PREGUNTAS_POR_JEFE, es_jefe=True))
        self.assertFalse(tamano_coherente_bloque_o_jefe(5, es_jefe=True))

    def test_sala_milestone_y_conteo_puertas(self) -> None:
        from Comun.jefe_partida import (
            es_puerta_diez_preguntas,
            n_puertas_jefe_en_sala,
            sala_es_milestone_jefe,
        )

        self.assertFalse(sala_es_milestone_jefe(9))
        self.assertTrue(sala_es_milestone_jefe(10))
        self.assertEqual(n_puertas_jefe_en_sala(10), 1)
        self.assertEqual(n_puertas_jefe_en_sala(20), 2)
        self.assertEqual(n_puertas_jefe_en_sala(30), 3)
        self.assertEqual(n_puertas_jefe_en_sala(40), 3)
        self.assertEqual(n_puertas_jefe_en_sala(50), 3)
        self.assertEqual(n_puertas_jefe_en_sala(15), 0)
        self.assertTrue(es_puerta_diez_preguntas(10))
        self.assertFalse(es_puerta_diez_preguntas(5))

    def test_clasificar_dificultad_jefe(self) -> None:
        from Comun.jefe_partida import clasificar_dificultad_jefe

        self.assertEqual(
            clasificar_dificultad_jefe(["Facil"] * 7 + ["Media"] * 3),
            "facil",
        )
        self.assertEqual(
            clasificar_dificultad_jefe(["Dificil"] * 8 + ["Media"] * 2),
            "dificil",
        )
        self.assertEqual(
            clasificar_dificultad_jefe(["Facil", "Media", "Dificil", "Media"]),
            "equilibrado",
        )

    def test_tamanos_milestone_diez_solo_en_bloque(self) -> None:
        from Comun.escape_room import asignar_tamanos_milestone_por_plantilla
        from Comun.eventos_partida import (
            definicion_materia_con_perfil,
            evento_por_id,
            perfiles_materia_escape_para_sala,
        )
        from Comun.jefe_partida import PREGUNTAS_POR_JEFE
        from Comun.modelos import Pregunta

        perfiles = perfiles_materia_escape_para_sala(20)
        plantillas = (
            (definicion_materia_con_perfil(perfiles[0]), perfiles[0].id),
            (evento_por_id("puerta_grupo"), None),
            (definicion_materia_con_perfil(perfiles[1]), perfiles[1].id),
        )
        pool_pequeno = [
            Pregunta(
                texto=f"p{i}",
                materia="M1" if i < 4 else "M2",
                tematica="",
                dificultad="Dificil",
                tipo="test",
                grupo="2",
                nivel="1",
                curso="1",
                semestre="1",
                opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
                correcta="A",
            )
            for i in range(8)
        ]
        rng = random.Random(7)
        tamanos = asignar_tamanos_milestone_por_plantilla(
            plantillas,
            19,
            pool=pool_pequeno,
            n_salas=30,
            puertas_por_sala=3,
            rng=rng,
        )
        self.assertEqual(len(tamanos), 3)
        self.assertEqual(sum(1 for t in tamanos if t == PREGUNTAS_POR_JEFE), 0)
        for tam in tamanos:
            self.assertIn(tam, (3, 5))

    def test_jefe_itera_foco_hasta_pool_viable(self) -> None:
        from Comun.escape_partida import asegurar_puerta_viable, contar_candidatas_puerta
        from Comun.eventos_partida import (
            EventoContenidoInstanciado,
            ModificadoresPuerta,
            evento_por_id,
        )
        from Comun.escape_room import PuertaEscape
        from Comun.jefe_partida import PREGUNTAS_POR_JEFE
        from Comun.modelos import Pregunta

        pool = [
            Pregunta(
                texto=f"c{i}",
                materia="M1",
                tematica="",
                dificultad="Facil",
                tipo="test",
                grupo="1",
                nivel="1",
                curso="1",
                semestre="1",
                opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
                correcta="A",
            )
            for i in range(12)
        ]
        plantilla = evento_por_id("puerta_curso")
        evento_malo = EventoContenidoInstanciado(definicion=plantilla, curso="9")
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=PREGUNTAS_POR_JEFE,
            modificadores=ModificadoresPuerta(rasgos=("Clásica",)),
            evento=evento_malo,
            es_jefe=True,
        )
        self.assertLess(
            contar_candidatas_puerta(pool, puerta, numero_sala=10, n_salas=30),
            PREGUNTAS_POR_JEFE,
        )
        ajustada = asegurar_puerta_viable(
            pool,
            puerta,
            numero_sala=10,
            n_salas=30,
            indice_puerta=0,
            materias_pool=(),
            rng=random.Random(3),
            pools_bloque={"grupos_pool": (), "cursos_pool": ("1",), "semestres_pool": ("1",), "periodos_pool": (("1", "1"),)},
        )
        self.assertTrue(ajustada.es_jefe)
        self.assertEqual(ajustada.n_preguntas, PREGUNTAS_POR_JEFE)
        self.assertEqual(ajustada.evento.curso, "1")
        self.assertGreaterEqual(
            contar_candidatas_puerta(pool, ajustada, numero_sala=10, n_salas=30),
            PREGUNTAS_POR_JEFE,
        )

    def test_grupo_pequeno_no_admite_jefe_en_milestone(self) -> None:
        from Comun.escape_partida import (
            contar_candidatas_puerta,
            grupos_viables_sala,
            plantilla_bloque_admite_jefe,
        )
        from Comun.eventos_partida import (
            EventoContenidoInstanciado,
            ModificadoresPuerta,
            evento_por_id,
        )
        from Comun.escape_room import PuertaEscape
        from Comun.jefe_partida import PREGUNTAS_POR_JEFE
        from Comun.modelos import Pregunta

        pool = [
            Pregunta(
                texto=f"p{i}",
                materia="M1" if i < 4 else "M2",
                tematica="",
                dificultad="Dificil",
                tipo="test",
                grupo="2",
                nivel="1",
                curso="1",
                semestre="1",
                opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
                correcta="A",
            )
            for i in range(8)
        ]
        self.assertEqual(
            grupos_viables_sala(
                pool, ("2",), numero_sala=10, n_salas=30, min_preguntas=10
            ),
            (),
        )
        plantilla = evento_por_id("puerta_grupo")
        self.assertFalse(
            plantilla_bloque_admite_jefe(
                pool,
                plantilla,
                numero_sala=10,
                n_salas=30,
                min_preguntas=PREGUNTAS_POR_JEFE,
                grupos_pool=("2",),
            )
        )
        evento = EventoContenidoInstanciado(definicion=plantilla, grupo="2")
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=PREGUNTAS_POR_JEFE,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        self.assertLess(
            contar_candidatas_puerta(pool, puerta, numero_sala=10, n_salas=30),
            PREGUNTAS_POR_JEFE,
        )

    def test_milestone_diez_solo_en_puertas_bloque(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.escape_partida import construir_pool_escape, materias_del_pool, puerta_es_jefe
        from Comun.escape_room import config_escape_room, generar_puertas_sala
        from Comun.eventos_partida import PityPuertasEspecialesEscape, plantilla_lleva_perfil_materia
        from Comun.rutas import PATH_PREGUNTAS, resolver_listado_materias
        from Comun.semillas import RngPartida

        materias_meta = cargar_materias(resolver_listado_materias())
        pool = construir_pool_escape(cargar_preguntas(PATH_PREGUNTAS, materias_meta))
        materias_pool = materias_del_pool(pool)
        config = config_escape_room(n_salas=30)
        for semilla in range(200):
            for sala_idx in (9, 19, 29):
                puertas, _ = generar_puertas_sala(
                    config.salas[sala_idx],
                    sala_idx,
                    materias_pool=materias_pool,
                    pool_preguntas=pool,
                    rng=RngPartida.desde_semilla(semilla * 10 + sala_idx),
                    n_salas=30,
                    pity=PityPuertasEspecialesEscape(),
                )
                for p in puertas:
                    if p.n_preguntas == 10 or puerta_es_jefe(p):
                        self.assertFalse(
                            plantilla_lleva_perfil_materia(p.evento.definicion),
                            msg=f"semilla={semilla} sala={sala_idx + 1}",
                        )
                    if plantilla_lleva_perfil_materia(p.evento.definicion):
                        self.assertIn(p.n_preguntas, (3, 5))

    def test_sala_10_tiene_jefe_sin_descanso(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.escape_partida import construir_pool_escape, materias_del_pool, puerta_es_jefe
        from Comun.escape_room import config_escape_room, generar_puertas_sala
        from Comun.eventos_partida import PityPuertasEspecialesEscape, RASGOS_BOTIN_ESCAPE
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia
        from Comun.rutas import PATH_PREGUNTAS, resolver_listado_materias
        from Comun.semillas import RngPartida
        from Comun.tienda_escape import puerta_es_tienda

        materias_meta = cargar_materias(resolver_listado_materias())
        pool = construir_pool_escape(
            cargar_preguntas(PATH_PREGUNTAS, materias_meta)
        )
        materias_pool = materias_del_pool(pool)
        config = config_escape_room(n_salas=30)
        sala = config.salas[9]
        estado = EstadoPartida(
            nombre="t",
            reglas=preset_resistencia(),
            puntos_arcade=500,
            vidas_restantes=3,
        )
        rng = RngPartida.desde_semilla(42)
        puertas, _ = generar_puertas_sala(
            sala,
            9,
            materias_pool=materias_pool,
            pool_preguntas=pool,
            rng=rng,
            n_salas=30,
            pity=PityPuertasEspecialesEscape(salas_sin_descanso=20, salas_sin_tienda=20),
            estado=estado,
            vidas_max=3,
        )
        jefes = [p for p in puertas if puerta_es_jefe(p)]
        self.assertEqual(len(jefes), 1)
        self.assertFalse(any(puerta_es_tienda(p) for p in puertas))
        self.assertFalse(any("descanso" in p.modificadores.eventos_ids for p in puertas))
        self.assertEqual(jefes[0].n_preguntas, 10)
        botines = [
            eid
            for eid in jefes[0].modificadores.eventos_ids
            if eid in RASGOS_BOTIN_ESCAPE
        ]
        self.assertGreaterEqual(len(botines), 2)

    def test_sala_20_y_30_conteo_jefes(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.escape_partida import construir_pool_escape, materias_del_pool, puerta_es_jefe
        from Comun.escape_room import PUERTAS_POR_SALA, config_escape_room, generar_puertas_sala
        from Comun.eventos_partida import PityPuertasEspecialesEscape
        from Comun.rutas import PATH_PREGUNTAS, resolver_listado_materias
        from Comun.semillas import RngPartida

        materias_meta = cargar_materias(resolver_listado_materias())
        pool = construir_pool_escape(cargar_preguntas(PATH_PREGUNTAS, materias_meta))
        materias_pool = materias_del_pool(pool)
        config = config_escape_room(n_salas=30)
        pity = PityPuertasEspecialesEscape()
        for sala_idx, esperado in ((19, 2), (29, 3)):
            puertas, _ = generar_puertas_sala(
                config.salas[sala_idx],
                sala_idx,
                materias_pool=materias_pool,
                pool_preguntas=pool,
                rng=RngPartida.desde_semilla(100 + sala_idx),
                n_salas=30,
                pity=pity,
            )
            jefes = [p for p in puertas if puerta_es_jefe(p)]
            self.assertEqual(len(jefes), esperado)
            self.assertEqual(len(puertas), PUERTAS_POR_SALA)
            normales = [p for p in puertas if not puerta_es_jefe(p)]
            self.assertTrue(all(p.n_preguntas in (3, 5) for p in normales))
            for j in jefes:
                from Comun.eventos_partida import plantilla_lleva_perfil_materia

                self.assertFalse(plantilla_lleva_perfil_materia(j.evento.definicion))

    def test_milestone_icono_corona_por_diez_preguntas(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.emojis_escape import EMOJI_JEFE
        from Comun.escape_partida import construir_pool_escape, materias_del_pool
        from Comun.escape_room import config_escape_room, generar_puertas_sala
        from Comun.eventos_partida import PityPuertasEspecialesEscape, iconos_efecto_puerta
        from Comun.jefe_partida import n_puertas_jefe_en_sala
        from Comun.rutas import PATH_PREGUNTAS, resolver_listado_materias
        from Comun.semillas import RngPartida

        materias_meta = cargar_materias(resolver_listado_materias())
        pool = construir_pool_escape(cargar_preguntas(PATH_PREGUNTAS, materias_meta))
        materias_pool = materias_del_pool(pool)
        config = config_escape_room(n_salas=50)
        pity = PityPuertasEspecialesEscape(salas_sin_descanso=99, salas_sin_tienda=99)

        for sala_idx in (9, 19, 29, 39):
            numero_sala = sala_idx + 1
            puertas, _ = generar_puertas_sala(
                config.salas[sala_idx],
                sala_idx,
                materias_pool=materias_pool,
                pool_preguntas=pool,
                rng=RngPartida.desde_semilla(200 + sala_idx),
                n_salas=50,
                pity=pity,
            )
            coronas = sum(
                1
                for p in puertas
                if EMOJI_JEFE
                in [
                    ic.emoji
                    for ic in iconos_efecto_puerta(
                        evento=p.evento,
                        modificadores=p.modificadores,
                        n_preguntas=p.n_preguntas,
                        rng=RngPartida.desde_semilla(0),
                    )
                ]
            )
            self.assertEqual(coronas, n_puertas_jefe_en_sala(numero_sala), msg=f"sala {numero_sala}")

        puertas_5, _ = generar_puertas_sala(
            config.salas[4],
            4,
            materias_pool=materias_pool,
            pool_preguntas=pool,
            rng=RngPartida.desde_semilla(99),
            n_salas=50,
            pity=pity,
        )
        for p in puertas_5:
            iconos = iconos_efecto_puerta(
                evento=p.evento,
                modificadores=p.modificadores,
                n_preguntas=p.n_preguntas,
                rng=RngPartida.desde_semilla(0),
            )
            self.assertNotIn(EMOJI_JEFE, [ic.emoji for ic in iconos])

    def test_resistencia_recompensa_jefe_garantizada(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia
        from Comun.resistencia_motor import (
            EstadoResistencia,
            recompensas_completar_jefe_resistencia,
        )

        estado = EstadoPartida(
            nombre="t",
            reglas=preset_resistencia(),
            vidas_restantes=2,
            puntos_arcade=0,
        )
        er = EstadoResistencia(vidas_max=3, semilla_partida=1)
        recompensas = recompensas_completar_jefe_resistencia(er, estado, numero_pregunta=20)
        self.assertGreaterEqual(len(recompensas), 3)
        self.assertTrue(any(r.delta_vidas or r.delta_vidas_max for r in recompensas))
        self.assertGreaterEqual(
            sum(1 for r in recompensas if r.powerup_id),
            2,
        )

    def test_resistencia_hard_pity_jefe(self) -> None:
        from Comun.jefe_partida import (
            PREGUNTA_MIN_JEFE_RESISTENCIA,
            PREGUNTAS_HARD_PITY_JEFE_RESISTENCIA,
            debe_forzar_jefe_resistencia,
        )

        self.assertGreaterEqual(PREGUNTA_MIN_JEFE_RESISTENCIA, 15)
        self.assertTrue(debe_forzar_jefe_resistencia(PREGUNTAS_HARD_PITY_JEFE_RESISTENCIA))
        self.assertFalse(debe_forzar_jefe_resistencia(5))

    def test_resistencia_jefe_no_antes_del_minimo(self) -> None:
        from Comun.modelos import Pregunta
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia
        from Comun.resistencia_motor import (
            EstadoResistencia,
            _intentar_activar_jefe_resistencia,
            configurar_partida_resistencia,
        )
        from Comun.jefe_partida import PREGUNTA_MIN_JEFE_RESISTENCIA

        pool = [
            Pregunta(
                texto="Q",
                materia="Física",
                tematica="",
                dificultad="Media",
                tipo="Teoria",
                grupo="10",
                nivel="1",
                curso="1",
                semestre="1",
                correcta="A",
                opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
            )
        ]
        estado = EstadoPartida(nombre="T", reglas=preset_resistencia(), vidas_restantes=3)
        er = EstadoResistencia()
        configurar_partida_resistencia(er, preset_id="resistencia")
        er.preguntas_sin_jefe = 99
        aviso = _intentar_activar_jefe_resistencia(
            pool,
            PREGUNTA_MIN_JEFE_RESISTENCIA - 1,
            er,
        )
        self.assertIsNone(aviso)
        self.assertIsNone(er.bloque_filtro)

    def test_jefe_visible_en_barra_y_aviso(self) -> None:
        from Comun.emojis_escape import EMOJI_JEFE
        from Comun.resistencia_motor import (
            BloqueFiltroActivo,
            EstadoResistencia,
            formatear_aviso_botin_jefe_resistencia,
            formatear_aviso_jefe,
            segmento_bloque_filtro_barra,
            texto_bloque_filtro_extra,
        )
        from Comun.linea_estado_ui import segmentos_linea_estado
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import preset_resistencia

        er = EstadoResistencia()
        er.bloque_filtro = BloqueFiltroActivo(
            etiqueta="Jefe: 10 preguntas Modelización física (medio)",
            preguntas_restantes=10,
            preguntas_totales=10,
            grupo="10",
            es_jefe=True,
            dificultad_jefe="medio",
        )
        aviso = formatear_aviso_jefe(er.bloque_filtro.etiqueta)
        self.assertIn("Enfrentamiento con jefe", aviso)
        self.assertIn(EMOJI_JEFE, aviso)
        self.assertEqual(segmento_bloque_filtro_barra(er), "Jefe 1/10")
        extra = texto_bloque_filtro_extra(er)
        self.assertIsNotNone(extra)
        assert extra is not None
        self.assertIn("Jefe activo", extra)
        estado = EstadoPartida(nombre="t", reglas=preset_resistencia(), vidas_restantes=3)
        segs = segmentos_linea_estado(
            estado,
            "",
            numero_pregunta=25,
            bloque_filtro_texto="Jefe 3/10",
        )
        progreso_puerta = next(s for s in segs if s.id == "pregunta_puerta")
        self.assertEqual(progreso_puerta.emoji, EMOJI_JEFE)

    def test_botin_jefe_un_solo_aviso(self) -> None:
        from Comun.resistencia_motor import (
            EventoRecompensaResistencia,
            formatear_aviso_botin_jefe_resistencia,
        )

        recompensas = [
            EventoRecompensaResistencia("Botín de jefe: +1 vida", delta_vidas=1),
            EventoRecompensaResistencia("Botín de jefe: Bomba", powerup_id="bomba"),
            EventoRecompensaResistencia("Botín de jefe: Skip", powerup_id="skip"),
            EventoRecompensaResistencia(
                "Botín de jefe: amuleto arcade",
                bonus_proximo_acierto=40,
            ),
        ]
        aviso = formatear_aviso_botin_jefe_resistencia(recompensas)
        self.assertIn("Jefe derrotado", aviso)
        self.assertIn("Bomba", aviso)
        self.assertIn("Saltar", aviso)

    def test_elegir_powerup_loot_prefiere_variedad(self) -> None:
        from Comun.objetos_partida import elegir_powerup_loot

        inv = {"bomba": 8}
        rng = random.Random(0)
        elegidos = {elegir_powerup_loot(inv, rng) for _ in range(40)}
        self.assertGreater(len(elegidos), 1)
        contador = {pid: 0 for pid in elegidos}
        for _ in range(200):
            pid = elegir_powerup_loot(inv, random.Random())
            contador[pid] = contador.get(pid, 0) + 1
        if "bomba" in contador:
            otros = [c for p, c in contador.items() if p != "bomba"]
            if otros:
                self.assertGreater(max(otros), contador.get("bomba", 0) // 3)


if __name__ == "__main__":
    unittest.main()
