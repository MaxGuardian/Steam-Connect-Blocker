import ctypes
import sys
import os
import configparser
import webbrowser
import tkinter
import json
from customtkinter import *
import subprocess
from tkinter import messagebox, filedialog
from PIL import Image

commandName = 'Steam Connect Blocker'
badPathToggle = False

with open('_internal\\text.json', 'r', encoding='utf-8') as file:
    interfaceText = json.load(file)

# проверка прав админа
if not ctypes.windll.shell32.IsUserAnAdmin():
    if ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 0) <= 32:
        sys.exit(1)
    sys.exit(0)

def change_internet_access():
    global badPathToggle
    if badPathToggle:
        badPathToggle = False
        return

    # получаем путь и если он неправильный - ошибка
    steamPath = pathEntry.get()
    if not os.path.isfile(steamPath) or not len(steamPath) >= 9 or not steamPath[-9:] == "steam.exe":
        messagebox.showerror(interfaceText[f"{language_code}badPath_title"], interfaceText[f"{language_code}badPath_message"])
        badPathToggle = True
        blockSwitch.toggle()
        return

    steamPath = steamPath.replace('/', '\\')
    settings["Settings"] = {'SavedPath': steamPath, 'Language': language_code[:-1]}
    with open(interfaceText["data_path"], 'w') as configfile:
        settings.write(configfile)

    # Проверяем есть ли правило, если да и при этом рубильник на off - то удаляем правило, если же нет и рубильник на on - то добавляем правило, в остальных случаях ничего не делается
    check_command = f"netsh advfirewall firewall show rule name='{commandName}'"
    result = subprocess.run(['powershell', '-Command', check_command], capture_output=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW)

    blockConn = blockSwitch.get()
    # здесь блокируем панель смены пути если блокировка работает
    if blockConn == "on":
        pathEntry.configure(state="disabled")
        pathButton.configure(state="disabled")
    else:
        pathEntry.configure(state="normal")
        pathButton.configure(state="normal")

    if result.returncode == 0 and blockConn == "off":
        delete_command = f"netsh advfirewall firewall delete rule name='{commandName}'"
        subprocess.run(['powershell', '-Command', delete_command], creationflags=subprocess.CREATE_NO_WINDOW)
    elif result.returncode == 1 and blockConn == "on":
        add_command = f"netsh advfirewall firewall add rule name='{commandName}' dir=out program='{steamPath}' action=block description='{interfaceText[f"{language_code}ruleDescription"]}'"
        subprocess.run(['powershell', '-Command', add_command], creationflags=subprocess.CREATE_NO_WINDOW)

        if subprocess.run(['powershell', '-Command', check_command], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).returncode == 1:
            messagebox.showerror(interfaceText[f"{language_code}bad_add_title"], interfaceText[f"{language_code}bad_add_message"])
            pathEntry.configure(state="normal")
            pathButton.configure(state="normal")
            badPathToggle = True
            blockSwitch.toggle()
            return

    global image_label
    result = subprocess.run(['powershell', '-Command', check_command], capture_output=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW)

    image_label.destroy()
    image_label = CTkLabel(app, image=logoImage if result.returncode == 1 else blockLogoImage, text="")
    image_label.place(relx=0.5, rely=0.25, anchor="center")

def browse_file():
    file_path = filedialog.askopenfilename()
    if file_path == "":
        return
    if not os.path.isfile(file_path) or not len(file_path) >= 9 or not file_path[-9:] == "steam.exe":
        messagebox.showerror(interfaceText[f"{language_code}badPath_title"], interfaceText[f"{language_code}badPath_message"])
        return
    pathEntry.delete(0, tkinter.END)
    pathEntry.insert(0, file_path.replace('/', '\\'))

    settings["Settings"] = {'SavedPath': file_path, 'Language': language_code[:-1]}
    with open(interfaceText["data_path"], 'w') as configfile:
        settings.write(configfile)

def open_git():
    webbrowser.open("https://github.com/MaxGuardian/Steam-Connect-Blocker")

def open_info():
    messagebox.showinfo(title=interfaceText[f"{language_code}info_title"], message=interfaceText[f"{language_code}info_message"])

