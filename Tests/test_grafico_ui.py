#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Textos compartidos, tooltips y barra de estado (pygame).

Secciones:
- test_textos_ui.py
- test_tooltips_ui.py
- test_texto_grafico.py
- test_barra_estado.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from Tests.Fixtures.support import emoji_font_disponible, ensure_docs_path, ensure_juego_path

ensure_juego_path()
ensure_docs_path()

# --- test_textos_ui.py ---

from unittest.mock import patch

from Comun.textos_ui import (
    OPCIONES_MENU_PRINCIPAL,
    con_emoji,
    etiqueta,
    info_dataset,
    mensaje_feedback,
    titulo_flexible,
    titulo_pantalla,
)


class TestTextosUi(unittest.TestCase):
    def test_con_emoji_simetrico(self) -> None:
        self.assertEqual(con_emoji("Modo historia", "📕"), "📕 Modo historia 📕")

    def test_con_emoji_simple(self) -> None:
        self.assertEqual(
            con_emoji("Modo feedback", "📣", simetrico=False),
            "📣 Modo feedback",
        )

    def test_con_emoji_fin(self) -> None:
        self.assertEqual(
            con_emoji("Siguiente", "▶️", posicion="fin"),
            "Siguiente ▶️",
        )

    def test_con_emoji_inicio(self) -> None:
        self.assertEqual(
            con_emoji("Atrás", "◀️", posicion="inicio"),
            "◀️ Atrás",
        )

    def test_sin_emoji(self) -> None:
        self.assertEqual(con_emoji("Modo libre", "🎮", usar_emojis=False), "Modo libre")

    def test_titulo_pantalla_alterno(self) -> None:
        self.assertEqual(
            titulo_pantalla("MODO HISTORIA", simetrico=False, contexto="alterno"),
            "📕 MODO HISTORIA",
        )

    def test_info_dataset_alterno(self) -> None:
        self.assertTrue(
            info_dataset(480, 40, simetrico=False, contexto="alterno").startswith("📕")
        )

    def test_titulo_pantalla_grafico_por_defecto(self) -> None:
        self.assertEqual(
            titulo_pantalla("MODO HISTORIA"),
            "📖 MODO HISTORIA 📖",
        )
        self.assertEqual(
            titulo_pantalla("MODO LIBRE"),
            "🎮 MODO LIBRE 🎮",
        )

    def test_info_dataset_grafico(self) -> None:
        self.assertIn("480 preguntas", info_dataset(480, 40))
        self.assertTrue(info_dataset(480, 40).startswith("📚"))

    def test_mensaje_feedback(self) -> None:
        self.assertIn("✅", mensaje_feedback("Correcto (+10 puntos)"))
        self.assertIn("❌", mensaje_feedback("Incorrecto"))

    def test_menu_principal_ids(self) -> None:
        ids = {o.id for o in OPCIONES_MENU_PRINCIPAL}
        self.assertEqual(ids, {"libre", "diarios", "historia", "especiales", "feedback", "salir"})

    def test_menu_grafico_sin_diarios(self) -> None:
        from Grafico.pantallas import MenuPrincipal

        ids = {o.id for o in MenuPrincipal.OPCIONES}
        self.assertNotIn("diarios", ids)
        self.assertEqual(
            ids, {"libre", "historia", "especiales", "feedback", "salir"}
        )

    @patch("Grafico.textos_grafico.emojis_habilitados", return_value=True)
    def test_emoji_icono_ranking(self, _mock: object) -> None:
        from Grafico.textos_grafico import emoji_icono

        self.assertEqual(emoji_icono("ranking"), "ℹ️")

    @patch("Grafico.textos_grafico.emojis_habilitados", return_value=True)
    def test_emoji_icono_diarios(self, _mock: object) -> None:
        from Grafico.textos_grafico import emoji_icono

        self.assertEqual(emoji_icono("diarios"), "📅")

    def test_opcion_menu_grafico(self) -> None:
        fb = next(o for o in OPCIONES_MENU_PRINCIPAL if o.id == "feedback")
        self.assertEqual(fb.etiqueta(), "📣 Modo feedback 📣")

    def test_navegacion_emojis_coherentes(self) -> None:
        from Comun.textos_ui import (
            BTN_ATRAS,
            BTN_CONTINUAR,
            BTN_EMPEZAR,
            BTN_SIGUIENTE,
            BTN_VOLVER,
            BTN_VOLVER_MENU,
            resolver_emoji,
        )

        atras = resolver_emoji(BTN_ATRAS[1])
        self.assertEqual(resolver_emoji(BTN_VOLVER[1]), atras)
        self.assertEqual(resolver_emoji(BTN_VOLVER_MENU[1]), atras)
        adelante = resolver_emoji(BTN_SIGUIENTE[1])
        self.assertEqual(resolver_emoji(BTN_EMPEZAR[1]), adelante)
        self.assertEqual(resolver_emoji(BTN_CONTINUAR[1]), adelante)

    @patch("Grafico.textos_grafico.emojis_habilitados", return_value=True)
    def test_etiqueta_navegacion_grafico(self, _mock: object) -> None:
        from Comun.textos_ui import BTN_ABANDONAR, BTN_ATRAS, BTN_SIGUIENTE
        from Grafico.textos_grafico import etiqueta as etiqueta_gfx

        self.assertEqual(etiqueta_gfx(*BTN_ATRAS), "◀️ Atrás")
        self.assertEqual(etiqueta_gfx(*BTN_SIGUIENTE), "Siguiente ▶️")
        self.assertEqual(etiqueta_gfx(*BTN_ABANDONAR), "Abandonar 🛑")

    @patch("Grafico.textos_grafico.emojis_habilitados", return_value=True)
    def test_etiqueta_menu_pausa_grafico(self, _mock: object) -> None:
        from Comun.textos_ui import (
            BTN_CONTINUAR,
            BTN_PANTALLA_TITULO,
            BTN_SALIR_PROGRAMA,
        )
        from Grafico.textos_grafico import etiqueta_menu

        self.assertEqual(etiqueta_menu(*BTN_CONTINUAR), "▶️ Continuar ▶️")
        self.assertEqual(
            etiqueta_menu(*BTN_PANTALLA_TITULO), "🏠 Pantalla de título 🏠"
        )
        self.assertEqual(
            etiqueta_menu(*BTN_SALIR_PROGRAMA), "🚪 Salir del programa 🚪"
        )

    def test_etiqueta_grafico_sin_emojis(self) -> None:
        from Comun.textos_ui import BTN_ATRAS, BTN_CONTINUAR
        from Grafico.textos_grafico import etiqueta as etiqueta_gfx, etiqueta_menu

        with patch("Grafico.textos_grafico.emojis_habilitados", return_value=False):
            self.assertEqual(etiqueta_gfx(*BTN_ATRAS), "Atrás")
            self.assertEqual(etiqueta_menu(*BTN_CONTINUAR), "Continuar")

    def test_titulo_flexible_prefijo(self) -> None:
        self.assertIn("🔥", titulo_flexible("FIN RACHA — Resistencia"))

