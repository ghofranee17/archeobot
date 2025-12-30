#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système d'authentification
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Tuple

class AuthSystem:
    """Gestion de l'authentification utilisateur"""
    
    def __init__(self, users_file="data/users.json"):
        self.users_file = users_file
        self._init_users_file()
    
    def _init_users_file(self):
        """Initialise le fichier utilisateurs s'il n'existe pas"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w") as f:
                json.dump({}, f)
    
    def _hash_password(self, password: str) -> str:
        """Hash un mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register(self, username: str, password: str) -> Tuple[bool, str]:
        """Enregistre un nouvel utilisateur"""
        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
            
            # Vérifier si l'utilisateur existe
            if username in users:
                return False, "Cet utilisateur existe déjà"
            
            # Créer le nouvel utilisateur
            users[username] = {
                "password": self._hash_password(password),
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
            
            # Sauvegarder
            with open(self.users_file, "w") as f:
                json.dump(users, f, indent=2)
            
            return True, "Inscription réussie !"
            
        except Exception as e:
            return False, f"Erreur lors de l'inscription: {e}"
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Authentifie un utilisateur"""
        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
            
            # Vérifier l'utilisateur
            if username not in users:
                return False, "Utilisateur non trouvé"
            
            # Vérifier le mot de passe
            if users[username]["password"] != self._hash_password(password):
                return False, "Mot de passe incorrect"
            
            # Mettre à jour la dernière connexion
            users[username]["last_login"] = datetime.now().isoformat()
            with open(self.users_file, "w") as f:
                json.dump(users, f, indent=2)
            
            return True, "Connexion réussie !"
            
        except Exception as e:
            return False, f"Erreur lors de la connexion: {e}"
    
    def user_exists(self, username: str) -> bool:
        """Vérifie si un utilisateur existe"""
        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
            return username in users
        except:
            return False