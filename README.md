# MultiRoblox 🔧🎮

**MultiRoblox** es una herramienta en Python que permite ejecutar múltiples instancias de Roblox cerrando de forma segura la handle `ROBLOX_singletonEvent` dentro del proceso `RobloxPlayerBeta.exe`.

Funciona de manera similar a "Close Handle" de **Process Explorer**, pero automatizado, centrado solo en ese evento y sin necesidad de matar el proceso.

<img width="1563" height="259" alt="ima34243ge" src="https://github.com/user-attachments/assets/79b8f8b5-9514-4a7b-a2fe-299ab36bb410" />

## ✅ Características

* Detecta si `RobloxPlayerBeta.exe` está en ejecución.
* Cierra la handle `ROBLOX_singletonEvent` automáticamente cuando Roblox está abierto.
* Permite ejecutar **múltiples instancias de Roblox** con diferentes cuentas.
* Enumeración de handles compatible con **Windows 64 bits** (usa SystemExtendedHandleInformation y fallback a Legacy si es necesario).
* Diseñado para ser **simple, ligero y rápido**.

---

## ⚠️ Requisitos

* **Windows 10/11 (x64)**
* **Python 3.8 o superior (x64)**
* Ejecutar **como Administrador** (para habilitar `SeDebugPrivilege`)
* Instalar dependencias:

  ```bash
  pip install -r requirements.txt
  ```

---

## 📦 Instalación

1. Clona el repositorio:

   ```bash
   git clone https://github.com/Kayy9961/MultiRoblox.git
   cd MultiRoblox
   ```
2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta el script (con privilegios de administrador):

   ```bash
   python main.py
   ```

---

## 🚀 Uso

* Si Roblox **no está abierto**, el programa mostrará un mensaje y se cerrará automáticamente en 5 segundos.
* Si Roblox **está abierto**, el script:

  1. Habilita los privilegios de depuración (`SeDebugPrivilege`)
  2. Enumera todas las handles activas del proceso
  3. Busca las handles tipo `Event` llamadas `ROBLOX_singletonEvent`
  4. Las cierra automáticamente 🎯

Una vez cerradas, podrás abrir otra instancia de Roblox sin interferencia del evento bloqueante.

---

## 🧠 Ejemplo de salida

```
🔧 Iniciando Roblox Event Closer

✅ Roblox detectado (PID 17048)
✨ Cerrada handle de '\Sessions\1\BaseNamedObjects\ROBLOX_singletonEvent'

📊 Handles analizadas: 174501
🎉 Cerradas 1 handle(s) del evento ROBLOX_singletonEvent correctamente.

💡 Fin del proceso.
```

---

## 📄 Archivos incluidos

* `main.py` — código principal
* `requirements.txt` — dependencias mínimas

Contenido de `requirements.txt`:

```
psutil>=5.9.0
```

---

## ⚙️ Personalización

Puedes editar las siguientes variables en `main.py`:

* `PROCESS_NAME` → Nombre del ejecutable (por defecto `RobloxPlayerBeta.exe`)
* `TARGET_EVENT_BASENAME` → Nombre del evento a cerrar
* `TARGET_VARIANTS` → Variantes de ruta a comparar (`BaseNamedObjects`, `Local`, etc.)

---

## ⚠️ Advertencia

Cerrar handles dentro de otro proceso puede provocar errores si el proceso las necesita. Úsalo bajo tu propia responsabilidad y **solo en tu propia máquina**.

No se recomienda su uso para evadir restricciones de software o romper términos de servicio de Roblox.

---

## 📜 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.

---

## 💬 Autor

Desarrollado por [Kayy9961](https://github.com/Kayy9961)

---

**Con MultiRoblox puedes iniciar Roblox en varias cuentas sin conflictos, de forma rápida y sencilla.**
