from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any


class VFSException(Exception):
    pass


class InvalidVFSPath(VFSException):
    pass


class VirtualFileSystem:
    """
    VFS logique de Nexus.

    Il expose des chemins virtuels de type:
        `/system/config.json`
        `/user/shinji/files/note.txt`

    ...et les mappe vers un dossier réel sur l'hôte.
    """

    def __init__(self, root: str | Path = "nexusFS"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Normalisation / résolution
    # -------------------------
    def normalize(self, virtualPath: str) -> str:
        if not virtualPath:
            raise InvalidVFSPath("Chemin vide...")

        path = virtualPath.replace("\\", "/").strip()

        if not path.startswith("/"):
            path = "/" + path

        # Nettoyage simple
        parts: list[str] = []
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                raise InvalidVFSPath("Les chemins parent '..' sont interdits dans le VFS.")
            parts.append(part)

        return "/" + "/".join(parts)

    def resolve(self, virtualPath: str) -> Path:
        normalized = self.normalize(virtualPath)
        relative = normalized.lstrip("/")
        return self.root / relative

    # -------------------------
    # Initialisation
    # -------------------------
    def ensureBaseTree(self) -> None:
        baseDirs = [
            "/system",
            "/apps",
            "/plugins",
            "/users",
            "/tmp",
        ]
        for vpath in baseDirs:
            self.makeDirs(vpath)

        systemConfig = "/system/system.json"
        if not self.exists(systemConfig):
            self.writeJSON(systemConfig, {
                "installed": False,
                "oobeCompleted": False,
                "version": "0.1.0"
            })

    def ensureUserTree(self, username: str) -> None:
        base = f"/users/{username}"
        dirs = [
            f"{base}",
            f"{base}/.trash",
            f"{base}/files",
            f"{base}/files/Desktop",
            f"{base}/files/Documents",
            f"{base}/files/Downloads",
            f"{base}/files/Images",
            f"{base}/files/Music",
            f"{base}/files/Videos",
            f"{base}/config",
            f"{base}/plugins",
            f"{base}/themes",
        ]
        for vpath in dirs:
            self.makeDirs(vpath)

        userConfig = f"{base}/config/user.json"
        if not self.exists(userConfig):
            self.writeJSON(userConfig, {
                "username": username,
                "theme": "dark",
                "accent": "auto",
                "wallpaper": "",
                "autoLogin": False,
                "passwordHash": ""
            })

    # -------------------------
    # Inspection
    # -------------------------
    def exists(self, virtualPath: str) -> bool:
        return self.resolve(virtualPath).exists()

    def isFile(self, virtualPath: str) -> bool:
        return self.resolve(virtualPath).is_file()

    def isDir(self, virtualPath: str) -> bool:
        return self.resolve(virtualPath).is_dir()

    def listDir(self, virtualPath: str) -> list[str]:
        real = self.resolve(virtualPath)
        if not real.exists():
            raise FileNotFoundError(f"Dossier introuvable: {virtualPath}")
        if not real.is_dir():
            raise NotADirectoryError(f"Ce n'est pas un dossier: {virtualPath}")

        return sorted(item.name for item in real.iterdir())

    # -------------------------
    # Création / écriture
    # -------------------------
    def makeDirs(self, virtualPath: str) -> None:
        self.resolve(virtualPath).mkdir(parents=True, exist_ok=True)

    def writeText(self, virtualPath: str, content: str, encoding: str = "utf-8") -> None:
        real = self.resolve(virtualPath)
        real.parent.mkdir(parents=True, exist_ok=True)
        real.write_text(content, encoding=encoding)

    def readText(self, virtualPath: str, encoding: str = "utf-8") -> str:
        real = self.resolve(virtualPath)
        if not real.exists():
            raise FileNotFoundError(f"Fichier introuvable: {virtualPath}")
        return real.read_text(encoding=encoding)

    def writeJSON(self, virtualPath: str, data: Any) -> None:
        real = self.resolve(virtualPath)
        real.parent.mkdir(parents=True, exist_ok=True)
        with real.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def readJSON(self, virtualPath: str) -> Any:
        real = self.resolve(virtualPath)
        if not real.exists():
            raise FileNotFoundError(f"Fichier JSON introuvable: {virtualPath}")
        with real.open("r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------
    # Modification / suppression
    # -------------------------
    def remove(self, virtualPath: str) -> None:
        real = self.resolve(virtualPath)
        if not real.exists():
            return

        if real.is_dir():
            shutil.rmtree(real)
        else:
            real.unlink()

    def rename(self, srcVirtualPath: str, dstVirtualPath: str) -> None:
        src = self.resolve(srcVirtualPath)
        dst = self.resolve(dstVirtualPath)

        if not src.exists():
            raise FileNotFoundError(f"Source introuvable: {srcVirtualPath}")

        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
    
    def copy(self, srcVirtualPath: str, dstVirtualPath: str) -> None:
        src = self.resolve(srcVirtualPath)
        dst = self.resolve(dstVirtualPath)

        if not src.exists():
            raise FileNotFoundError(srcVirtualPath)

        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    def touch(self, virtualPath: str) -> None:
        real = self.resolve(virtualPath)
        real.parent.mkdir(parents=True, exist_ok=True)
        real.touch(exist_ok=True)
