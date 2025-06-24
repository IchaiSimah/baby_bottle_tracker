#!/usr/bin/env python3
"""
Script de test pour la génération de graphiques de consommation quotidienne
"""

import sys
import os
from datetime import datetime, timedelta
from io import BytesIO

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.pdf import create_daily_consumption_chart

def create_test_data():
    """Crée des données de test pour le graphique"""
    test_entries = []
    
    # Créer des données pour les 7 derniers jours
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        
        # Ajouter 2-4 biberons par jour avec des quantités variables
        num_bottles = 2 + (i % 3)  # 2, 3, ou 4 biberons
        
        for j in range(num_bottles):
            # Quantités variables entre 80 et 150ml
            amount = 80 + (i * 10) + (j * 15)
            if amount > 150:
                amount = 150
            
            # Heures variables dans la journée
            hour = 6 + (j * 4)  # 6h, 10h, 14h, 18h
            if hour > 22:
                hour = 22
            
            entry_time = date.replace(hour=hour, minute=30, second=0, microsecond=0)
            
            test_entries.append({
                'time': entry_time,
                'amount': amount
            })
    
    return {'entries': test_entries}

def test_chart_generation():
    """Teste la génération de graphiques dans différentes langues"""
    print("🧪 Test de génération de graphiques de consommation quotidienne")
    print("=" * 60)
    
    # Créer des données de test
    test_data = create_test_data()
    print(f"✅ Données de test créées: {len(test_data['entries'])} biberons")
    
    # Tester dans différentes langues
    languages = ['fr', 'en', 'he']
    
    for lang in languages:
        print(f"\n🌍 Test en {lang.upper()}:")
        try:
            # Générer le graphique
            chart_buffer = create_daily_consumption_chart(test_data, 7, lang)
            
            if chart_buffer.getvalue():
                print(f"✅ Graphique généré avec succès en {lang}")
                print(f"📊 Taille du buffer: {len(chart_buffer.getvalue())} bytes")
                
                # Sauvegarder le graphique pour inspection
                filename = f"test_chart_{lang}.png"
                with open(filename, 'wb') as f:
                    f.write(chart_buffer.getvalue())
                print(f"💾 Graphique sauvegardé: {filename}")
            else:
                print(f"❌ Échec de génération du graphique en {lang}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération en {lang}: {e}")
    
    print("\n🔗 Test du lien d'information:")
    try:
        from handlers.pdf import LINK_TO_OFFICIAL_INFORMATIONS
        print(f"✅ Lien global configuré: {LINK_TO_OFFICIAL_INFORMATIONS}")
    except Exception as e:
        print(f"❌ Erreur avec le lien global: {e}")
    
    print("\n🎉 Tests terminés!")

if __name__ == "__main__":
    test_chart_generation() 