"""
audio_ecologia_ruso.py
Lee Ecologia_ruso.xlsx y genera un MP3 con SOLO voz rusa.

Flujo por párrafo:
  1. 🇷🇺 Voz rusa lee el párrafo
  2. ⏸️  Pausa (2.0 s)
"""

import os, sys, time, subprocess, traceback
import pandas as pd

# ── Configura estas rutas ────────────────────────────────────────────────────
FFMPEG     = r"C:\Users\guita\anaconda3\Library\bin\ffmpeg.exe"
XLSX_PATH  = r"C:\Users\guita\Downloads\Texto_idioma.xlsx"
OUTPUT_MP3 = r"C:\Users\guita\Downloads\Audio_idioma_Ruso.mp3"
TEMP_DIR   = os.path.join(os.getcwd(), "temp_audio_ecologia")
# ────────────────────────────────────────────────────────────────────────────

VOZ_RUSA = "ru-RU-DmitryNeural"

os.makedirs(TEMP_DIR, exist_ok=True)
print(f"Voz rusa: {VOZ_RUSA}\n")


def tts(texto, voz, archivo):
    if os.path.exists(archivo):
        os.remove(archivo)
    script = f"""
import asyncio, edge_tts
async def run():
    c = edge_tts.Communicate({repr(texto)}, {repr(voz)}, rate="-10%")
    await c.save({repr(archivo)})
asyncio.run(run())
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode())
    for _ in range(60):
        time.sleep(0.1)
        if os.path.exists(archivo) and os.path.getsize(archivo) > 1000:
            return
    raise RuntimeError(f"Archivo no generado: {archivo}")


def concatenar_mp3s(lista_mp3, mp3_out):
    lista_txt = mp3_out + "_lista.txt"
    with open(lista_txt, "w", encoding="utf-8") as f:
        for p in lista_mp3:
            f.write(f"file '{p}'\n")
    result = subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", lista_txt, "-c", "copy", mp3_out
    ], capture_output=True, timeout=120)
    os.remove(lista_txt)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode())


def hacer_silencio(nombre, duracion):
    path = os.path.join(TEMP_DIR, nombre)
    subprocess.run([
        FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", str(duracion), "-codec:a", "libmp3lame", path
    ], capture_output=True)
    return path

silencio = hacer_silencio("silencio.mp3", 2.0)
print("Silencio generado OK\n")

print("Leyendo Excel...")
df = pd.read_excel(XLSX_PATH)
df.columns = df.columns.str.strip().str.lower()
col_texto = [c for c in df.columns if 'texto' in c or 'ruso' in c or 'ru' in c][0]
print(f"Columna texto: '{col_texto}'")
print(f"Total párrafos: {len(df)}\n")

mp3s = []
exitosas = 0

for i, row in df.iterrows():
    try:
        texto = str(row[col_texto]).strip()
        if not texto or texto == 'nan':
            continue

        file_parr  = os.path.join(TEMP_DIR, f"{i}_parrafo.mp3")
        file_bloque = os.path.join(TEMP_DIR, f"{i}_bloque.mp3")

        tts(texto, VOZ_RUSA, file_parr)
        concatenar_mp3s([file_parr, silencio], file_bloque)

        mp3s.append(file_bloque)
        exitosas += 1
        print(f"OK [{i+1}/{len(df)}] — {texto[:70]}...")

    except Exception as e:
        print(f"ERROR párrafo {i+1}: {e}")
        traceback.print_exc()

print(f"\nPárrafos exitosos: {exitosas}/{len(df)}")

if mp3s:
    print("Concatenando MP3 final...")
    concatenar_mp3s(mp3s, OUTPUT_MP3)
    print(f"MP3 final: {os.path.getsize(OUTPUT_MP3):,} bytes")
    print(f"\n✅ Listo! Guardado en:\n{OUTPUT_MP3}")
else:
    print("No se generaron audios.")
