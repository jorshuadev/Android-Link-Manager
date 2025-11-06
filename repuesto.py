import os
import sys
import subprocess
import customtkinter as ctk
from tkinter import messagebox, PhotoImage

# -----------------------
# RUTAS (soporta PyInstaller)
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

# Evita reescalado que causa borrosidad
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

app = ctk.CTk()
app.title("Android Link Manager — DEVA")
app.geometry("560x560")
app.resizable(False, False)

# Aplica el ícono de la aplicación
if os.path.exists(ICON_PATH):
    try:
        app.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"No se pudo aplicar el ícono: {e}")

# -----------------------
# UTILIDADES / ADB
# -----------------------
def ejecutar_adb(args, timeout=8):
    try:
        proc = subprocess.run([ADB_PATH] + args, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
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
# GUÍA (una sola instancia, siempre al frente)
# -----------------------
guia_window = None

def abrir_guia_estilizada(parent=None):
    global guia_window
    if guia_window and guia_window.winfo_exists():
        guia_window.lift()
        guia_window.focus_force()
        return

    guia_window = ctk.CTkToplevel(parent or app)
    guia_window.title("Guía rápida — Activar Depuración USB")
    guia_window.geometry("500x420")
    guia_window.resizable(False, False)
    guia_window.attributes('-topmost', True)

    # Ícono en la ventana de guía
    if os.path.exists(ICON_PATH):
        try:
            guia_window.iconbitmap(ICON_PATH)
        except:
            pass

    header = ctk.CTkFrame(guia_window)
    header.pack(fill="x", padx=12, pady=(12,6))

    if os.path.exists(ICON_IMG):
        try:
            logo_img = PhotoImage(file=ICON_IMG)
            ctk.CTkLabel(header, image=logo_img, text="").pack(side="left", padx=(6,10))
            guia_window.logo_ref = logo_img  # evitar recolección
        except:
            pass

    ctk.CTkLabel(header, text="Cómo activar Depuración USB (ADB)", font=("Segoe UI", 18, "bold")).pack(side="left", padx=6)

    from tkinter import Frame, Text, Scrollbar, RIGHT, Y, LEFT, BOTH, END
    content_wrap = Frame(guia_window)
    content_wrap.pack(expand=True, fill=BOTH, padx=6, pady=6)

    try:
        modo = ctk.get_appearance_mode()
        bg_color = "#1f1f1f" if modo == "Dark" else "#f0f0f0"
    except Exception:
        bg_color = "#1f1f1f"

    text = Text(content_wrap, wrap="word", padx=12, pady=12, bd=0, relief="flat", font=("Segoe UI", 14),
                background=bg_color,
                foreground="#e6eef8" if bg_color == "#1f1f1f" else "#1f1f1f",
                insertbackground="#e6eef8" if bg_color == "#1f1f1f" else "#1f1f1f")
    scrollbar = Scrollbar(content_wrap, command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    #scrollbar.pack(side=RIGHT, fill=Y)
    text.pack(side=LEFT, expand=True, fill=BOTH)

    steps = (
        "1️ Abre Ajustes (Settings) en tu teléfono.\n\n"
        "2️ Ve a 'Acerca del teléfono' o 'About phone'.\n\n"
        "3️ Busca 'Número de compilación' / 'Build number' y tócala 7 veces.\n"
        "   → Aparecerá: '¡Ahora eres desarrollador!'\n\n"
        "4️ Regresa y abre 'Opciones de desarrollador' / 'Developer options'.\n\n"
        "5️ Activa 'Depuración USB'.\n"
        "   → Al conectar por USB aparecerá una solicitud.\n"
        "   → Acepta y marca 'Permitir siempre desde este equipo'.\n\n"
        "6️ Conecta por cable de datos (no solo carga) y selecciona 'Transferencia de archivos (MTP)'.\n\n"
        "7️ Si ADB no detecta, instala drivers del fabricante o universales.\n"
        "   Recomendación: cambia de puerto USB si no funciona.\n\n"
        "Si aparece 'unauthorized', acepta la solicitud en tu teléfono."
    )
    text.insert(END, steps)
    text.configure(state="disabled")

    footer = ctk.CTkFrame(guia_window)
    footer.pack(fill="x", padx=12, pady=(6,12))
    ctk.CTkButton(footer, text="Cerrar", command=guia_window.destroy, width=120).pack(side="right", padx=8)

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
        rc, out, err = ejecutar_adb(["tcpip", "5555"])
        rc2, out2, err2 = ejecutar_adb(["connect", ip])
        device_after = obtener_dispositivo()
        if device_after:
            lanzar_scrcpy(control_enabled, fullscreen_enabled, audio_enabled)
        else:
            messagebox.showwarning("Advertencia", "Conexión por WiFi realizada, pero ADB no lista el dispositivo.")
            if messagebox.askyesno("Intentar", "¿Deseas intentar abrir scrcpy de todas formas?"):
                lanzar_scrcpy(control_enabled, fullscreen_enabled, audio_enabled)
    else:
        device = obtener_dispositivo()
        if not device:
            abrir_guia_estilizada(app)
            return
        lanzar_scrcpy(control_enabled, fullscreen_enabled, audio_enabled)

def lanzar_scrcpy(control_enabled: bool, fullscreen_enabled: bool, audio_enabled: bool):
    bitrate = bitrate_option.get()
    resolucion = resolucion_option.get()
    fps = fps_option.get()
    orientation = orientation_var.get()

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

    if orientation == "Vertical":
        args += ["--lock-video-orientation", "0"]
    elif orientation == "Horizontal":
        args += ["--lock-video-orientation", "1"]

    try:
        subprocess.Popen(args)
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró scrcpy.exe.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo ejecutar scrcpy.\nDetalles:\n{e}")

# -----------------------
# INTERFAZ
# -----------------------
header = ctk.CTkFrame(app)
header.pack(fill="x", padx=12, pady=(12,8))

if os.path.exists(ICON_IMG):
    try:
        logo = PhotoImage(file=ICON_IMG)
        ctk.CTkLabel(header, image=logo, text="").pack(side="left", padx=(6,10))
        app.logo_ref = logo
    except:
        pass

ctk.CTkLabel(header, text="Android Link Manager", font=("Segoe UI", 22, "bold")).pack(side="left", padx=(6,0))

dispositivo_label = ctk.CTkLabel(app, text="⏳ Buscando dispositivo...", font=("Segoe UI", 13))
dispositivo_label.pack(anchor="w", padx=18, pady=(0,10))

section = ctk.CTkFrame(app)
section.pack(fill="x", padx=12, pady=6)

ctk.CTkLabel(section, text="⚙️ Opciones de calidad", font=("Segoe UI", 15, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8,6))
ctk.CTkLabel(section, text="Resolución máx:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
resolucion_option = ctk.CTkOptionMenu(section, values=["720", "1080", "1440", "2160"], width=120)
resolucion_option.set("1080")
resolucion_option.grid(row=1, column=1, sticky="w", padx=8)

ctk.CTkLabel(section, text="Bitrate (video):").grid(row=2, column=0, sticky="w", padx=8, pady=6)
bitrate_option = ctk.CTkOptionMenu(section, values=["2M", "4M", "8M", "16M", "32M"], width=120)
bitrate_option.set("8M")
bitrate_option.grid(row=2, column=1, sticky="w", padx=8)

ctk.CTkLabel(section, text="FPS máx:").grid(row=3, column=0, sticky="w", padx=8, pady=6)
fps_option = ctk.CTkOptionMenu(section, values=["30", "60", "90", "120"], width=120)
fps_option.set("60")
fps_option.grid(row=3, column=1, sticky="w", padx=8)

ctk.CTkLabel(section, text="Orientación:").grid(row=4, column=0, sticky="w", padx=8, pady=6)
orientation_var = ctk.StringVar(value="Automático")
ctk.CTkOptionMenu(section, values=["Automático", "Vertical", "Horizontal"], variable=orientation_var, width=120).grid(row=4, column=1, sticky="w", padx=8)

fullscreen_var = ctk.BooleanVar(value=False)
ctk.CTkCheckBox(section, text="Pantalla completa", variable=fullscreen_var).grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=(8,4))
control_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(section, text="Permitir control desde la PC", variable=control_var).grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(2,4))
audio_var = ctk.BooleanVar(value=False)
ctk.CTkCheckBox(section, text="Redirigir audio a la PC", variable=audio_var).grid(row=7, column=0, columnspan=2, sticky="w", padx=8, pady=(2,12))

ctk.CTkLabel(app, text="🌐 Conexión WiFi (opcional)", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=18, pady=(6,4))
entry_ip = ctk.CTkEntry(app, placeholder_text="Si pones una IP (192.168.x.x) usará WiFi, si no dejar vacío para USB")
entry_ip.pack(fill="x", padx=18, pady=(0,12))

buttons = ctk.CTkFrame(app)
buttons.pack(fill="x", padx=18, pady=(6,12))
ctk.CTkButton(buttons, text="🔍 Verificar conexión", command=verificar_o_mostrar_guia, width=240).grid(row=0, column=0, padx=(0,8), pady=6)
ctk.CTkButton(buttons, text="🔌 Conectar (USB / WiFi)", command=conectar_unificado, width=240).grid(row=0, column=1, padx=(8,0), pady=6)

footer = ctk.CTkLabel(app, text="© 2025 DEVA — Powered by ADB & Scrcpy", font=("Segoe UI", 10))
footer.pack(side="bottom", pady=10)

def actualizar_estado_ui():
    device = obtener_dispositivo()
    if device:
        dispositivo_label.configure(text=f"✅ Dispositivo conectado: {device}", text_color="lightgreen")
    else:
        dispositivo_label.configure(text="❌ Ningún dispositivo detectado", text_color="red")
    app.after(2000, actualizar_estado_ui)

actualizar_estado_ui()
app.mainloop()
