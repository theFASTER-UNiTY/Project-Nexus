import hashlib

from core.Service import Service


class PasswordService(Service):
    name = "passwords"

    def hashPassword(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def verifyPassword(self, password: str, storedHash: str) -> bool:
        if not storedHash:
            return password == ""

        return self.hashPassword(password) == storedHash

    def isPasswordSet(self, storedHash: str) -> bool:
        return bool(storedHash)
