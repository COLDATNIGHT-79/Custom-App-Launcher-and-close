import tkinter as tk
from subprocess import Popen, CREATE_NEW_CONSOLE
from tkinter import PhotoImage

opened_processes = []

def open_exe(exe_path):
    try:
        process = Popen(exe_path, creationflags=CREATE_NEW_CONSOLE)
        opened_processes.append(process)
        print(f"Opened {exe_path}")
    except FileNotFoundError:
        print(f"Error: The specified executable file ({exe_path}) was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
def close_all_apps():
    for process in opened_processes:
        try:
            process.terminate()
            print(f"Closed process: {process.pid}")
        except Exception as e:
            print(f"An error occurred while closing the process: {e}")


def create_button(root, exe_path, app_name, row, column):
    button_font = ('Bookman', 14, 'bold')  
    button = tk.Button(root, text=app_name, command=lambda: open_exe(exe_path), font=button_font, bg='#000000', fg='white', padx=10, pady=5)
    button.grid(row=row, column=column, padx=5, pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Colds Consequences")
    root.geometry("987x372")

   #IMAGE WILL NOT WORK SINCE YOUR PC MAY NOT HAVE THE IMAGE I HAVE. DOWNLOAD A "PNG" FILE AND FEED ITS LOCATION HERE
    bg_image = PhotoImage(file=r'C:\icons\sf.png') 

  
    bg_label = tk.Label(root, image=bg_image)
    bg_label.place(relwidth=1, relheight=1)
#modify the location of apps as per YOUR PC if you plan to use my code. :)
    exe_info = [
       
        (r'C:\Program Files\Unity Hub\UNITY.exe', 'UNITY'),
        (r'C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe', 'DaVinci Resolve'),
        (r'C:\Program Files\obs-studio\bin\64bit\obs.exe','OBS'),
        (r'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe', 'Blender'),
        (r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe', 'Aseprite'),
        (r'C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe', 'Visual Studio'),
        (r'C:\Users\ajnim\AppData\Local\Programs\codetantra-sea\CTS.exe', 'CodeTantra'),
        (r'C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EGS.exe','Epic Games Launcher'),
        (r'C:\Program Files (x86)\Steam\steamapps\common\Hunt Showdown\bin\win_x64\HuntGame.exe', 'Hunt Showdown'),
        (r'C:\Program Files (x86)\Steam\steamapps\common\Tom Clancys Rainbow Six Siege\r6.exe', 'Rainbow Six Siege'),
        (r'D:\SteamLibrary\steamapps\common\Dead Cells\deadcells.exe', 'Dead Cells'),
        (r'D:\SteamLibrary\steamapps\common\ForzaHorizon5\ForzaHo\ForzaHorizon5.exe', 'Forza Horizon 5'),
        
        (r'D:\SteamLibrary\steamapps\common\Red Dead Redemption 2\RDR2.exe', 'Red Dead Redemption 2'),
        (r'C:\Riot Games\Riot Client\RCS.exe', 'League of Legends'),
        
        (r'D:\SteamLibrary\steamapps\common\Satisfactory\FactoryGame.exe', 'Satisfactory')
        
    ]

    for i, (exe_path, app_name) in enumerate(exe_info):
        row = i // 3  # 3 buttons per row
        column = i % 3
        create_button(root, exe_path, app_name, row, column)
        
    close_all_button = tk.Button(root, text="Close All", command=close_all_apps, font=('Arial', 12), bg='red', fg='white', padx=10, pady=5)
    close_all_button.grid(row=(i + 1) // 3, column=0, columnspan=3, pady=10)

    root.mainloop()
