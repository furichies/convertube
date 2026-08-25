# ConverTube

ConverTube es una aplicación con interfaz gráfica (GTK4 / libadwaita) que permite extraer el audio de un video de YouTube y guardarlo en formato **MP3** o **M4A**, usando [yt-dlp](https://github.com/yt-dlp/yt-dlp) y [ffmpeg](https://ffmpeg.org).

## Características

- Interfaz sencilla y nativa basada en GTK4 + libadwaita
- Extracción de audio en MP3 o M4A
- Barra de progreso en tiempo real
- Selección de carpeta de destino (por defecto `~/Música`)
- Posibilidad de cancelar la descarga

## Requisitos

Distribución Debian o derivadas (Ubuntu, Mint, etc.) con:

- `python3` (≥ 3.10)
- `python3-gi`
- `gir1.2-gtk-4.0`
- `gir1.2-adw-1`
- `ffmpeg`

Todas las dependencias se instalan automáticamente al instalar el paquete `.deb`.

## Instalación

Descarga el paquete más reciente desde la página de [Releases](https://github.com/furichies/convertube/releases) e instálalo con:

```bash
sudo apt install ./convertube_1.0.2_all.deb
```

O alternativamente:

```bash
sudo dpkg -i convertube_1.0.2_all.deb
sudo apt -f install   # solo si faltan dependencias
```

## Uso

1. Abre **ConverTube** desde el menú de aplicaciones o ejecuta `convertube` en una terminal.
2. Pega la URL del video de YouTube.
3. Elige el formato de salida (**MP3** o **M4A**).
4. Selecciona la carpeta de destino.
5. Pulsa **Descargar**.

## Desinstalación

```bash
sudo apt remove convertube
```

## Licencia

Consulta el archivo de licencia incluido en el paquete (`/usr/share/doc/convertube/copyright`).
