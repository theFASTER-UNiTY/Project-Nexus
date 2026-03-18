import hashlib


class SessionManager:
    def __init__(self, kernel):
        self.kernel = kernel

        self.currentUser = None
        self.currentProfile = None
        self.sessionActive = False

    # -------------------------------------------------
    # État session
    # -------------------------------------------------
    def hasActiveSession(self) -> bool:
        return self.sessionActive

    def getCurrentUser(self):
        return self.currentUser

    # -------------------------------------------------
    # Login / Logout
    # -------------------------------------------------
    def login(self, username: str) -> dict:
        if not username or not username.strip():
            raise ValueError("Nom d'utilisateur invalide.")

        username = username.strip()

        if self.sessionActive:
            raise RuntimeError("Une session est déjà active.")

        self.kernel.bus.emit("session.starting", username=username)

        self.kernel.filesystem.ensureUserTree(username)
        profile = self.loadUserProfile(username)

        self.currentUser = username
        self.currentProfile = profile
        self.sessionActive = True

        self.kernel.state["user"] = username
        self.kernel.state["theme"]["scheme"] = profile.get("theme", "dark")

        self.kernel.bus.emit(
            "session.started",
            username=username,
            profile=profile
        )

        return profile

    def logout(self) -> None:
        print("Logging out...")
        if not self.sessionActive:
            return

        username = self.currentUser

        self.kernel.bus.emit("session.ending", username=username)

        self.saveUserProfile()

        self.currentUser = None
        self.currentProfile = None
        self.sessionActive = False

        self.kernel.state["user"] = None

        self.kernel.bus.emit("session.ended", username=username)

    # -------------------------------------------------
    # Profil utilisateur
    # -------------------------------------------------
    def loadUserProfile(self, username: str) -> dict:
        profilePath = f"/users/{username}/config/user.json"

        if not self.kernel.filesystem.exists(profilePath):
            self.kernel.filesystem.ensureUserTree(username)

        profile = self.kernel.filesystem.readJSON(profilePath)

        if not isinstance(profile, dict):
            raise TypeError("Le profil utilisateur doit être un objet JSON.")

        return profile

    def saveUserProfile(self) -> None:
        if not self.sessionActive:
            return

        if not self.currentUser or self.currentProfile is None:
            return

        profilePath = self.getCurrentUserProfilePath()
        self.kernel.filesystem.writeJSON(profilePath, self.currentProfile)

    def updateCurrentProfile(self, **changes) -> dict:
        if not self.sessionActive or self.currentProfile is None:
            raise RuntimeError("Aucune session active.")

        self.currentProfile.update(changes)
        self.kernel.state["theme"]["scheme"] = self.currentProfile.get("theme", "dark")

        self.kernel.bus.emit(
            "session.profile.updated",
            username=self.currentUser,
            profile=self.currentProfile,
            changes=changes
        )

        return self.currentProfile
    
    def hashPassword(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def verifyPassword(self, username: str, password: str) -> bool:
        profile = self.loadUserProfile(username)
        storedHash = profile.get("passwordHash", "")

        passwordService = self.kernel.services.get("passwords")
        if passwordService is None:
            raise RuntimeError("PasswordService indisponible.")

        return passwordService.verifyPassword(password, storedHash)

    def currentUserHasPassword(self) -> bool:
        if not self.sessionActive or not self.currentUser:
            return False

        profile = self.loadUserProfile(self.currentUser)
        return bool(profile.get("passwordHash", ""))

    def setCurrentUserPassword(self, password: str) -> None:
        if not self.sessionActive or self.currentProfile is None:
            raise RuntimeError("Aucune session active.")

        passwordService = self.kernel.services.get("passwords")
        if passwordService is None:
            raise RuntimeError("PasswordService indisponible.")

        self.currentProfile["passwordHash"] = passwordService.hashPassword(password) if password else ""
        self.saveUserProfile()
    
    def setUserPassword(self, username: str, password: str):
        profile = self.loadUserProfile(username)

        passwordService = self.kernel.services.get("passwords")
        if passwordService is None:
            raise RuntimeError("PasswordService indisponible.")

        profile["passwordHash"] = passwordService.hashPassword(password) if password else ""

        path = f"/users/{username}/config/user.json"
        self.kernel.filesystem.writeJSON(path, profile)

    # -------------------------------------------------
    # Chemins utiles
    # -------------------------------------------------
    def getCurrentUserHome(self) -> str:
        if not self.currentUser:
            raise RuntimeError("Aucune session active.")
        return f"/users/{self.currentUser}"

    def getCurrentUserProfilePath(self) -> str:
        if not self.currentUser:
            raise RuntimeError("Aucune session active.")
        return f"/users/{self.currentUser}/config/user.json"

    # -------------------------------------------------
    # Auto-login
    # -------------------------------------------------
    def isAutoLoginEnabled(self, username: str) -> bool:
        profile = self.loadUserProfile(username)
        return bool(profile.get("autoLogin", False))

    def getAutoLoginUser(self):
        usersRoot = "/users"

        if not self.kernel.filesystem.exists(usersRoot):
            return None

        if not self.kernel.filesystem.isDir(usersRoot):
            return None

        for username in self.kernel.filesystem.listDir(usersRoot):
            try:
                if self.isAutoLoginEnabled(username):
                    return username
            except Exception:
                continue

        return None

    def startDefaultSession(self):
        autoUser = self.getAutoLoginUser()

        if autoUser:
            return self.login(autoUser)

        return None
