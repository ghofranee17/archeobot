#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moteur RAG (Retrieval-Augmented Generation)
Gère la recherche et la génération de réponses
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import json

class RAGEngine:
    """Moteur RAG pour la recherche et génération de réponses"""
    
    def __init__(self, chroma_path="data/chroma_db"):
        """Initialise le moteur RAG avec ChromaDB"""
        self.chroma_path = chroma_path
        
        # Initialiser ChromaDB
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Fonction d'embedding
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Charger la collection
        self.collection = self.client.get_collection(
            name="sites_archeologiques_tunisie",
            embedding_function=self.embedding_func
        )
        
        print(f"✅ Moteur RAG initialisé - {self.collection.count()} documents")
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Recherche les documents les plus pertinents"""
        
        # Recherche dans ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Formater les résultats
        formatted_results = []
        if results['documents']:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convertir distance en score de similarité
                similarity_score = 1 - distance
                
                formatted_results.append({
                    'id': i,
                    'content': doc,
                    'metadata': metadata,
                    'similarity_score': round(similarity_score, 3),
                    'distance': round(distance, 3)
                })
        
        return formatted_results
    
    def generate_response(self, query: str, context_results: List[Dict]) -> Dict[str, Any]:
        """Génère une réponse basée sur le contexte"""
        
        if not context_results:
            return {
                "answer": "Je ne dispose pas d'informations fiables sur ce sujet dans ma base de connaissances.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Construire le contexte
        context_parts = []
        sources = []
        
        for result in context_results:
            context_parts.append(result['content'])
            
            # Extraire les sources
            meta = result['metadata']
            source_info = {
                'site': meta.get('site', 'Inconnu'),
                'source': meta.get('source', 'Document'),
                'score': result['similarity_score']
            }
            if source_info not in sources:
                sources.append(source_info)
        
        # Construire la réponse (version simplifiée)
        context = "\n\n".join(context_parts)
        
        # Pour un vrai projet, on utiliserait un LLM ici
        # Pour cette version, on retourne le contexte formaté
        answer = f"D'après les informations disponibles :\n\n{context}"
        
        # Score de confiance (moyenne des similarités)
        confidence = sum(r['similarity_score'] for r in context_results) / len(context_results)
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 3),
            "context_results": len(context_results)
        }
    
    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """Traite une requête complète"""
        print(f"🔍 Recherche: {question}")
        
        # 1. Recherche
        results = self.search(question, k=k)
        
        # 2. Génération de réponse
        if results:
            response = self.generate_response(question, results)
        else:
            response = {
                "answer": "Aucune information pertinente trouvée.",
                "sources": [],
                "confidence": 0.0,
                "context_results": 0
            }
        
        return response
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Retourne des informations sur la collection"""
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata
        }


# Interface en ligne de commande
def main():
    """Interface CLI pour tester le RAG"""
    print("🤖 MOTEUR RAG - TEST EN LIGNE DE COMMANDE")
    print("=" * 50)
    
    # Initialiser le moteur
    try:
        rag = RAGEngine()
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        print("Assurez-vous d'avoir exécuté ingest.py d'abord.")
        return
    
    # Afficher les infos
    info = rag.get_collection_info()
    print(f"📊 Collection: {info['name']}")
    print(f"📈 Documents: {info['count']}")
    print(f"📝 Description: {info['metadata'].get('description', 'N/A')}")
    
    print("\n💡 Exemples de questions:")
    print("- Carthage")
    print("- théâtre de Dougga")
    print("- sites UNESCO")
    print("- quit pour quitter")
    print("=" * 50)
    
    # Boucle interactive
    while True:
        try:
            question = input("\n❓ Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Au revoir!")
                break
            
            if not question:
                continue
            
            # Traiter la question
            result = rag.query(question, k=2)
            
            # Afficher les résultats
            print(f"\n✅ Réponse (confiance: {result['confidence']}):")
            print("-" * 40)
            print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
            
            if result['sources']:
                print(f"\n📚 Sources ({len(result['sources'])}):")
                for i, source in enumerate(result['sources']):
                    print(f"  {i+1}. {source['site']} - {source['source']} (score: {source['score']})")
            
        except KeyboardInterrupt:
            print("\n👋 Interruption - Au revoir!")
            break
        except Exception as e:
            print(f"⚠️ Erreur: {e}")

if __name__ == "__main__":
    main()