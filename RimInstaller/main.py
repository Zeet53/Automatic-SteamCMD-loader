import subprocess
import pyperclip
import threading
import time
import os

def run_steamcmd_commands(steamcmd_path, commands, timeout_seconds=None):
    full_command = [steamcmd_path] + commands
    list_commands = parse_steamcmd_commands(commands)
    logs_list = {}

    result = subprocess.run(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout_seconds
    )

    if result.stdout:
        lines = result.stdout.splitlines()
        for i, command in enumerate(list_commands):
            command_key = " ".join(command)
            if "success" in lines[8 + i].lower():
                logs_list[command_key] = "success"
            elif "error" in lines[8 + i].lower() or "fail" in lines[8 + i].lower():
                logs_list[command_key] = lines[8 + i]
        
        if len(list_commands) != len(list(logs_list.keys())):
            print('Неизвестная ошибка логи:\n')
            for i, line in enumerate(lines, 1):
                print(f'{i}. {line}')
            print('=' * 100 + '\n')
    
    if result.returncode == 0:
        print(f"УСПЕХ. Код: {result.returncode}")
    else:
        print(f"ОШИБКА. Код: {result.returncode}")
    
    return logs_list

def parse_steamcmd_commands(commands_list):
    result = []
    current_cmd = []
    
    for item in commands_list:
        if item.startswith('+'):
            if current_cmd:
                result.append(current_cmd)
            current_cmd = [item]
        else:
            current_cmd.append(item)
    
    if current_cmd:
        result.append(current_cmd)
    
    if len(result) > 3:
        result = result[2:-1]
    else:
        result = []
    
    return result

def load_or_create_config():
    default_config = """ЧАСТОТА ОБНОВЛЕНИЙ В МИЛИСЕКУНДАХ = 7000
ПУТЬ К STEAMCMD = D:/steamCMD/steamcmd.exe
КОД ИГРЫ В СТИМ = 294100
ПУТЬ К ПАПКЕ УСТАНОВКИ = C:/Users/No_Name/Desktop/test
"""

    if not os.path.exists('config.txt'):
        print("Файл config.txt не найден, создаю новый...")
        with open('config.txt', 'w', encoding='utf-8') as f:
            f.write(default_config)
        print("Файл config.txt создан. Отредактируйте его и перезапустите программу.")
        input("Нажмите Enter чтобы выйти")
        exit(0)
    
    config = {}
    try:
        with open('config.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        required_fields = [
            'ЧАСТОТА ОБНОВЛЕНИЙ В МИЛИСЕКУНДАХ',
            'ПУТЬ К STEAMCMD', 
            'КОД ИГРЫ В СТИМ',
            'ПУТЬ К ПАПКЕ УСТАНОВКИ'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"Отсутствуют обязательные поля: {', '.join(missing_fields)}")
            input("Нажмите Enter чтобы выйти")
            exit(0)
        
        try:
            INSTALLING_TIME = int(config['ЧАСТОТА ОБНОВЛЕНИЙ В МИЛИСЕКУНДАХ'])
            if INSTALLING_TIME <= 0:
                print("Ошибка: частота должна быть положительным числом")
                input("Нажмите Enter чтобы выйти")
                exit(0)
        except ValueError:
            print("Ошибка: значение 'ЧАСТОТА ОБНОВЛЕНИЙ В МИЛИСЕКУНДАХ' должно быть числом")
            input("Нажмите Enter чтобы выйти")
            exit(0)
        
        STEAMCMD_PATH = config['ПУТЬ К STEAMCMD']
        GAME_CODE = config['КОД ИГРЫ В СТИМ']
        TARGET_DIR = config['ПУТЬ К ПАПКЕ УСТАНОВКИ']
        
        if not os.path.exists(STEAMCMD_PATH):
            print(f"Внимание: SteamCMD не найден по пути: {STEAMCMD_PATH}")
            input("Нажмите Enter чтобы выйти")
            exit(0)
        
        return INSTALLING_TIME, STEAMCMD_PATH, GAME_CODE, TARGET_DIR
        
    except Exception as e:
        print(f"Ошибка в config.txt: {e}")
        print("\nИсправьте файл config.txt или удалите его для создания нового.")
        input("Нажмите Enter чтобы выйти")
        exit(1)

def run_steamcmd_in_thread(steamcmd_path, command_list):
    def thread_func():
        try:
            run_steamcmd_commands(steamcmd_path, command_list)
        except Exception as e:
            print(f"Ошибка в потоке SteamCMD: {e}")
    
    thread = threading.Thread(target=thread_func, daemon=True)
    thread.start()
    return thread

def main():
    INSTALLING_TIME, STEAMCMD_PATH, GAME_CODE, TARGET_DIR = load_or_create_config()
    
    prev = pyperclip.paste()
    commandsList = []
    last_install_time = time.time()
    
    print("Программа запущена. Копируйте ссылки на модификации в буфер обмена.")
    print("Для выхода нажмите Ctrl+C")
    
    while True:
        try:
            curr = pyperclip.paste()
            if curr != prev and curr.strip():
                prev = curr
                if '=' in curr:
                    command = ['+workshop_download_item', GAME_CODE, curr.split('=')[1]]
                    commandsList.append(command)
                    print(f"Добавлена команда: {command}")
            
            current_time_ms = time.time() * 1000
            
            if current_time_ms - last_install_time >= INSTALLING_TIME and len(commandsList) > 0:
                print('\nНачинаю скачивание...')
                cl = ["+force_install_dir", TARGET_DIR, "+login", "anonymous"]
                
                for newCommand in commandsList:
                    cl.extend(newCommand)
                cl.append('+quit')
                
                run_steamcmd_in_thread(STEAMCMD_PATH, cl)
                commandsList.clear()
                last_install_time = current_time_ms
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\nПрограмма остановлена пользователем.")
            break
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
