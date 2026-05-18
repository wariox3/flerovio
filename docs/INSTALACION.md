# Manual de instalación — Flerovio

Esta guía explica cómo instalar Flerovio en un computador Windows y cómo
usarlo por primera vez. Está pensada para usuarios sin experiencia técnica
previa.

---

## 1. Requisitos

- **Sistema operativo:** Windows 10 o Windows 11 (64 bits).
- **Espacio en disco:** aproximadamente 150 MB.
- **Conexión a internet:** necesaria para iniciar sesión y para recibir
  actualizaciones automáticas.
- **Cuenta activa** en Semántica ERP — Transporte (correo y contraseña).

---

## 2. Descargar el instalador

1. Abrir en el navegador la página de versiones:

   <https://github.com/wariox3/flerovio/releases/latest>

2. En la sección **Assets** (Archivos adjuntos), hacer clic en el archivo
   con el nombre similar a:

   ```
   flerovio-0.1.0-setup.exe
   ```

   El número de versión puede variar según la versión más reciente.

3. El archivo se descargará a la carpeta de **Descargas** del computador.

---

## 3. Ejecutar el instalador

### 3.1. Aviso de SmartScreen (importante)

La primera vez que se ejecute el instalador, Windows puede mostrar la
ventana azul **"Windows protegió tu PC"**. Esto es normal: ocurre porque
Flerovio todavía no incluye un certificado de firma comercial. **El archivo
es seguro**.

Para continuar:

1. Hacer clic en **"Más información"** (texto azul, debajo del mensaje).
2. Aparece un botón nuevo: **"Ejecutar de todas formas"**.
3. Hacer clic en ese botón.

> Si el antivirus muestra una alerta similar, marcar el archivo como
> seguro o pedirle al área de soporte que lo añada a la lista blanca.

### 3.2. Asistente de instalación

Una vez aceptado el aviso, aparece el instalador en español:

1. **Pantalla de bienvenida** — hacer clic en *Siguiente*.
2. **Carpeta de destino** — dejar la sugerida (`C:\Program Files\Flerovio`)
   o cambiarla si la política de la empresa lo requiere. *Siguiente*.
3. **Tareas adicionales** — marcar *"Crear un acceso directo en el
   escritorio"* si se quiere ese ícono. *Siguiente*.
4. **Resumen** — *Instalar*.
5. Esperar unos segundos a que se copien los archivos.
6. En la última pantalla, dejar marcada la opción *"Iniciar Flerovio"*
   y hacer clic en *Finalizar*.

---

## 4. Primer inicio de sesión

Al abrirse la aplicación se muestra el diálogo **"Iniciar sesión —
Flerovio"**:

1. **Correo**: el correo registrado en Semántica ERP.
2. **Contraseña**: la contraseña asociada a esa cuenta.
3. **Recordarme en este equipo** (opcional): si se marca, la próxima vez
   que se abra Flerovio entrará automáticamente sin pedir credenciales.

   > Marcar esta opción solo en equipos personales o de confianza.

4. Hacer clic en **Ingresar**.

Si las credenciales son correctas, se abre la ventana principal con el
nombre del usuario y de la empresa en la barra inferior.

### 4.1. ¿No puedo entrar?

| Mensaje | Causa probable | Qué hacer |
|---|---|---|
| *Credenciales inválidas* | Correo o contraseña incorrectos | Verificar mayúsculas y minúsculas, intentar de nuevo |
| *No se pudo conectar con el servidor* | Sin internet o cortafuegos bloqueando | Revisar conexión y permitir `api.semanticaapi.com.co` |
| *Error inesperado* | Problema interno | Cerrar y volver a abrir; si persiste, contactar a soporte |

---

## 5. Actualizaciones automáticas

Cada vez que se abre Flerovio, la aplicación consulta si hay una versión
más reciente publicada. Si la hay, muestra el diálogo **"Actualización
disponible"** con:

- El número de la nueva versión.
- La lista de cambios incluidos.
- Dos botones: **Instalar ahora** y **Más tarde**.

### Si se elige *Instalar ahora*

1. Se descarga el nuevo instalador (barra de progreso visible).
2. Flerovio se cierra automáticamente.
3. Se abre el asistente de instalación con la nueva versión.
4. Al terminar, Flerovio se reabre con los cambios aplicados.

### Si se elige *Más tarde*

La aplicación abre normalmente. El aviso volverá a aparecer la próxima
vez que se inicie Flerovio.

> No es necesario desinstalar manualmente la versión anterior: el nuevo
> instalador la reemplaza conservando la configuración del usuario.

---

## 6. Cerrar sesión

Para salir de la cuenta sin cerrar la aplicación:

1. Menú **Archivo → Cerrar sesión**.
2. Confirmar en el diálogo.
3. Vuelve a aparecer la pantalla de login, lista para que entre otro
   usuario o el mismo de nuevo.

---

## 7. Desinstalar Flerovio

1. Abrir **Configuración → Aplicaciones → Aplicaciones instaladas**.
2. Buscar **Flerovio** en la lista.
3. Hacer clic en los tres puntos y elegir **Desinstalar**.
4. Confirmar.

> La desinstalación no elimina los datos de la sesión guardados en el
> sistema. Para borrarlos completamente, revisar el **Administrador de
> credenciales de Windows** y eliminar la entrada `flerovio`.

---

## 8. Soporte

Si surge un problema que no se resuelve con esta guía:

- Anotar el mensaje exacto que muestra Flerovio.
- Anotar la versión instalada (visible en el menú **Ayuda → Acerca de
  Flerovio…**).
- Contactar al área de soporte de Semántica con esos datos.
