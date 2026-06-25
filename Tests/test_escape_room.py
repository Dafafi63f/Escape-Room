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
    delta_vidas_descanso_entrada,
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
    RolEscape,
    combinar_modificadores_puerta,
    evento_por_id,
    eventos_contenido_escape_para_sala,
    eventos_puerta_escape_para_sala,
    instanciar_evento_contenido,
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
        self.assertIn("solo_facil", contenido_ids)
        self.assertNotIn("relampago", puerta_ids)
        self.assertNotIn("relampago", contenido_ids)
        self.assertNotIn("solo_facil", puerta_ids)
        self.assertIsNone(evento_por_id("relampago").rol_escape)
        self.assertIsNotNone(evento_por_id("solo_facil").rol_escape)

    def test_config_tiene_30_salas(self) -> None:
        self.assertEqual(self.config.n_salas, SALAS_DEFECTO)
        self.assertEqual(len(self.config.salas), 30)
        self.assertEqual(self.config.puertas_por_sala, PUERTAS_POR_SALA)

    def test_generar_tres_puertas_distintas(self) -> None:
        sala = self.config.salas[0]
        puertas = generar_puertas_sala(
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
        ids = {p.evento.id for p in con_preguntas}
        self.assertEqual(len(ids), len(con_preguntas))
        materias = {p.evento.materia for p in con_preguntas if p.evento.materia}
        self.assertEqual(len(materias), len(con_preguntas))

    def test_salas_distintas_con_misma_semilla_base(self) -> None:
        firmas: set[tuple] = set()
        for idx in range(5):
            puertas = generar_puertas_sala(
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
                puertas = generar_puertas_sala(
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

    def test_catalogo_contenido_ampliado_sala_1(self) -> None:
        ids = {e.id for e in eventos_contenido_escape_para_sala(1)}
        self.assertIn("solo_media", ids)
        self.assertIn("pregunta_unica", ids)
        self.assertIn("mix_facil_media", ids)
        self.assertNotIn("materia_sorpresa", ids)
        self.assertNotIn("asignatura", ids)

    def test_rasgos_tiempo_puerta_escape(self) -> None:
        from Comun.eventos_partida import RASGOS_TIEMPO_PUERTA_ESCAPE, eventos_puerta_escape_para_sala

        ids_sala_30 = {e.id for e in eventos_puerta_escape_para_sala(30)}
        self.assertLessEqual(RASGOS_TIEMPO_PUERTA_ESCAPE, ids_sala_30)
        for eid in RASGOS_TIEMPO_PUERTA_ESCAPE:
            ev = evento_por_id(eid)
            self.assertEqual(ev.rol_escape, RolEscape.PUERTA)
            m = ev.modificadores
            self.assertTrue(
                m.tiempo_pregunta_seg is not None or m.tiempo_puerta_seg is not None,
                msg=eid,
            )
        ids_sala_3 = {e.id for e in eventos_puerta_escape_para_sala(3)}
        self.assertNotIn("cronometro_pregunta", ids_sala_3)

    def test_rasgos_niebla_solo_salas_avanzadas(self) -> None:
        from Comun.eventos_partida import (
            RASGOS_ENUNCIADO_PUERTA_ESCAPE,
            RASGOS_OPCIONES_PUERTA_ESCAPE,
            eventos_puerta_escape_para_sala,
        )

        niebla_ids = RASGOS_ENUNCIADO_PUERTA_ESCAPE | RASGOS_OPCIONES_PUERTA_ESCAPE
        ids_temprano = {e.id for e in eventos_puerta_escape_para_sala(11)}
        self.assertNotIn("bruma_leve", ids_temprano)
        self.assertFalse(niebla_ids & ids_temprano)
        ids_sala_12 = {e.id for e in eventos_puerta_escape_para_sala(12)}
        self.assertIn("bruma_leve", ids_sala_12)
        self.assertNotIn(
            "niebla_enunciado",
            {e.id for e in eventos_puerta_escape_para_sala(15)},
        )
        self.assertIn(
            "niebla_enunciado",
            {e.id for e in eventos_puerta_escape_para_sala(16)},
        )

    def test_rasgos_puerta_desde_catalogo_comun(self) -> None:
        cronometro = evento_por_id("cronometro_pregunta")
        niebla = evento_por_id("niebla_enunciado")
        self.assertEqual(cronometro.rol_escape, RolEscape.PUERTA)
        mods = combinar_modificadores_puerta((cronometro, niebla))
        self.assertEqual(mods.tiempo_pregunta_seg, 35)
        self.assertEqual(mods.fraccion_enunciado, 0.45)

    def test_generar_puerta_rasgos_exclusivos_no_se_combinan(self) -> None:
        from Comun.eventos_partida import (
            RASGOS_ENUNCIADO_PUERTA_ESCAPE,
            RASGOS_MULTIPLICADOR_PUERTA_ESCAPE,
            RASGOS_OPCIONES_PUERTA_ESCAPE,
            RASGOS_TIEMPO_PUERTA_ESCAPE,
            generar_modificadores_puerta,
        )

        familias = (
            RASGOS_TIEMPO_PUERTA_ESCAPE,
            RASGOS_MULTIPLICADOR_PUERTA_ESCAPE,
            RASGOS_ENUNCIADO_PUERTA_ESCAPE,
            RASGOS_OPCIONES_PUERTA_ESCAPE,
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
                evento_por_id("arriesgado"),
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
        from Comun.eventos_partida import iconos_efecto_puerta

        materia = self.materias_pool[0]
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("solo_facil"),
            materia=materia,
        )
        mods = combinar_modificadores_puerta(
            (evento_por_id("cronometro_pregunta"), evento_por_id("niebla_enunciado"))
        )
        iconos = iconos_efecto_puerta(
            evento=evento,
            modificadores=mods,
            n_preguntas=4,
        )
        self.assertEqual(len(iconos), 4)
        self.assertEqual(iconos[0].emoji, "⏱️")
        self.assertEqual(iconos[1].emoji, "🌫️")
        self.assertEqual(iconos[2].emoji, "🔢")
        self.assertEqual(iconos[3].emoji, "🟢")
        self.assertIn("35 s", iconos[0].tooltip)
        self.assertIn("45%", iconos[1].tooltip)
        self.assertIn("4 preguntas", iconos[2].tooltip)
        self.assertIn("Facil", iconos[3].tooltip)

    def test_iconos_dificultad_unificados(self) -> None:
        from Comun.eventos_partida import iconos_contenido_puerta

        materia = self.materias_pool[0]

        def icono_dif(ev_id: str) -> str:
            ev = EventoContenidoInstanciado(
                definicion=evento_por_id(ev_id),
                materia=materia,
            )
            iconos = iconos_contenido_puerta(ev)
            return iconos[0].emoji

        self.assertEqual(icono_dif("solo_facil"), "🟢")
        self.assertEqual(icono_dif("solo_media"), "🟡")
        self.assertEqual(icono_dif("solo_dificil"), "🔴")
        self.assertEqual(icono_dif("mix_facil_media"), "🎁")
        self.assertEqual(icono_dif("mezcla_media_dificil"), "🎁")
        self.assertEqual(icono_dif("pregunta_unica"), "⚖️")
        self.assertEqual(
            icono_dif("solo_teoria"),
            "📐",
        )

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
        puertas = generar_puertas_sala(
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
                (evento_por_id("cronometro_pregunta"),)
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
        self.assertEqual(reglas.tiempo_pregunta_seg, 35)

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
                (evento_por_id("cronometro_pregunta"),)
            ),
            evento=evento,
        )
        reglas = reglas_juego_desafio(puerta, numero_sala=20, n_salas=30)
        self.assertEqual(reglas.tiempo_pregunta_seg, 35)
        partida = reglas_partida_desde_desafio(preset_escape(), reglas)
        self.assertEqual(partida.tiempo_por_pregunta_seg, 35)
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
            vidas_max=4,
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
            vidas_max=4,
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
            (evento_por_id("descanso"), evento_por_id("niebla_enunciado"))
        )
        self.assertEqual(mods_niebla.eventos_ids, ("descanso",))
        self.assertEqual(mods_niebla.fraccion_enunciado, 1.0)
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
                            "niebla_enunciado",
                            "cronometro_pregunta",
                            "doble_puntos",
                        },
                    )

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
        self.assertEqual(delta_vidas_descanso_entrada(puerta), 0)
        self.assertEqual(bonificacion_completar_escape(puerta).delta_vidas, 1)

    def test_respiro_da_vida_al_entrar(self) -> None:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("pregunta_unica"),
            materia=self.materias_pool[0],
        )
        mods = combinar_modificadores_puerta((evento_por_id("respiro"),))
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=0,
            modificadores=mods,
            evento=evento,
        )
        self.assertEqual(delta_vidas_descanso_entrada(puerta), 1)
        self.assertEqual(bonificacion_completar_escape(puerta).delta_vidas, 0)

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
        self.assertEqual(delta_vidas_descanso_entrada(puerta), 0)
        self.assertEqual(bonificacion_completar_escape(puerta).delta_vidas, 0)

    def test_descanso_sin_bonificacion_al_completar(self) -> None:
        """Alias de test_descanso_sin_vida_ni_bonificacion (compatibilidad)."""
        self.test_descanso_sin_vida_ni_bonificacion()

    def test_combinar_respiro_solo_admite_botin(self) -> None:
        mods = combinar_modificadores_puerta(
            (
                evento_por_id("respiro"),
                evento_por_id("niebla_enunciado"),
                evento_por_id("botin"),
            )
        )
        self.assertEqual(set(mods.eventos_ids), {"respiro", "botin"})

    def test_aplicar_bonificacion_respeta_tope(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas_partida import preset_escape

        estado = EstadoPartida(
            nombre="t",
            reglas=preset_escape(),
            vidas_restantes=4,
        )
        ganadas = aplicar_bonificacion_completar(
            estado,
            BonificacionCompletarEscape(delta_vidas=2),
        )
        self.assertEqual(ganadas, 0)
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


if __name__ == "__main__":
    unittest.main()
