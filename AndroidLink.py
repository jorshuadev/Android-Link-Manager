import os
import sys
import subprocess
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import threading

# -----------------------
# RUTAS (compatible con PyInstaller)
# -----------------------
if getattr(sys, "frozen", False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(__file__)

ADB_PATH = os.path.join(BASE_PATH, "scrcpy", "adb.exe")
SCRCPY_PATH = os.path.join(BASE_PATH, "scrcpy", "scrcpy.exe")
ICON_PATH = os.path.join(BASE_PATH, "icon.ico")
ICON_IMG = os.path.join(BASE_PATH, "icon.png")

# -----------------------
# CONFIGURACIÓN VISUAL
# -----------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

app = ctk.CTk()
app.title("Android Link Manager — DEVA")
app.geometry("560x560")
app.resizable(False, False)

# Ícono de la app
if os.path.exists(ICON_PATH):
    try:
        app.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"No se pudo aplicar el ícono: {e}")

# -----------------------
# FUNCIONES ADB
# -----------------------
def ejecutar_adb(args, timeout=10):
    try:
        # Hide console window on Windows
        startupinfo = None
        creationflags = 0
        
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(
            [ADB_PATH] + args, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            creationflags=creationflags
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def obtener_dispositivo():
    rc, out, err = ejecutar_adb(["devices"])
    if rc != 0:
        return None
    lines = out.strip().splitlines()
    devices = [l for l in lines if "\tdevice" in l]
    return devices[0].split("\t")[0] if devices else None

# -----------------------
# GUÍA VISUAL
# -----------------------
def abrir_guia_estilizada(parent=None):
    guia = ctk.CTkToplevel(parent or app)
    guia.title("Guía — Activar Depuración USB")
    guia.geometry("520x420")
    guia.resizable(False, False)
    guia.attributes('-topmost', True)

    if os.path.exists(ICON_PATH):
        try:
            guia.iconbitmap(ICON_PATH)
        except:
            pass

    frame = ctk.CTkFrame(guia)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(frame, text="Cómo activar la depuración USB", font=("Segoe UI", 18, "bold")).pack(pady=(10, 5))
    ctk.CTkLabel(frame, text=(
        "1. Abre Ajustes → Acerca del teléfono.\n"
        "2. Toca 'Número de compilación' 7 veces.\n"
        "3. Regresa a Opciones de desarrollador.\n"
        "4. Activa 'Depuración USB'.\n"
        "5. Conecta el cable de datos (no solo carga).\n"
        "6. Acepta la solicitud 'Permitir depuración USB'.\n"
        "7. Si no se detecta, cambia de puerto USB o cable.\n"
    ), justify="left").pack(padx=10, pady=10)

    ctk.CTkButton(frame, text="Cerrar", command=guia.destroy, width=120).pack(pady=(10, 5))

# -----------------------
# FUNCIONES PRINCIPALES
# -----------------------
def verificar_o_mostrar_guia():
    device = obtener_dispositivo()
    if device:
        messagebox.showinfo("Conectado", f"✅ Dispositivo detectado: {device}")
    else:
        abrir_guia_estilizada(app)

def conectar_unificado():
    ip = entry_ip.get().strip()
    control_enabled = control_var.get()
    fullscreen_enabled = fullscreen_var.get()
    audio_enabled = audio_var.get()

    if ip:
        ejecutar_adb(["tcpip", "5555"])
        ejecutar_adb(["connect", ip])
        device = obtener_dispositivo()
        if device:
            lanzar_scrcpy(control_enabled, fullscreen_enabled)
        else:
            messagebox.showwarning("Advertencia", "Conexión WiFi realizada, pero no se detecta el dispositivo.")
    else:
        device = obtener_dispositivo()
        if not device:
            abrir_guia_estilizada(app)
            return
        lanzar_scrcpy(control_enabled, fullscreen_enabled)

scrcpy_process = None

def lanzar_scrcpy(control_enabled, fullscreen_enabled):
    global scrcpy_process
    
    if not os.path.exists(SCRCPY_PATH):
        messagebox.showerror("Error", f"scrcpy.exe no encontrado en:\n{SCRCPY_PATH}")
        return
    
    # Kill previous scrcpy process if it exists
    if scrcpy_process:
        try:
            scrcpy_process.terminate()
            scrcpy_process.wait(timeout=2)
        except:
            pass
    
    bitrate = bitrate_option.get()
    resolucion = resolucion_option.get()
    fps = fps_option.get()
    audio_enabled = audio_var.get()

    args = [SCRCPY_PATH,
            "--video-bit-rate", bitrate,
            "--max-fps", fps,
            "--max-size", resolucion]

    if fullscreen_enabled:
        args.append("--fullscreen")
    if not control_enabled:
        args.append("--no-control")
    
    if audio_enabled:
        args += ["--audio-source", "output", "--audio-bit-rate", "128K"]
    else:
        args.append("--no-audio")

    try:
        # Hide console window on Windows
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
        
        scrcpy_process = subprocess.Popen(args, creationflags=creationflags)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar scrcpy.\n{e}")

# -----------------------
# INTERFAZ
# -----------------------
header = ctk.CTkFrame(app)
header.pack(fill="x", padx=12, pady=(12,8))

if os.path.exists(ICON_IMG):
    try:
        pil_image = Image.open(ICON_IMG)
        logo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(32, 32))
        ctk.CTkLabel(header, image=logo, text="").pack(side="left", padx=(6,10))
        app.logo_ref = logo
    except:
        pass

