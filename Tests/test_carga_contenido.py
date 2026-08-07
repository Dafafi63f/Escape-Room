#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga portable del juego con CSV mínimo."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.contenido import es_csv_minimal, leer_cabeceras_csv
from Comun.contenido import (  # noqa: E402
    cargar_contenido_juego,
    construir_datos_juego,
)
from Comun.contenido import evaluar_requisitos_completo  # noqa: E402
from Comun.rutas import PATH_PREGUNTAS, resolver_plantillas  # noqa: E402
from Grafico.pantallas import MenuPrincipal  # noqa: E402
from Grafico.pantallas_libre import ConfigOpcionesLibre  # noqa: E402

_FIXTURE = Path(__file__).resolve().parents[1] / "Data" / "Privado" / "Preguntas_minimal.csv"


class TestCargaContenidoPortable(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import pygame

        pygame.init()
        pygame.display.set_mode((800, 600))

    @classmethod
    def tearDownClass(cls) -> None:
        import pygame

        from Grafico.fuentes import invalidar_cache_fuentes

        invalidar_cache_fuentes()
        if pygame.get_init():
            pygame.quit()

    def test_fixture_es_csv_minimal(self) -> None:
        self.assertTrue(_FIXTURE.is_file())
        cabeceras = leer_cabeceras_csv(_FIXTURE)
        self.assertTrue(es_csv_minimal(cabeceras))

    def test_carga_solo_csv_minimal(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.rutas import PATH_MATERIAS, PATH_PREGUNTAS

        materias_meta = cargar_materias(PATH_MATERIAS)
        n_banco_completo = len(cargar_preguntas(PATH_PREGUNTAS, materias_meta))
        contenido = cargar_contenido_juego(path_csv=_FIXTURE)
        self.assertTrue(contenido.perfil.solo_csv)
        self.assertTrue(contenido.perfil.modo_minimo)
        self.assertTrue(contenido.perfil.csv_minimal)
        self.assertEqual(len(contenido.preguntas), n_banco_completo)
        self.assertIsNone(contenido.path_plantillas_json)
        self.assertFalse(contenido.perfil.modo_historia_disponible)
        self.assertTrue(contenido.perfil.examen_fijo_barra_completo)
        self.assertTrue(contenido.perfil.modos_especiales_disponibles)
        self.assertFalse(contenido.perfil.banco_beta_disponible)
        self.assertFalse(contenido.perfil.filtros_libre_disponibles)
        self.assertFalse(contenido.perfil.mostrar_metadatos_pregunta)
        self.assertTrue(contenido.perfil.modos_diarios_disponibles)

    def test_datos_juego_desde_csv_minimal(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.rutas import PATH_MATERIAS, PATH_PREGUNTAS

        materias_meta = cargar_materias(PATH_MATERIAS)
        n_banco = len(cargar_preguntas(PATH_PREGUNTAS, materias_meta))
        datos = construir_datos_juego(cargar_contenido_juego(path_csv=_FIXTURE))
        self.assertEqual(datos.num_preguntas, n_banco)
        self.assertTrue(all(p.texto for p in datos.preguntas))
        self.assertTrue(all(p.opciones.values() for p in datos.preguntas))

    def test_csv_minimal_sin_placeholders_curriculares(self) -> None:
        contenido = cargar_contenido_juego(path_csv=_FIXTURE)
        muestra = contenido.preguntas[:20]
        self.assertTrue(muestra)
        for p in muestra:
            self.assertEqual(p.materia, "")
            self.assertEqual(p.grupo, "")
            self.assertEqual(p.curso, "")
            # Tipo/temática pueden salir de heurística; dificultad solo tras estadísticas.
            if p.dificultad:
                self.assertIn(p.dificultad, {"Facil", "Media", "Dificil"})

    def test_menu_principal_modos_minimo(self) -> None:
        datos = construir_datos_juego(cargar_contenido_juego(path_csv=_FIXTURE))
        menu = MenuPrincipal(datos, lambda _p: None, lambda: None)
        for opcion, boton in zip(menu.OPCIONES, menu.botones, strict=True):
            if opcion.id == "historia":
                self.assertFalse(boton.activo)
            if opcion.id == "especiales":
                self.assertTrue(boton.activo)
        self.assertTrue(datos.perfil.examen_fijo_barra_completo)
        self.assertTrue(datos.perfil.modos_diarios_disponibles)
        self.assertIn("mínimo", menu.mensaje.lower())

    def test_historia_portable_carrusel_vacio(self) -> None:
        from Comun.presets_historia import PRESETS_HISTORIA_PORTABLE, cargar_presets_historia
        from Comun.rutas import resolver_presets
        from Grafico.modo_historia import cargar_catalogo_historia

        contenido = cargar_contenido_juego(path_csv=_FIXTURE)
        presets = cargar_catalogo_historia(contenido.perfil)
        self.assertEqual(presets, [])
        self.assertEqual(PRESETS_HISTORIA_PORTABLE, frozenset())
        todos = cargar_presets_historia(resolver_presets())
        self.assertGreater(len(todos), 0)

    def test_especiales_portable_muestra_escape_inactivo(self) -> None:
        from Comun.presets_historia import cargar_presets_especiales
        from Comun.rutas import resolver_presets
        from Grafico.pantallas_modos import cargar_catalogo_especiales
        from Grafico.pantallas_modos import ConfigModosEspeciales

        contenido = cargar_contenido_juego(path_csv=_FIXTURE)
        presets = cargar_catalogo_especiales(contenido.perfil)
        self.assertEqual({p.id for p in presets}, {"escape_room", "resistencia"})
        self.assertFalse(contenido.perfil.modo_especial_disponible("escape_room"))
        self.assertTrue(contenido.perfil.modo_especial_disponible("resistencia"))
        todos = cargar_presets_especiales(resolver_presets())
        self.assertEqual(len(todos), len(presets))

        pantalla = ConfigModosEspeciales(
            construir_datos_juego(contenido),
            lambda _p: None,
            lambda: None,
        )
        por_id = {p.id: b for p, b in zip(pantalla.presets, pantalla.botones_modo, strict=True)}
        self.assertFalse(por_id["escape_room"].activo)
        self.assertTrue(por_id["resistencia"].activo)

    def test_resistencia_portable_sin_filtro_dificultad(self) -> None:
        from Comun.modelos import Pregunta
        from Comun.perfil_contenido import PerfilContenido
        from Comun.preguntas_resistencia import construir_banco_resistencia
        from Comun.resistencia_motor import EstadoResistencia, configurar_partida_resistencia
        from Comun.resistencia_partida import (
            baseline_escalada_resistencia,
            crear_seleccion_resistencia,
            elegir_indice_resistencia,
            escalada_para_pregunta,
        )

        pool = [
            Pregunta(
                texto="¿Test?",
                materia="",
                tematica="",
                dificultad="",
                tipo="",
                grupo="",
                nivel="",
                curso="",
                semestre="",
                opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
                correcta="A",
            )
        ]
        banco = construir_banco_resistencia(pool, {"": {}})
        er = EstadoResistencia()
        er.banco_resistencia = banco
        configurar_partida_resistencia(
            er, preset_id="resistencia", sin_escalada_dificultad=True
        )
        base = baseline_escalada_resistencia(50, solo_eventos=True)
        self.assertEqual(base.efectos, ())
        esc = escalada_para_pregunta(50, er=er)
        sel = crear_seleccion_resistencia(pool)
        idx = elegir_indice_resistencia(pool, sel, esc, numero_pregunta=50, er=er)
        self.assertEqual(idx, 0)
        perfil = PerfilContenido(modo_minimo=True, tiene_presets=True)
        self.assertTrue(perfil.resistencia_solo_eventos)

    def test_modo_libre_sin_paso_filtros(self) -> None:
        datos = construir_datos_juego(cargar_contenido_juego(path_csv=_FIXTURE))
        cfg = ConfigOpcionesLibre(datos, lambda _p: None, lambda: None)
        self.assertNotIn("banco", cfg._filas_visibles())
        self.assertEqual(cfg.boton_siguiente.etiqueta.split()[0], "Empezar")

    def test_examen_fijo_csv_minimal_genera_24_preguntas(self) -> None:
        from Comun.presets_historia import argumentos_generador, buscar_preset, config_defecto
        from Comun.generador_examen_historia import generar_examen
        from Comun.modos_diarios import semilla_examen_dia
        from Grafico.modo_historia import orden_materias_juego, preparar_partida_historia
        from Grafico.pantallas_examen_fijo import ConfigOpcionesHistoria
        from Grafico.pantallas_modos import abrir_config_examen_fijo

        datos = construir_datos_juego(cargar_contenido_juego(path_csv=_FIXTURE))
        preset = buscar_preset("examen_fijo")
        cfg = config_defecto(
            preset,
            materias_meta=datos.materias_meta,
            materias_orden=orden_materias_juego(datos),
            perfil=datos.perfil,
        )
        kwargs = argumentos_generador(
            preset, cfg, materias_meta=datos.materias_meta, perfil_datos=datos.perfil
        )
        self.assertTrue(kwargs["seleccion_plana"])
        self.assertEqual(kwargs["n_preguntas"], 24)

        plan, _reglas = preparar_partida_historia(datos, preset, cfg)
        self.assertEqual(len(plan.preguntas), 24)

        semilla_dia = semilla_examen_dia()
        textos_a = tuple(
            p.texto
            for p in generar_examen(
                datos.preguntas,
                materias_orden=orden_materias_juego(datos),
                materias_meta=datos.materias_meta,
                semilla=1,
                semilla_contenido=semilla_dia,
                **kwargs,
            ).preguntas
        )
        textos_b = tuple(
            p.texto
            for p in generar_examen(
                datos.preguntas,
                materias_orden=orden_materias_juego(datos),
                materias_meta=datos.materias_meta,
                semilla=2,
                semilla_contenido=semilla_dia,
                **kwargs,
            ).preguntas
        )
        self.assertEqual(set(textos_a), set(textos_b))

        destino: list = []

        def ir_a(pantalla) -> None:
            destino.append(pantalla)

        abrir_config_examen_fijo(datos, ir_a, lambda: None)
        self.assertEqual(len(destino), 1)
        pantalla = destino[0]
        self.assertIsInstance(pantalla, ConfigOpcionesHistoria)
        self.assertEqual(pantalla.preset.id, "examen_fijo")
        opciones = {op.id for op in pantalla._opciones_ui()}
        self.assertEqual(opciones, {"origen_semilla", "semilla", "estrategia_practica"})
        self.assertTrue(pantalla._filtro_ambito_bloqueado("semilla"))
        pantalla.config.valores["origen_semilla"] = "semilla"
        pantalla._sync_campo_semilla_desde_config()
        self.assertFalse(pantalla._filtro_ambito_bloqueado("semilla"))

    def test_examen_dirigido_csv_minimal_genera_otro_test(self) -> None:
        from Comun.informe_examen import RegistroRespuesta
        from Comun.presets_historia import argumentos_generador, buscar_preset, config_defecto
        from Grafico.modo_historia import (
            orden_materias_juego,
            preparar_examen_dirigido_sesion,
            preparar_partida_historia,
        )

        datos = construir_datos_juego(cargar_contenido_juego(path_csv=_FIXTURE))
        preset = buscar_preset("examen_fijo")
        cfg = config_defecto(
            preset,
            materias_meta=datos.materias_meta,
            materias_orden=orden_materias_juego(datos),
            perfil=datos.perfil,
        )
        kwargs = argumentos_generador(
            preset, cfg, materias_meta=datos.materias_meta, perfil_datos=datos.perfil
        )
        self.assertTrue(kwargs["seleccion_plana"])

        plan_inicial, _ = preparar_partida_historia(datos, preset, cfg)
        registros = [
            RegistroRespuesta(i + 1, p, "B", False)
            for i, p in enumerate(plan_inicial.preguntas[:8])
        ]
        plan_dirigido, _reglas, cadena = preparar_examen_dirigido_sesion(
            datos, preset, cfg, registros
        )
        self.assertEqual(len(plan_dirigido.preguntas), 24)
        self.assertEqual(cadena.n_sesiones, 1)
        self.assertNotEqual(
            tuple(p.texto for p in plan_inicial.preguntas),
            tuple(p.texto for p in plan_dirigido.preguntas),
        )

    def test_csv_curricular_rechazado_con_flag(self) -> None:
        from Comun.rutas import PATH_PREGUNTAS

        with self.assertRaises(ValueError) as ctx:
            cargar_contenido_juego(path_csv=PATH_PREGUNTAS)
        self.assertIn("no admitido", str(ctx.exception).lower())

    def test_listado_junto_csv_ignorado_en_minimo(self) -> None:
        from Comun.rutas import PATH_MATERIAS

        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            csv_path = raiz / "Preguntas.csv"
            shutil.copy(_FIXTURE, csv_path)
            shutil.copy(PATH_MATERIAS, raiz / "listado_materias.csv")
            contenido = cargar_contenido_juego(path_csv=csv_path)
        self.assertTrue(contenido.perfil.modo_minimo)
        self.assertIsNone(contenido.path_listado_materias)
        self.assertFalse(contenido.perfil.filtros_libre_disponibles)

    def test_evaluar_requisitos_completo_en_repo(self) -> None:
        resultado = evaluar_requisitos_completo()
        self.assertTrue(resultado.completo, resultado.faltas)
        self.assertEqual(resultado.avisos, ())
        self.assertNotIn("plantillas.json", resultado.faltas)

    def test_carga_completa_sin_regression(self) -> None:
        contenido = cargar_contenido_juego()
        self.assertFalse(contenido.perfil.solo_csv)
        self.assertFalse(contenido.perfil.modo_minimo)
        self.assertTrue(contenido.perfil.paquete_completo)
        self.assertGreater(len(contenido.preguntas), 100)
        self.assertIsNotNone(contenido.path_plantillas_json)
        self.assertTrue(contenido.perfil.modo_historia_disponible)
        self.assertTrue(contenido.perfil.modos_diarios_disponibles)
        self.assertIsNotNone(contenido.path_listado_materias)
        self.assertEqual(contenido.path_preguntas_csv, PATH_PREGUNTAS)
        self.assertEqual(contenido.path_plantillas_json, resolver_plantillas())

    def test_paquete_minimo_aislado_sin_datos_externos(self) -> None:
        from Comun.rutas import resolver_presets

        presets_repo = resolver_presets()
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / "MATCAD_minimal"
            raiz.mkdir()
            (raiz / ".matcad-paquete-minimo").write_text("ok\n", encoding="utf-8")
            data = raiz / "Data"
            data.mkdir()
            shutil.copy(_FIXTURE, data / "Preguntas.csv")
            cwd_prev = Path.cwd()
            try:
                import os

                os.chdir(raiz)
                contenido = cargar_contenido_juego()
            finally:
                os.chdir(cwd_prev)
        self.assertEqual(contenido.perfil.tipo_paquete, "minimo")
        self.assertFalse(contenido.perfil.tiene_presets)
        self.assertFalse(contenido.perfil.modos_diarios_disponibles)
        self.assertEqual(contenido.avisos_carga, ())
        self.assertNotEqual(
            contenido.path_preguntas_csv.resolve(),
            presets_repo.resolve().parent,
        )

    def test_paquete_minimo_detectado_sin_marcador(self) -> None:
        from Comun import rutas
        from Comun.contenido import detectar_tipo_paquete
        from Comun.rutas import resolver_presets

        presets_origen = resolver_presets()
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / "MATCAD_minimal"
            juego = raiz / "Juego"
            juego.mkdir(parents=True)
            data = raiz / "Data"
            data.mkdir(parents=True)
            shutil.copy(_FIXTURE, data / "Preguntas.csv")
            shutil.copy(presets_origen, juego / "presets.json")
            cwd_prev = Path.cwd()
            try:
                import os

                os.chdir(raiz)
                with patch.object(rutas, "_JUEGO_DIR", juego):
                    self.assertEqual(detectar_tipo_paquete(), "minimo")
                    contenido = cargar_contenido_juego()
            finally:
                os.chdir(cwd_prev)
        self.assertEqual(contenido.perfil.tipo_paquete, "minimo")
        self.assertTrue(contenido.perfil.tiene_presets)

    def test_zip_minimal_una_sola_carpeta_contenedora(self) -> None:
        """El zip no debe anidar MATCAD_minimal/MATCAD_minimal/ al descomprimir."""
        import zipfile

        zip_path = Path(__file__).resolve().parents[1] / "Juego" / "Distribucion" / "MATCAD_juego_minimal.zip"
        if not zip_path.is_file():
            self.skipTest(f"No existe {zip_path}; ejecuta crear_zip_minimal.py")

        with zipfile.ZipFile(zip_path) as zf:
            nombres = zf.namelist()
            presets = json.loads(zf.read("Juego/presets.json").decode("utf-8"))

        prohibidos = ("MATCAD_minimal/", "MATCAD_minimal\\")
        for nombre in nombres:
            self.assertFalse(
                nombre.startswith(prohibidos),
                f"Carpeta anidada prohibida en el zip: {nombre}",
            )

        raices = {n.split("/")[0] for n in nombres}
        self.assertIn("Jugar.bat", nombres)
        self.assertIn("Juego", raices)
        self.assertIn("Data/Preguntas.csv", nombres)
        self.assertNotIn("Preguntas.csv", nombres)
        self.assertFalse(any(n.startswith("Data/Banco/") for n in nombres))
        self.assertFalse(any(n.startswith("Data/Juego/") for n in nombres))
        self.assertFalse(any(n.startswith("Data/Privado/") for n in nombres))
        self.assertIn("Juego/CHANGELOG_JUEGO.md", nombres)
        self.assertFalse(any(n.startswith("Docs/") for n in nombres))
        from Comun.contenido import MODULOS_EXCLUIDOS_MINIMO

        for rel in MODULOS_EXCLUIDOS_MINIMO:
            ruta_zip = f"Juego/{rel}"
            self.assertNotIn(
                ruta_zip,
                nombres,
                f"El zip mínimo no debe incluir {ruta_zip}",
            )
        self.assertEqual({p["id"] for p in presets["presets"]}, {"examen_fijo"})

    def test_zip_portable_iterador_excluye_scripts_y_distribucion(self) -> None:
        from Docs.utilidades_distribucion import _iterar_ficheros_zip_portable

        archivos = {arc for _, arc in _iterar_ficheros_zip_portable()}
        self.assertIn("Juego/juego_grafico.py", archivos)
        self.assertIn("Juego/Comun/rutas.py", archivos)
        self.assertIn("Juego/Grafico/app.py", archivos)
        self.assertFalse(any(a.startswith("Juego/Scripts/") for a in archivos))
        self.assertFalse(any(a.startswith("Juego/Distribucion/") for a in archivos))

    def test_zip_portable_cubre_juego_y_data(self) -> None:
        """El zip completo incluye Data/ y Juego/ jugable (sin Scripts/ ni Distribucion/)."""
        import zipfile

        from Docs.utilidades_distribucion import _iterar_ficheros_zip_portable

        zip_path = Path(__file__).resolve().parents[1] / "Juego" / "Distribucion" / "MATCAD_juego_portable.zip"
        if not zip_path.is_file():
            self.skipTest(f"No existe {zip_path}; ejecuta utilidades_distribucion.py --solo-zip")

        esperados = {arc for _, arc in _iterar_ficheros_zip_portable()}
        esperados |= {"Jugar.bat", "LEEME.txt", "COMO_JUGAR.md", "CHANGELOG_JUEGO.md"}
        with zipfile.ZipFile(zip_path) as zf:
            actuales = set(zf.namelist()) - {".matcad-paquete-completo"}
        faltan = esperados - actuales
        self.assertFalse(faltan, f"Faltan en el zip portable: {sorted(faltan)[:10]}")
        self.assertIn("Data/Banco/plantillas.json", actuales)
        self.assertIn("Juego/presets.json", actuales)
        self.assertIn("Juego/juego_grafico.py", actuales)
        self.assertIn("Juego/Grafico/pantallas_escape.py", actuales)
        self.assertIn("Juego/Comun/rutas.py", actuales)
        self.assertNotIn("Data/Banco/creador_privado.json", actuales)
        # creador_privado.json en Data/Privado/ solo si el autor empaqueta SMTP al generar el zip.
        self.assertNotIn("Docs/CHANGELOG_JUEGO.md", actuales)
        self.assertNotIn("Juego/LEEME.txt", actuales)
        self.assertNotIn("Juego/Distribucion/Jugar.bat", actuales)
        self.assertFalse(any(n.startswith("Juego/Scripts/") for n in actuales))
        self.assertFalse(any(n.startswith("Juego/Distribucion/") for n in actuales))
        self.assertFalse(
            any(n.startswith("Data/Juego/") for n in actuales),
            "El zip portable no debe incluir runtime ni catálogos en Data/Juego/",
        )
        privado = [n for n in actuales if n.startswith("Data/Privado/")]
        self.assertTrue(
            all(n == "Data/Privado/creador_privado.json" for n in privado),
            f"Solo creador_privado.json puede ir en Data/Privado/: {privado}",
        )
        for ruta in (
            "Data/preferencias_grafico.json",
            "Data/estadisticas_jugador.json",
            "Data/metadatos_inferidos.json",
        ):
            self.assertNotIn(ruta, actuales, f"Runtime en zip portable: {ruta}")
        self.assertFalse(
            any(n.startswith("Data/") and n.endswith(".txt") for n in actuales),
            "Informes/feedback .txt no deben ir en el zip portable",
        )

    def test_auditar_carpetas_data_sin_problemas_en_repo(self) -> None:
        from Comun.persistencia import auditar_carpetas_data

        raiz = Path(__file__).resolve().parents[1]
        problemas = auditar_carpetas_data(raiz)
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_zip_portable_excluye_data_juego_y_privado(self) -> None:
        from Docs.utilidades_distribucion import _iterar_ficheros_zip_portable

        archivos = {arc for _, arc in _iterar_ficheros_zip_portable()}
        self.assertFalse(any(a.startswith("Data/Juego/") for a in archivos))
        self.assertFalse(any(a.startswith("Data/Privado/") for a in archivos))

    def test_zip_portable_excluye_runtime_en_data(self) -> None:
        from Docs.utilidades_distribucion import _iterar_ficheros_zip_portable

        archivos = {arc for _, arc in _iterar_ficheros_zip_portable()}
        prohibidos = (
            "Data/preferencias_grafico.json",
            "Data/estadisticas_jugador.json",
            "Data/metadatos_inferidos.json",
        )
        for ruta in prohibidos:
            self.assertNotIn(ruta, archivos, f"Runtime del jugador no debe empaquetarse: {ruta}")
        self.assertFalse(any(a.endswith(".txt") and a.startswith("Data/") for a in archivos))

    def test_auditoria_contenido_minimo_coherente(self) -> None:
        """Las exclusiones no deben romper el cierre de imports del flujo mínimo."""
        import importlib.util

        from Comun.contenido import MODULOS_EXCLUIDOS_MINIMO

        ruta = (
            Path(__file__).resolve().parents[1]
            / "Juego"
            / "Scripts"
            / "auditar_contenido_minimo.py"
        )
        spec = importlib.util.spec_from_file_location("auditar_contenido_minimo", ruta)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        necesarios, opcionales, excluidos = mod.auditar()
        self.assertGreater(len(necesarios), 40)
        self.assertEqual(len(excluidos), 5)
        self.assertIn("Comun.escape_room", excluidos)
        self.assertIn("Grafico.pantallas_historia", excluidos)


if __name__ == "__main__":
    unittest.main()