def change_language():
    global language_code
    language_code = ("ENG" if language_code[:-1] == "RU" else "RU") + "_"
    settings["Settings"] = {'SavedPath': settings.get("Settings", "SavedPath"), 'Language': language_code[:-1]}
    with open(interfaceText["data_path"], 'w') as configfile:
        settings.write(configfile)

    blockSwitch.configure(text=interfaceText[f"{language_code}switch_text"])
    pathEntry.configure(placeholder_text=interfaceText[f"{language_code}pathEntryText"])
    pathButton.configure(text=interfaceText[f"{language_code}pathButtonText"])
    languageButton.configure(text=language_code[:-1])


# Создание графического интерфейса

# базовая настройка (создание окна и т.д.)
app = CTk()
app.geometry("500x500")
app.resizable(False, False)
set_appearance_mode("dark")

app.title("Steam Connect Blocker")
app.iconbitmap('_internal\steamconnblocker.ico')

# создание сохранений если их нет
if not os.path.isdir(interfaceText["folder_path"]):
    os.makedirs(interfaceText["folder_path"])
settings = configparser.ConfigParser()
if not os.path.isfile(interfaceText["data_path"]):
    settings["Settings"] = {'SavedPath': interfaceText["default_steam_path"], 'Language': "ENG"}
    with open(interfaceText["data_path"], 'w') as configfile:
        settings.write(configfile)

settings.read(interfaceText["data_path"])
language_code = settings.get("Settings", "Language") + "_"

# проверяем состояние блокировки, в зависимости от него настраиваем UI
check_command = f"netsh advfirewall firewall show rule name='{commandName}'"
result = subprocess.run(['powershell', '-Command', check_command], capture_output=True, text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW)

# делаем переключатель блокировки
switch_var = StringVar(value="off" if result.returncode == 1 else "on")
blockSwitch = CTkSwitch(master=app, text=interfaceText[f"{language_code}switch_text"], command=change_internet_access,
                        variable=switch_var, onvalue="on", offvalue="off")
blockSwitch.place(relx=0.5, rely=0.5, anchor="center")

# добавляем лого с отображением состояния блокировки
blockLogoImage = CTkImage(dark_image=Image.open("_internal\steamconnblocker_block.png"), size=(170, 170))
logoImage = CTkImage(dark_image=Image.open("_internal\steamconnblocker.png"), size=(170, 170))

image_label = CTkLabel(app, image=logoImage if result.returncode == 1 else blockLogoImage, text="")
image_label.place(relx=0.5, rely=0.25, anchor="center")

# окно выбора пути
pathEntry = CTkEntry(master=app, placeholder_text=interfaceText[f"{language_code}pathEntryText"], width=300)
pathEntry.place(relx=0.35, rely=0.7, anchor="center")
pathEntry.insert(0, settings.get("Settings", "SavedPath").replace('/', '\\'))
pathButton = CTkButton(master=app, text=interfaceText[f"{language_code}pathButtonText"], command=browse_file,
                       corner_radius=6)
pathButton.place(relx=0.8, rely=0.7, anchor="center")

if blockSwitch.get() == "on":  # здесь блокируем панель смены пути если блокировка работает
    pathEntry.configure(state="disabled")
    pathButton.configure(state="disabled")
else:
    pathEntry.configure(state="normal")
    pathButton.configure(state="normal")


# добавляем прочие кнопки (нижние)
infoButton = CTkButton(master=app, image=CTkImage(dark_image=Image.open("_internal\infoLogo.png"), size=(44, 44)), command=open_info, text="",
                      width=50, height=50)
infoButton.place(relx=0.5, rely=0.9, anchor="center")

gitButton = CTkButton(master=app, image=CTkImage(dark_image=Image.open("_internal\gitLogo.png"), size=(40, 40)), command=open_git, text="",
                      width=50, height=50)
gitButton.place(relx=0.35, rely=0.9, anchor="center")


languageButton = CTkButton(master=app, command=change_language, text=language_code[:-1], font=CTkFont("Arial", weight="bold"),
                      width=55, height=52)
languageButton.place(relx=0.65, rely=0.9, anchor="center")

app.mainloop()