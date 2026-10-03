# El Rayo de Júpiter · Lista de precios

App liviana para buscar productos, precios y stock desde el celular, pensada para usar en el local
(empleados del salón y clientes). Se actualiza sola con el PDF de precios del Google Drive.

## Cómo funciona

1. Tres veces por día (7, 10 y 13 h) GitHub descarga el PDF del Drive.
2. `scripts/actualizar.py` lee los productos (código, descripción, precio, bulto y categoría).
3. Genera `index.html` con los datos adentro: la app carga en un solo pedido (~60 KB, ~15 KB comprimido).
4. Si la lista cambió, guarda los cambios y GitHub Pages publica la versión nueva en un minuto.

**Stock:** si el producto figura con precio, hay stock. Si figura con `$ -`, se muestra "Sin stock".

## Puesta en marcha (una sola vez)

1. Crear un repositorio en GitHub (puede ser público) y subir todos estos archivos.
2. **Settings → Pages →** Source: *Deploy from a branch*, Branch: `main` / `(root)` → Save.
3. **Settings → Actions → General →** Workflow permissions: *Read and write permissions* → Save.
4. **Actions → Actualizar lista de precios → Run workflow** para probar la primera actualización.
5. La app queda en `https://<usuario>.github.io/<repositorio>/`. Desde el celular: menú → *Agregar a pantalla de inicio*.

## Importante sobre el PDF del Drive

- El archivo tiene que estar compartido como **"Cualquier persona con el enlace"**.
- Para actualizarlo hay que **reemplazar el mismo archivo** (en Drive: clic derecho → *Administrar versiones* →
  *Subir versión nueva*). Si suben un archivo nuevo, cambia el ID y hay que actualizar `DRIVE_ID` en el script.
- Si un día el PDF cambia de formato y se leen menos de 50 productos, el script no publica nada
  y la app sigue mostrando la última lista buena.

## Ajustes

- **Ocultar precios de alguna marca:** en `scripts/actualizar.py`, completar `OCULTAR_PRECIO_DE`
  (ej. `["MANAOS", "NEVARES", "PITUSAS"]`). Esos productos muestran "Consultá el precio".
- **Fotos:** ver `img/LEEME.txt`.
- **Logo e íconos:** están en `assets/` y se incrustan en la página al generarla. Para cambiar uno, reemplazá el archivo con el mismo nombre.
- **Diseño o textos:** editar `scripts/plantilla.html` (no `index.html`, que se regenera).
- **Probar en la compu:** `pip install pdfplumber` y `python scripts/actualizar.py lista.pdf`.
