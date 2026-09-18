import os
import re
import shutil
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk

_LIB_APP = "/usr/share/convertube/lib"
if os.path.isdir(_LIB_APP):
    sys.path.insert(0, _LIB_APP)

import yt_dlp


class ConverTube(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.ejemplo.convertube")
        self._cancelar = False
        self._descargando = False
        self._cortando = False

    def do_activate(self):
        self._construir_interfaz()

    def _construir_interfaz(self):
        self.win = Adw.ApplicationWindow(application=self)
        self.win.set_title("ConverTube")
        self.win.set_icon_name("com.ejemplo.convertube")
        self.win.set_default_size(580, 520)

        # Barra de cabecera dentro de un ToolbarView: proporciona la
        # zona de arrastre y los botones de ventana en GNOME. Sin ella
        # la ventana queda sin decoración arrastrable y no se puede
        # mover del centro. (AdwApplicationWindow no admite
        # gtk_window_set_titlebar, por eso se usa ToolbarView.)
        vista = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle.new("ConverTube", "Descarga audio y corta MP3"))
        vista.add_top_bar(header)

        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        caja.set_margin_top(16)
        caja.set_margin_bottom(16)
        caja.set_margin_start(16)
        caja.set_margin_end(16)

        titulo = Gtk.Label(label="ConverTube")
        titulo.add_css_class("title-1")
        caja.append(titulo)

        subtitulo = Gtk.Label(label="Descarga audio y corta MP3")
        subtitulo.add_css_class("dim-label")
        caja.append(subtitulo)

        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        caja.append(notebook)

        tab_descarga = self._crear_tab_descarga()
        notebook.append_page(tab_descarga, Gtk.Label(label="Descargar"))

        tab_corte = self._crear_tab_corte()
        notebook.append_page(tab_corte, Gtk.Label(label="Cortar MP3"))

        vista.set_content(caja)
        self.win.set_content(vista)
        self.win.present()

    def _crear_tab_descarga(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        caja.set_margin_top(16)
        caja.set_margin_bottom(16)
        caja.set_margin_start(12)
        caja.set_margin_end(12)

        self.entrada_url = Gtk.Entry()
        self.entrada_url.set_placeholder_text("Pega aquí la URL del video")
        self.entrada_url.set_hexpand(True)
        caja.append(self.entrada_url)

        fila_formato = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        etiqueta_formato = Gtk.Label(label="Formato:")
        self.selector_formato = Gtk.DropDown.new_from_strings(["MP3", "M4A"])
        self.selector_formato.set_selected(0)
        fila_formato.append(etiqueta_formato)
        fila_formato.append(self.selector_formato)
        caja.append(fila_formato)

        fila_carpeta = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.etiqueta_carpeta = Gtk.Label(
            label=os.path.join(os.path.expanduser("~"), "Música")
        )
        self.etiqueta_carpeta.set_ellipsize(2)
        self.etiqueta_carpeta.set_hexpand(True)
        boton_carpeta = Gtk.Button(label="Elegir carpeta…")
        boton_carpeta.connect("clicked", self._al_elegir_carpeta)
        fila_carpeta.append(self.etiqueta_carpeta)
        fila_carpeta.append(boton_carpeta)
        caja.append(fila_carpeta)

        barra_botones = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        barra_botones.set_halign(Gtk.Align.CENTER)
        self.boton_descargar = Gtk.Button(label="Descargar")
        self.boton_descargar.add_css_class("suggested-action")
        self.boton_descargar.connect("clicked", self._al_descargar)
        self.boton_cancelar = Gtk.Button(label="Cancelar")
        self.boton_cancelar.set_sensitive(False)
        self.boton_cancelar.connect("clicked", self._al_cancelar)
        barra_botones.append(self.boton_descargar)
        barra_botones.append(self.boton_cancelar)
        caja.append(barra_botones)

        self.progreso = Gtk.ProgressBar()
        self.progreso.set_show_text(True)
        self.progreso.set_fraction(0.0)
        caja.append(self.progreso)

        self.estado = Gtk.Label(label="")
        self.estado.add_css_class("dim-label")
        self.estado.set_wrap(True)
        caja.append(self.estado)

        return caja

    def _crear_tab_corte(self):
        caja = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        caja.set_margin_top(16)
        caja.set_margin_bottom(16)
        caja.set_margin_start(12)
        caja.set_margin_end(12)

        label_entrada = Gtk.Label(label="Archivo MP3:")
        label_entrada.set_halign(Gtk.Align.START)
        caja.append(label_entrada)

        fila_entrada = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.corte_entrada = Gtk.Entry()
        self.corte_entrada.set_placeholder_text("Selecciona un MP3…")
        self.corte_entrada.set_hexpand(True)
        fila_entrada.append(self.corte_entrada)
        boton_entrada = Gtk.Button(label="Examinar…")
        boton_entrada.connect("clicked", self._al_elegir_mp3)
        fila_entrada.append(boton_entrada)
        caja.append(fila_entrada)

        self.corte_duracion = Gtk.Label(label="")
        self.corte_duracion.add_css_class("dim-label")
        self.corte_duracion.set_halign(Gtk.Align.START)
        caja.append(self.corte_duracion)

        fila_tiempos = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        fila_tiempos.append(Gtk.Label(label="Inicio (MM:SS):"))
        self.corte_inicio = Gtk.Entry()
        self.corte_inicio.set_text("00:00")
        self.corte_inicio.set_width_chars(7)
        fila_tiempos.append(self.corte_inicio)
        fila_tiempos.append(Gtk.Label(label="Fin (MM:SS):"))
        self.corte_fin = Gtk.Entry()
        self.corte_fin.set_text("00:30")
        self.corte_fin.set_width_chars(7)
        fila_tiempos.append(self.corte_fin)
        caja.append(fila_tiempos)

        label_salida = Gtk.Label(label="Archivo de salida:")
        label_salida.set_halign(Gtk.Align.START)
        caja.append(label_salida)

        fila_salida = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.corte_salida = Gtk.Entry()
        self.corte_salida.set_placeholder_text("Se guardará como …_corte.mp3")
        self.corte_salida.set_hexpand(True)
        fila_salida.append(self.corte_salida)
        boton_salida = Gtk.Button(label="Guardar como…")
        boton_salida.connect("clicked", self._al_elegir_salida)
        fila_salida.append(boton_salida)
        caja.append(fila_salida)

        barra_corte = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        barra_corte.set_halign(Gtk.Align.CENTER)
        self.boton_cortar = Gtk.Button(label="Cortar y guardar")
        self.boton_cortar.add_css_class("suggested-action")
        self.boton_cortar.connect("clicked", self._al_cortar)
        barra_corte.append(self.boton_cortar)
        caja.append(barra_corte)

        self.corte_progreso = Gtk.ProgressBar()
        self.corte_progreso.set_show_text(True)
        self.corte_progreso.set_text("Listo")
        self.corte_progreso.set_fraction(0.0)
        caja.append(self.corte_progreso)

        self.corte_estado = Gtk.Label(label="Listo.")
        self.corte_estado.add_css_class("dim-label")
        self.corte_estado.set_wrap(True)
        self.corte_estado.set_halign(Gtk.Align.START)
        caja.append(self.corte_estado)

        return caja

    def _al_elegir_carpeta(self, boton):
        dialogo = Gtk.FileDialog()
        dialogo.select_folder(self.win, None, self._carpeta_elegida)

    def _carpeta_elegida(self, dialogo, resultado):
        try:
            archivo = dialogo.select_folder_finish(resultado)
            ruta = archivo.get_path()
            if ruta:
                self.etiqueta_carpeta.set_label(ruta)
        except GLib.Error:
            pass

    def _al_elegir_mp3(self, boton):
        dialogo = Gtk.FileDialog()
        filtro = Gtk.FileFilter()
        filtro.set_name("MP3")
        filtro.add_pattern("*.mp3")
        filtros = Gio.ListStore.new(Gtk.FileFilter)
        filtros.append(filtro)
        dialogo.set_filters(filtros)
        dialogo.open(self.win, None, self._mp3_elegido)

    def _mp3_elegido(self, dialogo, resultado):
        try:
            archivo = dialogo.open_finish(resultado)
            ruta = archivo.get_path()
            if ruta:
                self.corte_entrada.set_text(ruta)
                if not self.corte_salida.get_text().strip():
                    base, _ = os.path.splitext(ruta)
                    self.corte_salida.set_text(f"{base}_corte.mp3")
                self._actualizar_duracion(ruta)
        except GLib.Error:
            pass

    def _al_elegir_salida(self, boton):
        dialogo = Gtk.FileDialog()
        dialogo.set_initial_name(os.path.basename(self.corte_salida.get_text().strip()) or "corte.mp3")
        carpeta = os.path.dirname(self.corte_salida.get_text().strip())
        if carpeta and os.path.isdir(carpeta):
            try:
                gio_file = Gio.File.new_for_path(carpeta)
                dialogo.set_initial_folder(gio_file)
            except Exception:
                pass
        dialogo.save(self.win, None, self._salida_elegida)

    def _salida_elegida(self, dialogo, resultado):
        try:
            archivo = dialogo.save_finish(resultado)
            ruta = archivo.get_path()
            if ruta:
                if not ruta.lower().endswith(".mp3"):
                    ruta += ".mp3"
                self.corte_salida.set_text(ruta)
        except GLib.Error:
            pass

    @staticmethod
    def _formatear_tiempo(segundos):
        segundos = int(round(segundos))
        m, s = divmod(segundos, 60)
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _parse_tiempo(texto):
        texto = texto.strip()
        if not texto:
            raise ValueError("vacío")
        partes = texto.split(":")
        if len(partes) == 1:
            if not re.fullmatch(r"\d+(\.\d+)?", partes[0]):
                raise ValueError("formato inválido")
            v = float(partes[0])
            if v < 0:
                raise ValueError("negativo")
            return v
        elif len(partes) == 2:
            m, s = partes
            if not m.isdigit() or not re.fullmatch(r"\d+(\.\d+)?", s):
                raise ValueError("formato inválido")
            m = int(m)
            s_val = float(s)
            if not (0 <= s_val < 60):
                raise ValueError("segundos 00-59")
            return m * 60 + s_val
        else:
            raise ValueError("usa MM:SS")

    @staticmethod
    def _obtener_duracion(ruta):
        if not shutil.which("ffprobe"):
            return None
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", ruta],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                return float(r.stdout.strip())
        except Exception:
            pass
        return None

    def _actualizar_duracion(self, ruta):
        dur = self._obtener_duracion(ruta)
        if dur is not None:
            GLib.idle_add(self.corte_duracion.set_label, f"Duración: {self._formatear_tiempo(dur)}  ({dur:.1f}s)")
        else:
            GLib.idle_add(self.corte_duracion.set_label, "")

    def _al_descargar(self, boton):
        url = self.entrada_url.get_text().strip()
        if not url:
            self.estado.set_label("Introduce una URL primero.")
            return
        if self._descargando:
            return
        self._descargando = True
        self._cancelar = False
        self.boton_descargar.set_sensitive(False)
        self.boton_cancelar.set_sensitive(True)
        self.progreso.set_fraction(0.0)
        formato = "mp3" if self.selector_formato.get_selected() == 0 else "m4a"
        carpeta = self.etiqueta_carpeta.get_label()
        hilo = threading.Thread(
            target=self._descargar, args=(url, formato, carpeta), daemon=True
        )
        hilo.start()

    def _al_cancelar(self, boton):
        self._cancelar = True
        self.estado.set_label("Cancelando…")

    def _hook_progreso(self, d):
        if self._cancelar:
            raise yt_dlp.utils.DownloadError("Descarga cancelada por el usuario.")
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            descargado = d.get("downloaded_bytes", 0)
            if total:
                fraccion = descargado / total
                texto = f"Descargando… {int(fraccion * 100)}%"
            else:
                fraccion = 0.0
                texto = "Descargando…"
            GLib.idle_add(self.progreso.set_fraction, fraccion)
            GLib.idle_add(self.progreso.set_text, texto)
        elif d["status"] == "finished":
            GLib.idle_add(self.progreso.set_text, "Convirtiendo…")

    def _descargar(self, url, formato, carpeta):
        runtimes = {"deno": {}}
        for rt in ("bun", "node"):
            if shutil.which(rt):
                runtimes[rt] = {}
        opciones = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(carpeta, "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": formato,
                    "preferredquality": "192",
                }
            ],
            "progress_hooks": [self._hook_progreso],
            "noplaylist": True,
            "quiet": True,
            "js_runtimes": runtimes,
        }
        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url, download=True)
                titulo = info.get("title", "audio")
                mensaje = f"Listo: {titulo}.{formato}"
                GLib.idle_add(self._fin_descarga, True, mensaje)
        except yt_dlp.utils.DownloadError as e:
            mensaje = str(e)
            if "cancelada por el usuario" in mensaje:
                mensaje = "Descarga cancelada."
            GLib.idle_add(self._fin_descarga, False, mensaje)
        except Exception as e:
            GLib.idle_add(self._fin_descarga, False, f"Error inesperado: {e}")

    def _fin_descarga(self, exito, mensaje):
        self._descargando = False
        self.boton_descargar.set_sensitive(True)
        self.boton_cancelar.set_sensitive(False)
        self.estado.set_label(mensaje)
        if exito:
            self.progreso.set_fraction(1.0)
        elif "cancelada" not in mensaje.lower():
            self.progreso.set_fraction(0.0)

    def _al_cortar(self, boton):
        if self._cortando:
            return
        entrada = self.corte_entrada.get_text().strip()
        salida = self.corte_salida.get_text().strip()
        inicio_txt = self.corte_inicio.get_text().strip()
        fin_txt = self.corte_fin.get_text().strip()

        if not entrada or not os.path.isfile(entrada):
            self.corte_estado.set_label("Selecciona un archivo MP3 válido.")
            return
        if not entrada.lower().endswith(".mp3"):
            self.corte_estado.set_label("El archivo debe ser MP3.")
            return
        if not salida:
            self.corte_estado.set_label("Selecciona el archivo de salida.")
            return
        if not salida.lower().endswith(".mp3"):
            salida += ".mp3"
            self.corte_salida.set_text(salida)
        carpeta_salida = os.path.dirname(os.path.abspath(salida))
        if carpeta_salida and not os.path.isdir(carpeta_salida):
            self.corte_estado.set_label("La carpeta de salida no existe.")
            return
        try:
            inicio = self._parse_tiempo(inicio_txt)
        except Exception:
            self.corte_estado.set_label("Inicio inválido. Usa MM:SS (ej. 01:30).")
            return
        try:
            fin = self._parse_tiempo(fin_txt)
        except Exception:
            self.corte_estado.set_label("Fin inválido. Usa MM:SS (ej. 02:15).")
            return
        if inicio >= fin:
            self.corte_estado.set_label("El inicio debe ser menor que el fin.")
            return
        if not shutil.which("ffmpeg"):
            self.corte_estado.set_label("ffmpeg no encontrado. Instálalo para cortar MP3.")
            return
        dur = self._obtener_duracion(entrada)
        if dur is not None and fin > dur + 0.1:
            self.corte_estado.set_label(f"El fin ({self._formatear_tiempo(fin)}) supera la duración ({self._formatear_tiempo(dur)}).")
            return
        if dur is not None and inicio >= dur:
            self.corte_estado.set_label("El inicio supera la duración del archivo.")
            return

        self._cortando = True
        self.boton_cortar.set_sensitive(False)
        self.corte_progreso.set_fraction(0.0)
        self.corte_progreso.set_text("Cortando…")
        self.corte_estado.set_label(f"Cortando {self._formatear_tiempo(inicio)} → {self._formatear_tiempo(fin)}…")
        threading.Thread(target=self._cortar, args=(entrada, salida, inicio, fin), daemon=True).start()

        GLib.timeout_add(100, self._pulso_corte)

    def _pulso_corte(self):
        if self._cortando:
            self.corte_progreso.pulse()
            return True
        return False

    def _cortar(self, entrada, salida, inicio, fin):
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", entrada,
                "-ss", str(inicio),
                "-to", str(fin),
                "-c:a", "libmp3lame",
                "-q:a", "0",
                salida
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip()[:600] or "ffmpeg falló")
            if not os.path.isfile(salida) or os.path.getsize(salida) == 0:
                raise RuntimeError("no se generó el archivo de salida")
            GLib.idle_add(self._fin_corte, True, salida, inicio, fin)
        except Exception as e:
            GLib.idle_add(self._fin_corte, False, str(e), inicio, fin)

    def _fin_corte(self, exito, info, inicio, fin):
        self._cortando = False
        self.boton_cortar.set_sensitive(True)
        if exito:
            salida = info
            self.corte_progreso.set_fraction(1.0)
            self.corte_progreso.set_text("Completado")
            self.corte_estado.set_label(f"Guardado: {os.path.basename(salida)} ({self._formatear_tiempo(inicio)} → {self._formatear_tiempo(fin)})")
        else:
            self.corte_progreso.set_fraction(0.0)
            self.corte_progreso.set_text("Error")
            self.corte_estado.set_label(f"Error al cortar: {info}")


if __name__ == "__main__":
    app = ConverTube()
    app.run(None)
