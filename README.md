# 🔐 Gestor de Contraseñas Seguro - Versión Escritorio

Aplicación de escritorio nativa intuitiva para gestionar contraseñas de forma segura y fácil de usar.

## Características

### 🔒 Seguridad
- **Encriptación AES-256**: Todas las contraseñas están encriptadas
- **Contraseña maestra**: Una sola contraseña para acceder a todas tus contraseñas
- **Derivación de clave PBKDF2**: Algoritmo robusto para derivar la clave de encriptación con 100,000 iteraciones
- **Base de datos SQLite**: Almacenamiento local y seguro
- **Limpieza de memoria**: Limpieza explícita de datos sensibles al cerrar sesión

### 🎨 Interfaz de Escritorio Moderna
- **Diseño intuitivo**: Interfaz gráfica amigable para cualquier usuario
- **Interfaz profesional**: Diseño moderno con colores y tipografía atractivos
- **Búsqueda instantánea**: Encuentra contraseñas rápidamente
- **Categorización**: Organiza tus contraseñas por categorías
- **Nativa**: Funciona como aplicación de Windows sin navegador

### ⚡ Funcionalidades
- **Generador de contraseñas**: Crea contraseñas seguras automáticamente
- **Copiado al portapapeles**: Copia usuario y contraseña con un clic
- **CRUD completo**: Agregar, editar, eliminar contraseñas
- **Filtrado por categoría**: Filtra contraseñas por categoría
- **Notas adicionales**: Agrega información extra a cada contraseña

## Instalación

### Requisitos
- Python 3.7 o superior

### Dependencias
```bash
pip install cryptography pyperclip
```

## Uso

### Opción 1: Archivo .exe (Recomendado - Más fácil)

#### Usar el ejecutable
1. Ve a la carpeta `GestorDeContraseñas/dist/`
2. Doble clic en `GestorContrasenas.exe`
3. Ingresa tu contraseña maestra
4. ¡Listo!

**Ventajas del .exe:**
- No necesitas Python instalado
- Solo doble clic para iniciar
- Funciona como cualquier programa de Windows
- Sin ventana de consola

### Opción 2: Desde código Python

#### Iniciar la aplicación de escritorio
```bash
python password_desktop.py
```

### Primer uso
1. Ejecuta `GestorContrasenas.exe` (o `python password_desktop.py`)
2. Ingresa una contraseña maestra (mínimo 8 caracteres)
3. ¡Listo! Tu caja fuerte está creada

### Usos posteriores
1. Doble clic en `GestorContrasenas.exe` (o ejecuta `python password_desktop.py`)
2. Ingresa tu contraseña maestra
3. Accede a todas tus contraseñas

## Guía de Uso

### 🔐 Pantalla de Login
- **Contraseña maestra**: Ingresa tu contraseña para acceder
- **Botón "Ingresar"**: Abre la caja fuerte

### 📋 Dashboard Principal

#### Agregar Contraseña
1. Clic en "➕ Agregar Contraseña"
2. Completa los campos:
   - **Sitio/Servicio**: Ejemplo: Gmail, Netflix, Banco
   - **Usuario/Email**: Tu usuario o email
   - **Contraseña**: Tu contraseña
   - **Categoría**: Selecciona una categoría
   - **Notas**: Información adicional (opcional)
3. Clic en "Guardar"

#### Generar Contraseña Segura
1. En el diálogo de agregar contraseña
2. Clic en el botón "🎲"
3. Se genera una contraseña de 16 caracteres con símbolos

#### Buscar Contraseñas
- **Búsqueda por texto**: Escribe en el campo de búsqueda
- Resultados filtrados en tiempo real

#### Copiar al Portapapeles
- Clic en "📋" para copiar la contraseña
- Clic en "👁" para mostrar/ocultar la contraseña

#### Editar Contraseña
- Doble clic en una contraseña para editar
- Modifica los campos deseados
- Clic en "Guardar"

#### Eliminar Contraseña
- Selecciona una contraseña en la lista
- Clic en "🗑️ Eliminar"
- Confirma la eliminación

## Categorías Predefinidas

- **General**: Contraseñas generales
- **Trabajo**: Contraseñas laborales
- **Personal**: Contraseñas personales
- **Finanzas**: Bancos, inversiones
- **Social**: Redes sociales
- **Compras**: E-commerce, tiendas

