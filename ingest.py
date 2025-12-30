#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'ingestion des données pour le chatbot RAG
Charge les documents, les nettoie et les indexe dans ChromaDB
"""

import os
import sys
from pathlib import Path

# Ajouter le chemin src
sys.path.append(str(Path(__file__).parent.parent))

from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
import chromadb
from chromadb.config import Settings

def load_documents(data_dir="data/raw"):
    """Charge tous les documents depuis le dossier raw"""
    documents = []
    
    # Liste des fichiers
    files = [
        "carthage.txt",
        "dougga.txt", 
        "el_jem.txt",
        "kerkouane.txt",
        "sbeitla.txt"
    ]
    
    for file in files:
        filepath = os.path.join(data_dir, file)
        if os.path.exists(filepath):
            try:
                loader = TextLoader(filepath, encoding="utf-8")
                docs = loader.load()
                
                # Ajouter des métadonnées
                for doc in docs:
                    site_name = file.replace(".txt", "").capitalize()
                    doc.metadata.update({
                        "source": file,
                        "site": site_name,
                        "type": "guide_officiel",
                        "date": "2024"
                    })
                
                documents.extend(docs)
                print(f"✅ {file}: {len(docs)} document(s) chargé(s)")
                
            except Exception as e:
                print(f"❌ Erreur avec {file}: {e}")
    
    return documents

def create_chunks(documents, chunk_size=500, chunk_overlap=50):
    """Découpe les documents en chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"📊 {len(chunks)} chunks créés")
    return chunks

def create_vector_store(chunks, persist_directory="data/chroma_db"):
    """Crée et sauvegarde la base vectorielle ChromaDB"""
    
    # Créer le dossier si nécessaire
    os.makedirs(persist_directory, exist_ok=True)
    
    # Initialiser les embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Créer la base vectorielle
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name="sites_archeologiques_tunisie",
        collection_metadata={
            "description": "Base de connaissances des sites archéologiques de Tunisie",
            "hnsw:space": "cosine"
        }
    )
    
    # Sauvegarder
    vectorstore.persist()
    
    # Vérification
    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_collection("sites_archeologiques_tunisie")
    print(f"🎉 Base ChromaDB créée avec succès!")
    print(f"📍 Emplacement: {persist_directory}")
    print(f"📈 Documents indexés: {collection.count()}")
    
    return vectorstore

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🏛️ INGESTION DES DONNÉES - SITES ARCHÉOLOGIQUES TUNISIE")
    print("=" * 60)
    
    # 1. Charger les documents
    print("\n📥 Chargement des documents...")
    documents = load_documents()
    
    if not documents:
        print("❌ Aucun document trouvé. Vérifiez le dossier data/raw/")
        return
    
    # 2. Créer les chunks
    print("\n✂️ Découpage en chunks...")
    chunks = create_chunks(documents)
    
    # 3. Créer la base vectorielle
    print("\n🔧 Création de la base ChromaDB...")
    vectorstore = create_vector_store(chunks)
    
    # 4. Test de vérification
    print("\n🧪 Test de recherche...")
    test_query = "Carthage"
    results = vectorstore.similarity_search(test_query, k=2)
    
    print(f"\nTest '{test_query}':")
    for i, doc in enumerate(results):
        print(f"  {i+1}. {doc.page_content[:80]}...")
    
    print("\n" + "=" * 60)
    print("✅ INGESTION TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)

if __name__ == "__main__":
    main()