ctk.CTkLabel(header, text="Android Link Manager", font=("Segoe UI", 22, "bold")).pack(side="left", padx=6)

# Estado del dispositivo
dispositivo_label = ctk.CTkLabel(app, text="⏳ Buscando dispositivo...", font=("Segoe UI", 13))
dispositivo_label.pack(anchor="w", padx=18, pady=(0,10))

# Opciones
section = ctk.CTkFrame(app)
section.pack(fill="x", padx=12, pady=6)

ctk.CTkLabel(section, text="⚙️ Opciones de calidad", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8,6))
ctk.CTkLabel(section, text="Resolución:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
resolucion_option = ctk.CTkOptionMenu(section, values=["720", "1080", "1440", "2160"])
resolucion_option.set("1080")
resolucion_option.grid(row=1, column=1, sticky="w", padx=8)

ctk.CTkLabel(section, text="Bitrate:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
bitrate_option = ctk.CTkOptionMenu(section, values=["2M", "4M", "8M", "16M", "32M"])
bitrate_option.set("8M")
bitrate_option.grid(row=2, column=1, sticky="w", padx=8)

ctk.CTkLabel(section, text="FPS:").grid(row=3, column=0, sticky="w", padx=8, pady=6)
fps_option = ctk.CTkOptionMenu(section, values=["30", "60", "90", "120"])
fps_option.set("60")
fps_option.grid(row=3, column=1, sticky="w", padx=8)

fullscreen_var = ctk.BooleanVar(value=False)
ctk.CTkCheckBox(section, text="Pantalla completa", variable=fullscreen_var).grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=(8,4))
control_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(section, text="Permitir control desde la PC", variable=control_var).grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(2,4))
audio_var = ctk.BooleanVar(value=False)
ctk.CTkCheckBox(section, text="Redirigir audio a la PC", variable=audio_var).grid(row=7, column=0, columnspan=2, sticky="w", padx=8, pady=(2,12))

# Conexión
ctk.CTkLabel(app, text="🌐 Conexión WiFi (opcional)", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(6,4))
entry_ip = ctk.CTkEntry(app, placeholder_text="Si pones una IP (192.168.x.x) usará WiFi, si no, dejar vacío para USB")
entry_ip.pack(fill="x", padx=18, pady=(0,12))

# Botones
buttons = ctk.CTkFrame(app)
buttons.pack(fill="x", padx=18, pady=(6,12))
ctk.CTkButton(buttons, text="🔍 Verificar conexión", command=verificar_o_mostrar_guia, width=240).grid(row=0, column=0, padx=(0,8), pady=6)
ctk.CTkButton(buttons, text="🔌 Conectar (USB / WiFi)", command=conectar_unificado, width=240).grid(row=0, column=1, padx=(8,0), pady=6)

footer = ctk.CTkLabel(app, text="© 2025 DEVA — Powered by ADB & Scrcpy", font=("Segoe UI", 10))
footer.pack(side="bottom", pady=10)

# -----------------------
# ACTUALIZAR ESTADO DE LA UI
# -----------------------
def actualizar_estado_ui():
    def actualizar_en_hilo():
        while True:
            try:
                device = obtener_dispositivo()
                if device:
                    dispositivo_label.configure(text=f"✅ Dispositivo conectado: {device}", text_color="lightgreen")
                else:
                    dispositivo_label.configure(text="❌ Ningún dispositivo detectado", text_color="red")
            except Exception as e:
                dispositivo_label.configure(text="❌ Error al verificar dispositivo", text_color="red")
            
            import time
            time.sleep(2)
    
    thread = threading.Thread(target=actualizar_en_hilo, daemon=True)
    thread.start()

actualizar_estado_ui()
app.mainloop()
