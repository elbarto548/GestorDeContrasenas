# 🔐 Gestor de Contraseñas Seguro - Versión Escritorio

Aplicación de escritorio nativa para gestionar contraseñas de forma segura con encriptación AES-256.

## Características

- **Encriptación AES-256** con derivación de clave PBKDF2 (100,000 iteraciones)
- **Contraseña maestra** única para acceder a todas tus contraseñas
- **Interfaz gráfica** intuitiva con búsqueda instantánea y categorización
- **Generador de contraseñas** seguras automático
- **Base de datos SQLite** local y encriptada

## Instalación

### Requisitos
- Python 3.7 o superior

### Dependencias
```bash
pip install cryptography pyperclip
```

## Uso

### Opción 1: Ejecutable (Recomendado)
1. Ve a `dist/`
2. Doble clic en `GestorContrasenas.exe`
3. Ingresa tu contraseña maestra

### Opción 2: Python
```bash
python password_desktop.py
```

### Primer uso
1. Ejecuta la aplicación
2. Crea una contraseña maestra (mínimo 8 caracteres)
3. La base de datos `passwords.db` se crea automáticamente

### Funciones principales
- **Agregar**: Clic en "➕ Agregar Contraseña"
- **Generar**: Clic en "🎲" para crear contraseñas seguras
- **Buscar**: Escribe en el campo de búsqueda
- **Copiar**: Clic en "📋" para copiar contraseña
- **Editar**: Doble clic en una contraseña
- **Eliminar**: Selecciona y clic en "🗑️ Eliminar"

## Seguridad

- Las contraseñas se encriptan con AES-256 antes de guardarlas
- Sin la contraseña maestra, es imposible acceder a los datos
- La memoria se limpia al cerrar sesión
- **Importante**: Si olvidas tu contraseña maestra, no hay recuperación (diseño de seguridad)

## Archivos

- `passwords.db` - Base de datos encriptada (se crea automáticamente)
- `GestorContrasenas.exe` - Ejecutable en `dist/`

## Solución de problemas

**La aplicación no abre**: Instala dependencias `pip install cryptography pyperclip`

**Error al copiar**: Verifica `pip install pyperclip`

**Olvidé contraseña maestra**: No hay recuperación por diseño de seguridad

## Backup

Copia regularmente el archivo `passwords.db` a una ubicación segura (USB, nube, etc.)
