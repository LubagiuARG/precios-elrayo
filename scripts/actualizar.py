"""
Lee la lista de precios en PDF de El Rayo de Júpiter y genera:
  - data/productos.json  (los datos, por si se quieren usar en otro lado)
  - index.html           (la app, con los datos incrustados: carga en un solo pedido)

Uso:
  python scripts/actualizar.py                 -> descarga el PDF desde Google Drive
  python scripts/actualizar.py lista.pdf       -> usa un PDF local
"""
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

import pdfplumber

RAIZ = Path(__file__).resolve().parent.parent
DRIVE_ID = "15RKEUQhmvjaL8b2lIzTJPayJHNaoMpD7"
URL_DRIVE = f"https://drive.google.com/uc?export=download&id={DRIVE_ID}"

# Marcas cuyo precio NO se muestra en la app (aparece "Consultá el precio").
# Ejemplo: ["MANAOS", "NEVARES", "PITUSAS"]. Vacío = se muestran todos.
OCULTAR_PRECIO_DE = []

RE_PRODUCTO = re.compile(r"^(\d+),\s*(.+?)\s*\$\s*([\d\.]+,\d{2}|-)\s*$")
RE_BULTO = re.compile(r"\(\s*(\d+)\s*\)")
RE_FECHA = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")
IGNORAR = ("DISTRIBUIDORA", "AV OTERO", "WHATSAPP", "PRECIOS", "CÓDIGO", "CODIGO")
CORRECCIONES = {
    "PAPELES HIEGIENICOS/COCINA": "PAPELES HIGIÉNICOS / COCINA",
    "APERITIVOS / BEBIDAS CON ALCOH": "APERITIVOS / BEBIDAS CON ALCOHOL",
    "CREMIGAL..": "CREMIGAL",
    "AZUCAR / ENDULZANTES": "AZÚCAR / ENDULZANTES",
    "LINEA COCA-COLA": "LÍNEA COCA-COLA",
}


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def bonito(s):
    """'FIAMBRES / QUESOS' -> 'Fiambres / quesos'"""
    s = CORRECCIONES.get(s.strip(), s.strip())
    s = s.capitalize()
    return s.replace("coca-cola", "Coca-Cola").replace("Coca-cola", "Coca-Cola")


def descargar(destino):
    req = urllib.request.Request(URL_DRIVE, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = r.read()
    if not datos.startswith(b"%PDF"):
        sys.exit("Lo descargado no es un PDF. ¿El archivo sigue compartido como "
                 "'Cualquier persona con el enlace'?")
    destino.write_bytes(datos)


def es_categoria(linea):
    return (linea == linea.upper()
            and not linea.startswith(IGNORAR)
            and not RE_FECHA.search(linea)
            and not linea.isdigit()
            and re.search(r"[A-ZÁÉÍÓÚÑ]", linea) is not None)


def leer_pdf(ruta):
    productos, fecha, categoria = [], None, "Varios"
    with pdfplumber.open(ruta) as pdf:
        for pagina in pdf.pages:
            for linea in (pagina.extract_text() or "").splitlines():
                linea = linea.strip()
                if not linea:
                    continue
                if fecha is None:
                    m = RE_FECHA.search(linea)
                    if m:
                        fecha = m.group(1)
                m = RE_PRODUCTO.match(linea)
                if m:
                    codigo, desc, precio = m.groups()
                    oculto = any(x in sin_tildes(desc.upper()) for x in OCULTAR_PRECIO_DE)
                    valor = None if precio == "-" else float(precio.replace(".", "").replace(",", "."))
                    bulto = RE_BULTO.search(desc)
                    productos.append({
                        "c": int(codigo),                                   # código
                        "d": re.sub(r"\s+", " ", RE_BULTO.sub("", desc)).strip(),  # descripción
                        "p": None if oculto else valor,                     # precio
                        "b": int(bulto.group(1)) if bulto else None,        # unidades por bulto
                        "cat": categoria,
                        "s": valor is not None,  # stock: sin precio en la lista = sin stock
                        "q": oculto,             # precio a consultar
                    })
                elif es_categoria(linea):
                    categoria = bonito(linea)
    return fecha, productos


def main():
    if len(sys.argv) > 1:
        pdf = Path(sys.argv[1])
    else:
        pdf = RAIZ / "data" / "lista.pdf"
        descargar(pdf)
    fecha, productos = leer_pdf(pdf)
    if len(productos) < 50:
        sys.exit(f"Solo se leyeron {len(productos)} productos: el formato del PDF puede "
                 "haber cambiado. No se actualiza nada.")

    datos = {"fecha": fecha, "productos": productos}
    (RAIZ / "data" / "productos.json").write_text(
        json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")

    # Fotos: img/<codigo>.webp (o .jpg). Solo se listan las que existen.
    imgs = {}
    for f in (RAIZ / "img").iterdir():
        if f.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png") and f.stem.isdigit():
            imgs[f.stem] = f.name

    plantilla = (RAIZ / "scripts" / "plantilla.html").read_text(encoding="utf-8")
    html = (plantilla
            .replace("/*DATOS*/null", json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
            .replace("/*IMAGENES*/{}", json.dumps(imgs)))
    # Logo e íconos van incrustados en la página: cero pedidos extra al abrir la app
    import base64
    for f in (RAIZ / "assets").iterdir():
        tipo = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}.get(f.suffix.lower())
        if tipo:
            html = html.replace("{{" + f.name + "}}", f"data:{tipo};base64,{base64.b64encode(f.read_bytes()).decode()}")
    (RAIZ / "index.html").write_text(html, encoding="utf-8")

    cats = {}
    for p in productos:
        cats[p["cat"]] = cats.get(p["cat"], 0) + 1
    print(f"Lista del {fecha}: {len(productos)} productos en {len(cats)} categorías, "
          f"{len(imgs)} fotos")
    for c, n in cats.items():
        print(f"  {n:4d}  {c}")


if __name__ == "__main__":
    main()