# --- test_preferencias_grafico.py ---

from Comun.preferencias_grafico import (  # noqa: E402
    PreferenciasGrafico,
    cargar_preferencias_grafico,
    debe_saltar_bienvenida_grafico,
    guardar_preferencias_grafico,
    nombre_jugador_grafico,
    nombre_inicial_grafico,
    resolver_path_preferencias_grafico,
)
from Comun.preferencias_grafico import NOMBRE_JUGADOR_DEFECTO  # noqa: E402


class TestPreferenciasGrafico(unittest.TestCase):
    def test_guardar_y_cargar_en_temporal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preferencias_grafico.json"
            with patch(
                "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                return_value=path,
            ):
                guardar_preferencias_grafico(
                    PreferenciasGrafico(
                        nombre_jugador="Tester",
                        mostrar_tooltips=False,
                        mostrar_emojis=False,
                    )
                )
                prefs = cargar_preferencias_grafico()
            self.assertEqual(prefs.nombre_jugador, "Tester")
            self.assertFalse(prefs.mostrar_tooltips)
            self.assertFalse(prefs.mostrar_emojis)

    def test_nombre_inicial_omite_anonimo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preferencias_grafico.json"
            path.write_text(
                json.dumps({"nombre_jugador": "Anonimo"}),
                encoding="utf-8",
            )
            with patch(
                "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                return_value=path,
            ):
                self.assertEqual(nombre_inicial_grafico(), "")
                path.write_text(
                    json.dumps({"nombre_jugador": "Daniel"}),
                    encoding="utf-8",
                )
                self.assertEqual(nombre_inicial_grafico(), "Daniel")

    def test_nombre_jugador_grafico_desde_prefs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preferencias_grafico.json"
            with patch(
                "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                return_value=path,
            ):
                guardar_preferencias_grafico(
                    PreferenciasGrafico(nombre_jugador="Laura")
                )
                self.assertEqual(nombre_jugador_grafico(), "Laura")

    def test_debe_saltar_bienvenida_solo_con_nombre_real(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preferencias_grafico.json"
            with patch(
                "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                return_value=path,
            ):
                self.assertFalse(debe_saltar_bienvenida_grafico())
                guardar_preferencias_grafico(
                    PreferenciasGrafico(nombre_jugador="Daniel")
                )
                self.assertTrue(debe_saltar_bienvenida_grafico())
                guardar_preferencias_grafico(PreferenciasGrafico(nombre_jugador=""))
                self.assertFalse(debe_saltar_bienvenida_grafico())

    def test_bienvenida_vacia_guarda_anonimo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preferencias_grafico.json"
            with patch(
                "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                return_value=path,
            ):
                from Comun.preferencias_grafico import es_nombre_anonimo, nombre_jugador_efectivo

                nombre_efectivo = nombre_jugador_efectivo("")
                nombre_guardado = (
                    "" if es_nombre_anonimo(nombre_efectivo) else nombre_efectivo
                )
                guardar_preferencias_grafico(
                    PreferenciasGrafico(nombre_jugador=nombre_guardado)
                )
                self.assertEqual(cargar_preferencias_grafico().nombre_jugador, "")
                self.assertEqual(nombre_jugador_grafico(), NOMBRE_JUGADOR_DEFECTO)


# --- persistencia / datos locales ---

from Comun.persistencia import (  # noqa: E402
    borrar_txt_informes_feedback,
    inicializar_datos_locales_juego,
    listar_txt_informes_feedback,
    vaciar_estadisticas_locales,
    vaciar_preferencias_locales,
)

# --- test_utilidades_limpieza.py ---

from utilidades import (  # noqa: E402
    borrar_temporales,
    dir_data_juego,
    dirs_data_juego,
    listar_carpetas_data_juego_vacias,
    listar_directorios_vacios,
    listar_ficheros_runtime_juego,
)


class TestBorrarTemporalesExterno(unittest.TestCase):
    def test_elimina_preferencias_desde_fuera(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            juego = raiz / "Data" / "Juego"
            juego.mkdir(parents=True)
            (juego / "preferencias_grafico.json").write_text("{}", encoding="utf-8")
            (juego / "estadisticas_jugador.json").write_text("{}", encoding="utf-8")
            (juego / "metadatos_inferidos.json").write_text("{}", encoding="utf-8")
            (juego / "informe_partida_demo.txt").write_text("informe", encoding="utf-8")
            (juego / "feedback_bug_jugador_20260101_000000_abcd.txt").write_text(
                "feedback", encoding="utf-8"
            )

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                json_locales, _, txt = listar_ficheros_runtime_juego()
                self.assertEqual(len(json_locales), 3)
                self.assertEqual(len(txt), 2)
                resumen = borrar_temporales(raiz, incluir_pycache=False)
                self.assertEqual(resumen.json_preferencias_borrados, 3)
                self.assertEqual(resumen.txt_borrados, 2)
                self.assertEqual(listar_ficheros_runtime_juego(), ([], [], []))

    def test_elimina_runtime_plano_y_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            data = raiz / "Data"
            data.mkdir(parents=True)
            (data / "preferencias_grafico.json").write_text("{}", encoding="utf-8")
            (data / "informe_plano.txt").write_text("x", encoding="utf-8")
            informes = data / "Informes"
            informes.mkdir()
            (informes / "viejo.txt").write_text("y", encoding="utf-8")
            feedback = data / "Feedback"
            feedback.mkdir()
            (feedback / "aviso.txt").write_text("z", encoding="utf-8")
            (data / "README.md").write_text("keep", encoding="utf-8")

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                resumen = borrar_temporales(raiz, incluir_pycache=False)
                self.assertEqual(resumen.json_preferencias_borrados, 1)
                self.assertEqual(resumen.txt_borrados, 3)
                self.assertFalse((data / "preferencias_grafico.json").exists())
                self.assertFalse(informes.exists())
                self.assertFalse(feedback.exists())
                self.assertTrue((data / "README.md").is_file())

    def test_dir_data_juego(self) -> None:
        with patch("utilidades.raiz_proyecto", return_value=Path("/proyecto")):
            self.assertEqual(dir_data_juego(), Path("/proyecto") / "Data" / "Juego")

    def test_dirs_data_juego_solo_canonica(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            canon = raiz / "Data" / "Juego"
            exe = raiz / "Juego" / "Data" / "Juego"
            canon.mkdir(parents=True)
            exe.mkdir(parents=True)
            with patch("utilidades.raiz_proyecto", return_value=raiz):
                self.assertEqual(dirs_data_juego(), [canon])

    def test_elimina_runtime_junto_al_exe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            juego_exe = raiz / "Juego" / "Data" / "Juego"
            juego_exe.mkdir(parents=True)
            (juego_exe / "preferencias_grafico.json").write_text("{}", encoding="utf-8")
            (juego_exe / "ranking_obsoleto.json").write_text("{}", encoding="utf-8")

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                self.assertEqual(len(listar_ficheros_runtime_juego()[0]), 0)
                resumen = borrar_temporales(raiz, incluir_pycache=False)
                self.assertEqual(resumen.json_preferencias_borrados, 0)
                self.assertFalse((raiz / "Juego" / "Data").exists())
                self.assertGreaterEqual(resumen.carpetas_vacias_borradas, 1)

    def test_elimina_arbol_data_exe_con_banco(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            data_exe = raiz / "Juego" / "Data"
            (data_exe / "Banco").mkdir(parents=True)
            (data_exe / "Banco" / "creador_privado.json").write_text("{}", encoding="utf-8")
            (data_exe / "Juego").mkdir(parents=True)
            (data_exe / "Juego" / "ranking_obsoleto.json").write_text("{}", encoding="utf-8")

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                resumen = borrar_temporales(raiz, incluir_pycache=False)
                self.assertFalse(data_exe.exists())
                self.assertGreaterEqual(resumen.carpetas_vacias_borradas, 1)

    def test_elimina_carpetas_vacias_sin_ficheros_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            vacia = raiz / "Juego" / "Data" / "Juego"
            vacia.mkdir(parents=True)

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                resumen = borrar_temporales(raiz, incluir_pycache=False)
                self.assertGreaterEqual(resumen.carpetas_vacias_borradas, 1)
                self.assertFalse((raiz / "Juego" / "Data").exists())

    def test_elimina_data_exe_si_rmtree_falla(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "Juego" / "Data" / "Juego").mkdir(parents=True)

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                with patch(
                    "utilidades.shutil.rmtree",
                    side_effect=OSError("bloqueado"),
                ):
                    resumen = borrar_temporales(raiz, incluir_pycache=False)
                self.assertFalse((raiz / "Juego" / "Data").exists())
                self.assertGreaterEqual(resumen.carpetas_vacias_borradas, 1)
                self.assertEqual(resumen.carpetas_vacias_errores, 0)

    def test_solo_pycache_elimina_data_exe_vacio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / "Juego" / "Data" / "Juego").mkdir(parents=True)

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                resumen = borrar_temporales(
                    raiz,
                    incluir_pycache=True,
                    incluir_txt=False,
                    incluir_json=False,
                )
                self.assertFalse((raiz / "Juego" / "Data").exists())
                self.assertGreaterEqual(resumen.carpetas_vacias_borradas, 2)

    def test_elimina_runtime_y_borra_carpeta_vacia(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            juego = raiz / "Data" / "Juego"
            juego.mkdir(parents=True)
            (juego / "preferencias_grafico.json").write_text("{}", encoding="utf-8")
            (juego / "estadisticas_jugador.json").write_text("{}", encoding="utf-8")

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                resumen = borrar_temporales(raiz, incluir_pycache=False)
                self.assertEqual(resumen.json_preferencias_borrados, 2)
                self.assertGreaterEqual(resumen.carpetas_vacias_borradas, 1)
                self.assertFalse(juego.exists())

    def test_elimina_directorios_vacios_anidados(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            hoja = raiz / "test" / "a" / "b" / "z"
            hoja.mkdir(parents=True)

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                previstos = listar_directorios_vacios(raiz)
                self.assertIn(hoja, previstos)
                self.assertIn(hoja.parent, previstos)
                self.assertIn(raiz / "test", previstos)
                resumen = borrar_temporales(raiz, incluir_txt=False, incluir_json=False)
                self.assertFalse((raiz / "test").exists())
                self.assertGreaterEqual(resumen.carpetas_vacias_borradas, 4)

    def test_conserva_ancestro_con_contenido_en_rama_vacia(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            a = raiz / "test" / "a"
            a.mkdir(parents=True)
            (a / "datos.txt").write_text("x", encoding="utf-8")
            (a / "b" / "z").mkdir(parents=True)

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                previstos = listar_directorios_vacios(raiz)
                self.assertIn(a / "b" / "z", previstos)
                self.assertIn(a / "b", previstos)
                self.assertNotIn(raiz / "test", previstos)
                self.assertNotIn(a, previstos)

                resumen = borrar_temporales(raiz, incluir_txt=False, incluir_json=False)
                self.assertEqual(resumen.carpetas_vacias_borradas, 2)
                self.assertTrue((raiz / "test").is_dir())
                self.assertTrue(a.is_dir())
                self.assertTrue((a / "datos.txt").is_file())
                self.assertFalse((a / "b").exists())

    def test_solo_borra_hoja_vacia_si_padre_intermedio_tiene_archivos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            b = raiz / "test" / "a" / "b"
            b.mkdir(parents=True)
            (b / "f.txt").write_text("x", encoding="utf-8")
            (b / "z").mkdir()

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                previstos = listar_directorios_vacios(raiz)
                self.assertEqual(previstos, [b / "z"])

                borrar_temporales(raiz, incluir_txt=False, incluir_json=False)
                self.assertTrue((raiz / "test").is_dir())
                self.assertTrue(b.is_dir())
                self.assertTrue((b / "f.txt").is_file())
                self.assertFalse((b / "z").exists())

    def test_elimina_ramas_vacias_hermanas_bajo_mismo_padre(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            a = raiz / "test" / "a"
            (a / "b" / "z").mkdir(parents=True)
            (a / "c").mkdir(parents=True)

            with patch("utilidades.raiz_proyecto", return_value=raiz):
                previstos = listar_directorios_vacios(raiz)
                self.assertIn(a / "b" / "z", previstos)
                self.assertIn(a / "b", previstos)
                self.assertIn(a / "c", previstos)
                self.assertIn(a, previstos)
                self.assertIn(raiz / "test", previstos)

                resumen = borrar_temporales(raiz, incluir_txt=False, incluir_json=False)
                self.assertEqual(resumen.carpetas_vacias_borradas, 5)
                self.assertFalse((raiz / "test").exists())


class TestRutasDataEscritura(unittest.TestCase):
    def test_dir_juego_datos_repara_fichero_en_ruta(self) -> None:
        from Comun.rutas import _dir_juego_datos

        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            data = raiz / "Data"
            data.mkdir()
            (data / "Juego").write_text("bloqueo", encoding="utf-8")

            with patch("Comun.rutas._data_root", return_value=data):
                carpeta = _dir_juego_datos()
                self.assertTrue(carpeta.is_dir())
                self.assertEqual(carpeta, data / "Juego")


class TestDatosLocalesJuego(unittest.TestCase):
    def test_esquemas_coinciden_con_modulos(self) -> None:
        from Comun.persistencia import (
            estadisticas_jugador_vacio,
            preferencias_grafico_vacio,
        )
        from Comun.estadisticas_jugador import vaciar_estadisticas_jugador
        from Comun.preferencias_grafico import PreferenciasGrafico, guardar_preferencias_grafico

        with tempfile.TemporaryDirectory() as tmp:
            path_prefs = Path(tmp) / "preferencias_grafico.json"
            with patch(
                "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                return_value=path_prefs,
            ):
                guardar_preferencias_grafico(PreferenciasGrafico())
                guardado_prefs = json.loads(path_prefs.read_text(encoding="utf-8"))
            self.assertEqual(guardado_prefs, preferencias_grafico_vacio())

            path_stats = Path(tmp) / "estadisticas_jugador.json"
            with patch(
                "Comun.estadisticas_jugador.resolver_path_estadisticas_jugador",
                return_value=path_stats,
            ):
                vaciar_estadisticas_jugador()
                guardado_stats = json.loads(path_stats.read_text(encoding="utf-8"))
            self.assertEqual(guardado_stats, estadisticas_jugador_vacio())

    def test_borrar_txt_informes_y_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            juego = Path(tmp) / "Juego"
            juego.mkdir()
            (juego / "a.txt").write_text("a", encoding="utf-8")
            (juego / "b.txt").write_text("b", encoding="utf-8")
            with patch("Comun.persistencia.resolver_dir_informes", return_value=juego):
                self.assertEqual(len(listar_txt_informes_feedback()), 2)
                resumen = borrar_txt_informes_feedback()
                self.assertEqual(resumen.borrados, 2)
                self.assertEqual(resumen.errores, 0)
                self.assertEqual(listar_txt_informes_feedback(), [])

    def test_inicializar_crea_json_si_faltan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            juego = Path(tmp) / "Juego"
            juego.mkdir()
            path_graf = juego / "preferencias_grafico.json"
            path_stats = juego / "estadisticas_jugador.json"

            def _crear_stats() -> Path:
                if not path_stats.is_file():
                    path_stats.write_text(
                        '{"totales": {"partidas": 0, "preguntas": 0, '
                        '"aciertos": 0, "fallos": 0}, "por_modo": {}, "por_materia": {}, '
                        '"por_tipo": {}, "records": {}, "sesiones": [], "dias_activos": []}',
                        encoding="utf-8",
                    )
                return path_stats

            with (
                patch(
                    "Comun.persistencia.resolver_path_preferencias_grafico",
                    return_value=path_graf,
                ),
                patch(
                    "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                    return_value=path_graf,
                ),
                patch(
                    "Comun.persistencia.resolver_path_estadisticas_jugador",
                    side_effect=_crear_stats,
                ),
                patch(
                    "Comun.estadisticas_jugador.resolver_path_estadisticas_jugador",
                    side_effect=_crear_stats,
                ),
            ):
                inicializar_datos_locales_juego()
                self.assertTrue(path_graf.is_file())
                self.assertTrue(path_stats.is_file())

    def test_listar_txt_no_incluye_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            juego = Path(tmp) / "Juego"
            juego.mkdir()
            (juego / "informe.txt").write_text("a", encoding="utf-8")
            (juego / "preferencias_grafico.json").write_text("{}", encoding="utf-8")
            with patch("Comun.persistencia.resolver_dir_informes", return_value=juego):
                self.assertEqual([p.name for p in listar_txt_informes_feedback()], ["informe.txt"])

    def test_vaciar_preferencias_conserva_fichero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            juego = Path(tmp) / "Juego"
            juego.mkdir()
            path_graf = juego / "preferencias_grafico.json"
            path_graf.write_text('{"nombre_jugador": "Ana"}', encoding="utf-8")
            with patch(
                "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
                return_value=path_graf,
            ):
                vaciar_preferencias_locales()
                self.assertTrue(path_graf.is_file())
                self.assertIn('"nombre_jugador": ""', path_graf.read_text(encoding="utf-8"))

    def test_vaciar_estadisticas_conserva_fichero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            juego = Path(tmp) / "Juego"
            juego.mkdir()
            path_stats = juego / "estadisticas_jugador.json"
            path_stats.write_text(
                '{"totales": {"partidas": 3, "preguntas": 10, '
                '"aciertos": 8, "fallos": 2}, "por_modo": {}, "por_materia": {}, '
                '"por_tipo": {}, "records": {}, "sesiones": [], "dias_activos": []}',
                encoding="utf-8",
            )
            with patch(
                "Comun.estadisticas_jugador.resolver_path_estadisticas_jugador",
                return_value=path_stats,
            ):
                vaciar_estadisticas_locales()
                self.assertTrue(path_stats.is_file())
                self.assertIn('"partidas": 0', path_stats.read_text(encoding="utf-8"))


# --- test_tooltips_ui.py ---

from Grafico.tooltips_ui import (  # noqa: E402
    TOOLTIP_PAUSA,
    tooltip_filtro_principal,
    tooltip_menu_principal,
    tooltip_opcion_ciclo_historia,
    tooltip_opcion_ciclo_libre,
    tooltips_menu_pausa,
)


class TestTooltipsUi(unittest.TestCase):
    def test_menu_principal_tiene_texto(self) -> None:
        for oid in ("libre", "historia", "feedback", "salir"):
            self.assertTrue(tooltip_menu_principal(oid))

    def test_filtros_tienen_texto(self) -> None:
        for codigo in ("todas", "tematica", "semestre", "tipo"):
            texto = tooltip_filtro_principal(codigo)
            self.assertIsNotNone(texto)
            self.assertGreater(len(texto or ""), 10)

    def test_opcion_ciclo_libre(self) -> None:
        self.assertIsNone(tooltip_opcion_ciclo_libre("vidas", "3"))
        self.assertIsNone(tooltip_opcion_ciclo_libre("tiempo_pregunta", "90"))
        self.assertIsNotNone(tooltip_opcion_ciclo_libre("banco", "dataset"))
        self.assertIsNotNone(tooltip_opcion_ciclo_libre("sistema", "arcade"))
        self.assertIsNotNone(tooltip_opcion_ciclo_libre("n_preguntas", "infinito"))
        self.assertIsNone(tooltip_opcion_ciclo_libre("n_preguntas", "10"))

    def test_pausa_no_vacia(self) -> None:
        self.assertGreater(len(TOOLTIP_PAUSA), 20)
        tips = tooltips_menu_pausa(en_partida=False)
        self.assertEqual(len(tips), 3)
        self.assertTrue(all(len(t) > 10 for t in tips))
        tips_partida = tooltips_menu_pausa(en_partida=True)
        self.assertNotEqual(tips[0], tips_partida[0])

    def test_opcion_ciclo_historia(self) -> None:
        self.assertIsNotNone(
            tooltip_opcion_ciclo_historia("curso", "curso", "", etiqueta_opcion="Curso")
        )
        self.assertIsNotNone(
            tooltip_opcion_ciclo_historia(
                "estrategia_practica",
                "eleccion",
                "debilidades",
            )
        )
        self.assertIsNotNone(
            tooltip_opcion_ciclo_historia(
                "tiempo_total_min",
                "entero",
                "0",
            )
        )

    def test_navegacion_y_abandono_tienen_texto(self) -> None:
        from Grafico.tooltips_ui import (
            TOOLTIP_ABANDONAR_HISTORIA,
            TOOLTIP_ABANDONAR_LIBRE,
            TOOLTIP_ABANDONAR_RESISTENCIA,
            TOOLTIP_ATRAS,
            TOOLTIP_CONTINUAR,
            TOOLTIP_DIFICULTAD_PROGRESIVA,
            TOOLTIP_EMPEZAR,
            tooltip_guardar_informe,
            TOOLTIP_SIGUIENTE,
            TOOLTIP_VER_RANKING,
        )

        for texto in (
            TOOLTIP_ATRAS,
            TOOLTIP_SIGUIENTE,
            TOOLTIP_EMPEZAR,
            TOOLTIP_CONTINUAR,
            TOOLTIP_DIFICULTAD_PROGRESIVA,
            TOOLTIP_ABANDONAR_LIBRE,
            TOOLTIP_ABANDONAR_HISTORIA,
            TOOLTIP_ABANDONAR_RESISTENCIA,
            tooltip_guardar_informe(),
            TOOLTIP_VER_RANKING,
        ):
            self.assertGreater(len(texto), 15, msg=texto[:30])

    def test_tiempo_modo_y_sistema_libre(self) -> None:
        self.assertIn("cronómetro", tooltip_opcion_ciclo_libre("tiempo_modo", "ninguno") or "")
        self.assertIn("Puntos", tooltip_opcion_ciclo_libre("sistema", "arcade") or "")


class TestPosicionBotonesFila(unittest.TestCase):
    def test_empaqueta_cuatro_botones_fin_partida_en_dos_filas(self) -> None:
        import pygame

        pygame.init()
        from Grafico.tema import ANCHO, MARGEN, crear_fuentes
        from Grafico.textos_grafico import etiqueta
        from Grafico.ui import Boton, empaquetar_indices_en_filas, posicionar_botones_fila, rect_boton_etiqueta
        from Comun.textos_ui import (
            BTN_CAMBIAR_OPCIONES,
            BTN_EXAMEN_DIRIGIDO,
            BTN_REPETIR_PARTIDA,
            BTN_VOLVER_MENU,
        )

        fuente = crear_fuentes()["menu"]
        etiqs = [
            etiqueta(*b)
            for b in (
                BTN_REPETIR_PARTIDA,
                BTN_EXAMEN_DIRIGIDO,
                BTN_CAMBIAR_OPCIONES,
                BTN_VOLVER_MENU,
            )
        ]
        botones = [
            Boton(
                etiq,
                rect_boton_etiqueta(etiq, fuente, x_centro=0, y=0, alto_min=44),
                lambda: None,
            )
            for etiq in etiqs
        ]
        anchos = [b.rect.width for b in botones]
        ancho_max = ANCHO - 2 * MARGEN
        filas = empaquetar_indices_en_filas(anchos, ancho_disponible=ancho_max, gap=10)
        self.assertEqual(len(filas), 2)
        posicionar_botones_fila(botones, 632, x_centro=ANCHO // 2, gap=10)
        for boton in botones:
            self.assertGreaterEqual(boton.rect.left, MARGEN)
            self.assertLessEqual(boton.rect.right, ANCHO - MARGEN)


class TestBarraProgresoPartida(unittest.TestCase):
    def test_ultima_pregunta_llena_la_barra(self) -> None:
        from Grafico.pantallas import fraccion_barra_progreso_partida

        self.assertEqual(
            fraccion_barra_progreso_partida(indice_pregunta=19, total=20),
            1.0,
        )

    def test_primera_pregunta_no_vacia(self) -> None:
        from Grafico.pantallas import fraccion_barra_progreso_partida

        self.assertEqual(
            fraccion_barra_progreso_partida(indice_pregunta=0, total=20),
            0.05,
        )


# --- test_texto_grafico.py ---

class TestTextoGrafico(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import pygame

        from Grafico.fuentes import invalidar_cache_fuentes

        pygame.init()
        pygame.display.set_mode((960, 720))
        invalidar_cache_fuentes()

    @classmethod
    def tearDownClass(cls) -> None:
        import pygame

        from Grafico.fuentes import invalidar_cache_fuentes

        invalidar_cache_fuentes()
        if pygame.get_init():
            pygame.quit()

    def test_partir_lineas_titulo_largo(self) -> None:
        from Grafico.texto import _partir_lineas_centro

        titulo = "Pregunta 18 — Ranking — resistencia"
        lineas = _partir_lineas_centro(titulo, 40, 400, bold=True)
        self.assertGreater(len(lineas), 1)
        for linea in lineas:
            self.assertTrue(linea)

    def test_partir_lineas_corta_una_sola(self) -> None:
        from Grafico.texto import _partir_lineas_centro

        lineas = _partir_lineas_centro("FIN DE PARTIDA", 40, 880, bold=True)
        self.assertEqual(lineas, ["FIN DE PARTIDA"])

    def test_icono_saltar_usa_fuente_emoji(self) -> None:
        from Comun.resistencia_motor import emoji_powerup
        from Grafico.texto import familia_caracter, segmentar_por_familia

        icono = emoji_powerup("skip")
        self.assertEqual(icono, "⏭️")
        self.assertEqual(familia_caracter(icono[0]), "emoji")
        familias = {fam for _, fam in segmentar_por_familia(icono)}
        self.assertIn("emoji", familias)
        self.assertNotIn("simbolos", familias)

    def test_icono_comodin_naip_usa_fuente_emoji(self) -> None:
        from Comun.objetos_partida import emoji_powerup
        from Grafico.texto import familia_caracter, segmentar_por_familia

        icono = emoji_powerup("comodin")
        self.assertEqual(icono, "🃏")
        self.assertEqual(familia_caracter(icono), "emoji")
        familias = {fam for _, fam in segmentar_por_familia(icono)}
        self.assertEqual(familias, {"emoji"})

    def test_dibujar_texto_centro_con_ancho_max_multilinea(self) -> None:
        import pygame

        from Grafico.texto import dibujar_texto_centro
        from Grafico.tema import ANCHO, MARGEN

        titulo = "Pregunta 18 — Ranking — resistencia"
        ancho_max = ANCHO - 2 * MARGEN
        superficie = pygame.Surface((ANCHO, 160))
        rect = dibujar_texto_centro(
            superficie,
            titulo,
            (ANCHO // 2, 80),
            40,
            (255, 255, 255),
            bold=True,
            ancho_max=ancho_max,
        )
        self.assertLessEqual(rect.width, ancho_max + 4)
        self.assertGreater(rect.height, 45)

    def test_dibujar_texto_centro_sin_ancho_max_igual_que_antes(self) -> None:
        import pygame

        from Grafico.texto import dibujar_texto_centro
        from Grafico.tema import ANCHO

        superficie = pygame.Surface((ANCHO, 80))
        rect = dibujar_texto_centro(
            superficie,
            "Corto",
            (ANCHO // 2, 40),
            40,
            (255, 255, 255),
            bold=True,
        )
        self.assertGreater(rect.width, 0)
        self.assertGreater(rect.height, 0)

# --- test_barra_estado.py ---

from Comun.linea_estado_ui import (  # noqa: E402
    EMOJI_TIEMPO_PREG,
    EMOJI_TIEMPO_TOTAL,
    formatear_linea_estado,
    segmentos_linea_estado,
)
from Comun.motor_nucleo import EstadoPartida, linea_estado  # noqa: E402
from Comun.reglas import ReglasPartida, SistemaPuntuacion, preset_libre_arcade, preset_libre_contrarreloj  # noqa: E402


class TestBarraEstado(unittest.TestCase):
    def test_segmentos_modo_libre_infinito(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=3)
        segs = segmentos_linea_estado(estado, "", numero_pregunta=1)
        textos = [s.texto for s in segs]
        self.assertIn("1", textos)
        self.assertIn("3/3", textos)
        self.assertIn("0", textos)
        self.assertEqual(segs[0].emoji, "❓")
        self.assertEqual(segs[1].emoji, "❤️")
        self.assertEqual(segs[2].emoji, "⭐")
        self.assertNotIn("tiempo_total", [s.id for s in segs])

    def test_segmentos_modo_libre_finito(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=3)
        segs = segmentos_linea_estado(estado, "3/10")
        progreso = next(s for s in segs if s.id == "progreso")
        self.assertEqual(progreso.emoji, "📝")
        self.assertEqual(progreso.texto, "3/10")

    def test_formato_texto_con_emojis(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=3)
        texto = formatear_linea_estado(
            segmentos_linea_estado(estado, "", numero_pregunta=1),
            usar_emojis=True,
        )
        self.assertIn("❓", texto)
        self.assertIn("❤️", texto)
        self.assertNotIn(EMOJI_TIEMPO_TOTAL, texto)
        self.assertIn("⭐", texto)

    def test_linea_estado_motor_usa_emojis(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=2)
        texto = linea_estado(estado, "3/10")
        self.assertIn("📝", texto)
        self.assertIn("3/10", texto)
        self.assertIn("❤️", texto)

    def test_segmentos_racha_resistencia(self) -> None:
        reglas = preset_libre_contrarreloj()
        estado = EstadoPartida(nombre="Bob", reglas=reglas, vidas_restantes=1)
        estado.puntos_arcade = 120
        segs = segmentos_linea_estado(
            estado,
            "",
            numero_pregunta=13,
            racha=12,
            segundos_pregunta_restantes=8,
        )
        pregunta = next(s for s in segs if s.id == "progreso")
        racha = next(s for s in segs if s.id == "racha")
        self.assertEqual(pregunta.emoji, "❓")
        self.assertEqual(pregunta.texto, "13")
        self.assertEqual(racha.emoji, "🔥")
        self.assertEqual(racha.texto, "12")
        temporizador = next(s for s in segs if s.id == "tiempo_preg")
        self.assertEqual(temporizador.emoji, EMOJI_TIEMPO_PREG)
        self.assertEqual(temporizador.texto, "8s")
        self.assertNotIn("tiempo_total", [s.id for s in segs])

    def test_sin_chip_tiempo_sin_limite_global(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=3)
        ids = [s.id for s in segmentos_linea_estado(estado, "Pregunta 1/∞")]
        self.assertNotIn("tiempo_total", ids)

    def test_ambos_tiempos_simultaneos(self) -> None:
        reglas = ReglasPartida(
            sistema_puntuacion=SistemaPuntuacion.PORCENTAJE,
            tiempo_por_pregunta_seg=90,
            tiempo_total_seg=600,
        )
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=None)
        segs = segmentos_linea_estado(estado, "1/10", segundos_pregunta_restantes=42)
        ids = [s.id for s in segs]
        self.assertIn("tiempo_total", ids)
        self.assertIn("tiempo_preg", ids)
        self.assertLess(ids.index("tiempo_total"), ids.index("tiempo_preg"))

    def test_barra_no_muestra_nota_ni_porcentaje_durante_partida(self) -> None:
        from Comun.reglas import preset_historia_examen, preset_libre_contrarreloj, preset_libre_repaso

        for reglas in (preset_historia_examen(), preset_libre_repaso(), preset_libre_contrarreloj()):
            with self.subTest(sistema=reglas.sistema_puntuacion):
                estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=None)
                estado.respondidas = 10
                estado.aciertos = 7
                ids = [s.id for s in segmentos_linea_estado(estado, "10/24")]
                self.assertNotIn("nota", ids)
                self.assertNotIn("aciertos", ids)
                self.assertNotIn("puntos", ids)

    def test_modo_libre_sigue_mostrando_puntos_arcade(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=3)
        estado.respondidas = 2
        ids = [s.id for s in segmentos_linea_estado(estado, "", numero_pregunta=2)]
        self.assertIn("puntos", ids)

    def test_progreso_puerta_escape_en_barra(self) -> None:
        from Comun.reglas import preset_escape

        estado = EstadoPartida(nombre="Ana", reglas=preset_escape(), vidas_restantes=3)
        segs = segmentos_linea_estado(
            estado,
            "",
            progreso_sala="1/30",
            progreso_puerta="2/5",
            vidas_max=3,
        )
        ids = [s.id for s in segs]
        self.assertEqual(ids[0], "sala_escape")
        sala = next(s for s in segs if s.id == "sala_escape")
        self.assertEqual(sala.emoji, "🗺️")
        self.assertEqual(sala.texto, "1/30")
        self.assertEqual(ids[1], "pregunta_puerta")
        pregunta = next(s for s in segs if s.id == "pregunta_puerta")
        self.assertEqual(pregunta.emoji, "📝")
        self.assertEqual(pregunta.texto, "2/5")

    @unittest.skipUnless(emoji_font_disponible(), "Fuente emoji del sistema no disponible")
    def test_render_icono_barra_rechaza_tofu_fuente_texto(self) -> None:
        import pygame

        pygame.init()
        from Comun.linea_estado_ui import EMOJI_TIEMPO_PREG, EMOJI_TIEMPO_TOTAL
        from Grafico.fuentes import crear_fuente, render_icono_barra, superficie_emoji_valida

        fe = crear_fuente(16, familia="emoji")
        ft = crear_fuente(16, familia="texto")
        tofu = ft.render(EMOJI_TIEMPO_PREG, True, (255, 255, 255))
        self.assertFalse(superficie_emoji_valida(tofu))
        reloj_gris = fe.render(EMOJI_TIEMPO_TOTAL, True, (220, 232, 248))
        self.assertTrue(superficie_emoji_valida(reloj_gris))
        # Noto Color Emoji ignora el tinte y dibuja bitmap a color; usamos gris sintético.
        pseudo_reloj = pygame.Surface((28, 28), pygame.SRCALPHA)
        for x in range(28):
            for y in range(28):
                if (x - 14) ** 2 + (y - 14) ** 2 <= 13**2:
                    g = 210 + (x + y) % 8
                    pseudo_reloj.set_at((x, y), (g, g + 2, g + 4, 255))
        self.assertFalse(superficie_emoji_valida(pseudo_reloj))
        surf = render_icono_barra(
            fe,
            ft,
            (EMOJI_TIEMPO_PREG,),
            "P·",
            (255, 255, 255),
            usar_emoji=True,
        )
        self.assertTrue(superficie_emoji_valida(surf))
        pygame.quit()

    def test_segmentos_tiempos_distintos(self) -> None:
        import time

        reglas = ReglasPartida(
            sistema_puntuacion=SistemaPuntuacion.ARCADE,
            vidas=3,
            tiempo_por_pregunta_seg=90,
            tiempo_total_seg=600,
        )
        estado = EstadoPartida(
            nombre="Ana",
            reglas=reglas,
            vidas_restantes=3,
            inicio_total=time.monotonic(),
        )
        segs = segmentos_linea_estado(
            estado, "Pregunta 2/10", segundos_pregunta_restantes=45
        )
        total = next(s for s in segs if s.id == "tiempo_total")
        pregunta = next(s for s in segs if s.id == "tiempo_preg")
        self.assertEqual(total.emoji, EMOJI_TIEMPO_TOTAL)
        self.assertEqual(pregunta.emoji, EMOJI_TIEMPO_PREG)
        self.assertNotEqual(total.emoji, pregunta.emoji)
        texto = formatear_linea_estado(segs, usar_emojis=False)
        self.assertIn("T·", texto)
        self.assertIn("P·", texto)

if __name__ == "__main__":
    unittest.main()
