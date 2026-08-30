# ConverTube

ConverTube es una aplicación con interfaz gráfica (GTK4 / libadwaita) que permite extraer el audio de un video de YouTube y guardarlo en formato **MP3** o **M4A**, usando [yt-dlp](https://github.com/yt-dlp/yt-dlp) y [ffmpeg](https://ffmpeg.org). Incluye además un editor para **cortar archivos MP3** locales con precisión.

## Características

- Interfaz sencilla y nativa basada en GTK4 + libadwaita con dos pestañas: **Descargar** y **Cortar MP3**
- Extracción de audio en MP3 o M4A
- Barra de progreso en tiempo real
- Selección de carpeta de destino (por defecto `~/Música`)
- Posibilidad de cancelar la descarga
- **Corte de MP3**: selecciona un archivo local, indica inicio y fin en formato `MM:SS` y guarda el fragmento recortado (re-encode preciso con `ffmpeg` via `libmp3lame`, validación con `ffprobe`)

## Requisitos

Distribución Debian o derivadas (Ubuntu, Mint, etc.) con:

- `python3` (≥ 3.10)
- `python3-gi`
- `gir1.2-gtk-4.0`
- `gir1.2-adw-1`
- `ffmpeg` (requerido tanto para descarga como para corte)

Todas las dependencias se instalan automáticamente al instalar el paquete `.deb`.

## Instalación

Descarga el paquete más reciente desde la página de [Releases](https://github.com/furichies/convertube/releases) e instálalo con:

```bash
sudo apt install ./convertube_1.1.0_all.deb
```

O alternativamente:

```bash
sudo dpkg -i convertube_1.1.0_all.deb
sudo apt -f install   # solo si faltan dependencias
```

## Uso

### Pestaña Descargar

1. Abre **ConverTube** desde el menú de aplicaciones o ejecuta `convertube` en una terminal.
2. Pega la URL del video de YouTube.
3. Elige el formato de salida (**MP3** o **M4A**).
4. Selecciona la carpeta de destino.
5. Pulsa **Descargar**.

### Pestaña Cortar MP3

1. Cambia a la pestaña **Cortar MP3**.
2. Pulsa **Examinar…** y selecciona un archivo `.mp3` (se muestra su duración total).
3. Indica **Inicio (MM:SS)** y **Fin (MM:SS)** — por ejemplo `00:30` → `01:15`.
4. Pulsa **Guardar como…** o edita la ruta de salida (por defecto `*_corte.mp3`).
5. Pulsa **Cortar y guardar** — el corte se ejecuta en segundo plano con `ffmpeg -c:a libmp3lame`.

Validaciones: el inicio debe ser menor que el fin, ambos en `MM:SS` (segundos `00-59`), y el fin no puede superar la duración del archivo.

## Desinstalación

```bash
sudo apt remove convertube
```

## Changelog

- **1.1.0** (2026-08-30): nueva pestaña "Cortar MP3" (selección de MP3, tiempos `MM:SS`, salida `*_corte.mp3`, re-encode `ffmpeg`), ventana ampliada, muestra duración vía `ffprobe`.
- **1.0.2** (2026-08-25): corrige empaquetado yt-dlp integrado, habilita runtimes JS.
- **1.0.1** (2026-08-25): incluye yt-dlp vendorizado, botón cerrar.
- **1.0.0** (2026-08-25): versión inicial.

## Licencia

Consulta el archivo de licencia incluido en el paquete (`/usr/share/doc/convertube/copyright`).
