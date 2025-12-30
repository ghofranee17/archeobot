#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Streamlit principale
Interface utilisateur du chatbot RAG
"""

import streamlit as st
import sys
from pathlib import Path

# Ajouter le chemin src
sys.path.append(str(Path(__file__).parent.parent))

from src.rag import RAGEngine
from src.auth import AuthSystem

# Configuration de la page
st.set_page_config(
    page_title="Chatbot RAG - Sites Archéologiques Tunisie",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des systèmes
@st.cache_resource
def init_rag():
    """Initialise le moteur RAG"""
    try:
        return RAGEngine()
    except Exception as e:
        st.error(f"Erreur d'initialisation RAG: {e}")
        return None

@st.cache_resource
def init_auth():
    """Initialise le système d'authentification"""
    return AuthSystem()

# Variables de session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None

# Initialiser
rag_engine = init_rag()
auth_system = init_auth()

# ========== PAGES ==========

def login_page():
    """Page de connexion/inscription"""
    st.title("🔐 Chatbot RAG - Connexion")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        st.subheader("Connexion existante")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Nom d'utilisateur", key="login_user")
            password = st.text_input("Mot de passe", type="password", key="login_pwd")
            
            if st.button("Se connecter", type="primary", use_container_width=True):
                if username and password:
                    success, message = auth_system.login(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.rag_engine = rag_engine
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Veuillez remplir tous les champs")
    
    with tab2:
        st.subheader("Nouveau compte")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            new_user = st.text_input("Nouvel utilisateur", key="signup_user")
            new_pwd = st.text_input("Nouveau mot de passe", type="password", key="signup_pwd")
            confirm_pwd = st.text_input("Confirmer le mot de passe", type="password", key="signup_confirm")
            
            if st.button("S'inscrire", type="primary", use_container_width=True):
                if new_user and new_pwd and confirm_pwd:
                    if new_pwd != confirm_pwd:
                        st.error("Les mots de passe ne correspondent pas")
                    elif len(new_user) < 3:
                        st.error("Le nom d'utilisateur doit avoir au moins 3 caractères")
                    elif len(new_pwd) < 6:
                        st.error("Le mot de passe doit avoir au moins 6 caractères")
                    else:
                        success, message = auth_system.register(new_user, new_pwd)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.warning("Veuillez remplir tous les champs")
    
    # Information sur le projet
    st.markdown("---")
    with st.expander("ℹ️ À propos du projet"):
        st.write("""
        **Chatbot RAG sur les Sites Archéologiques de Tunisie**
        
        Ce projet utilise l'architecture RAG (Retrieval-Augmented Generation) pour fournir
        des informations précises et sourcées sur les sites archéologiques tunisiens.
        
        **Fonctionnalités :**
        - Recherche intelligente dans une base de connaissances
        - Réponses structurées avec sources
        - Interface moderne et intuitive
        - Authentification sécurisée
        
        **Technologies :** Python, Streamlit, ChromaDB, RAG
        """)

def chatbot_page():
    """Page principale du chatbot"""
    
    # Header
    col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
    with col_h1:
        st.title("🏛️ Chatbot RAG Archéologique")
        st.caption(f"Connecté en tant que : **{st.session_state.username}**")
    
    with col_h3:
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.rerun()
    
    st.markdown("---")
    
    # Layout principal
    col_main, col_side = st.columns([3, 1])
    
    with col_main:
        # Zone de recherche
        st.subheader("💬 Posez votre question")
        
        question = st.text_input(
            "Recherchez un site ou posez une question :",
            placeholder="Ex: Parle-moi de Carthage, Décris le théâtre de Dougga...",
            key="question_input"
        )
        
        # Boutons rapides
        st.write("**Questions rapides :**")
        col_btns = st.columns(5)
        quick_questions = ["Carthage", "Dougga", "El Jem", "Kerkouane", "Sbeitla"]
        
        for i, (col, q) in enumerate(zip(col_btns, quick_questions)):
            with col:
                if st.button(q, use_container_width=True):
                    question = q
        
        # Recherche
        if st.button("🔍 Rechercher avec RAG", type="primary", use_container_width=True) or question:
            if question:
                if not rag_engine:
                    st.error("Le moteur RAG n'est pas initialisé. Exécutez ingest.py d'abord.")
                else:
                    with st.spinner("🔍 Recherche en cours..."):
                        try:
                            result = rag_engine.query(question, k=3)
                            
                            # Afficher les résultats
                            if result['confidence'] > 0:
                                st.success(f"✅ {result['context_results']} résultat(s) trouvé(s)")
                                st.markdown("---")
                                
                                # Réponse
                                with st.expander("📝 Réponse complète", expanded=True):
                                    st.write(result['answer'])
                                
                                # Sources
                                if result['sources']:
                                    st.subheader("📚 Sources utilisées")
                                    for i, source in enumerate(result['sources']):
                                        st.write(f"**{i+1}. {source['site']}**")
                                        st.caption(f"Source: {source['source']} | Score: {source['score']}")
                                
                                # Métriques
                                col_met1, col_met2, col_met3 = st.columns(3)
                                with col_met1:
                                    st.metric("Confiance", f"{result['confidence']:.2%}")
                                with col_met2:
                                    st.metric("Sources", result['context_results'])
                                with col_met3:
                                    st.metric("Status", "✅ Réponse fiable")
                                
                            else:
                                st.warning("⚠️ Aucune information pertinente trouvée.")
                                st.info("💡 Essayez avec : Carthage, Dougga, El Jem, Kerkouane, Sbeitla")
                                
                        except Exception as e:
                            st.error(f"Erreur lors de la recherche : {e}")
    
    with col_side:
        # Sidebar
        st.subheader("📚 Informations")
        
        if rag_engine:
            info = rag_engine.get_collection_info()
            st.metric("Documents", info['count'])
            st.metric("Sites", "5")
        
        st.markdown("---")
        st.write("**🏛️ Sites disponibles :**")
        sites = ["Carthage", "Dougga", "El Jem", "Kerkouane", "Sbeitla"]
        for site in sites:
            st.write(f"• {site}")
        
        st.markdown("---")
        with st.expander("🤖 À propos du RAG"):
            st.write("""
            **R**etrieval : Récupération des informations pertinentes
            
            **A**ugmented : Contexte enrichi avec les sources
            
            **G**eneration : Génération de réponse structurée
            
            *Pas d'hallucinations, réponses sourcées*
            """)
    
    # Footer
    st.markdown("---")
    st.caption("""
    **Projet IA Générative** - Chatbot RAG sur les Sites Archéologiques de Tunisie  
    Architecture complète : Streamlit + ChromaDB + RAG
    """)

# ========== ROUTAGE ==========

def main():
    """Fonction principale de routage"""
    
    if not st.session_state.authenticated:
        login_page()
    else:
        chatbot_page()

if __name__ == "__main__":
    main()