## Seguridad

### Cómo funciona la encriptación
1. Tu contraseña maestra se usa para derivar una clave usando PBKDF2-HMAC-SHA256
2. La clave derivada se usa para encriptar/desencriptar contraseñas con AES-256 (Fernet)
3. Las contraseñas encriptadas se guardan en la base de datos
4. Sin la contraseña maestra, es imposible acceder a las contraseñas
5. Al cerrar sesión, se limpia la memoria de datos sensibles

### Recomendaciones de seguridad
- **Contraseña maestra fuerte**: Usa una contraseña larga y única
- **No compartas tu contraseña maestra**: Solo tú debes conocerla
- **Backup regular**: Copia el archivo `passwords.db` regularmente
- **No uses la misma contraseña**: Para diferentes sitios

## Archivos Generados

- `passwords.db`: Base de datos SQLite con contraseñas encriptadas
- `GestorContrasenas.exe`: Ejecutable de la aplicación (en la carpeta dist/)

## Solución de Problemas

### Olvidé mi contraseña maestra
Lamentablemente, no hay forma de recuperar la contraseña maestra por diseño de seguridad. La encriptación no puede ser revertida sin la contraseña original.

### La aplicación no abre
- Verifica que Python esté instalado correctamente
- Instala las dependencias: `pip install cryptography pyperclip`
- Verifica que tkinter esté instalado (viene con Python)

### Error al copiar al portapapeles
- Verifica que pyperclip esté instalado: `pip install pyperclip`
- En Linux, puede requerir: `sudo apt-get install xclip`

## Ejemplos de Uso

### Ejemplo 1: Agregar contraseña de Gmail
1. Clic en "➕ Agregar Contraseña"
2. Sitio: "Gmail"
3. Usuario: "mi.email@gmail.com"
4. Contraseña: "mi_contraseña_segura"
5. Categoría: "Personal"
6. Clic en "Guardar"

### Ejemplo 2: Generar contraseña para Netflix
1. Clic en "➕ Agregar Contraseña"
2. Sitio: "Netflix"
3. Usuario: "mi.usuario"
4. Clic en "🎲" para generar contraseña
5. Categoría: "Social"
6. Clic en "Guardar"

### Ejemplo 3: Buscar contraseña del banco
1. Escribe "banco" en el campo de búsqueda
2. Se muestran todas las contraseñas relacionadas
3. Clic en " " para copiar la contraseña

### Ejemplo 4: Backup de contraseñas
1. Copia el archivo `passwords.db` a una ubicación segura
2. Guarda en un USB o servicio de almacenamiento en la nube
3. Para restaurar, simplemente reemplaza el archivo `passwords.db`

## Características Técnicas

### Encriptación
- **Algoritmo**: AES-256 (Fernet)
- **Derivación de clave**: PBKDF2-HMAC-SHA256
- **Iteraciones**: 100,000
- **Salt**: Fijo (para compatibilidad con contraseñas existentes)

### Base de Datos
- **Sistema**: SQLite3
- **Tablas**: passwords, categories, master_password
- **Índices**: Optimizados para búsqueda

### Interfaz Gráfica
- **Framework**: tkinter
- **Estilo**: Diseño personalizado con colores modernos
- **Widgets**: Treeview, Entry, Button, Combobox, Text

## Mejoras Futuras

- [ ] Autenticación de dos factores
- [ ] Sincronización en la nube
- [ ] Generador de contraseñas personalizable
- [ ] Auditoría de seguridad
- [ ] Indicador de fuerza de contraseña
- [ ] Importación desde navegadores
- [ ] Compartido seguro de contraseñas
- [ ] Expiración automática de contraseñas
- [ ] Notificación de contraseñas débiles

## Licencia

Este script es de código libre y puede ser modificado y distribuido según las necesidades del usuario.

## Aviso de Seguridad

Este software proporciona encriptación robusta, pero la seguridad depende de:
1. La fortaleza de tu contraseña maestra
2. La seguridad de tu computadora
3. No compartir tu contraseña maestra
4. Hacer backups regularmente

El autor no se hace responsable por pérdidas de datos debido a contraseñas maestras olvidadas o comprometidas.
