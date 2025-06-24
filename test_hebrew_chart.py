#!/usr/bin/env python3
"""
Script de test spécifique pour la génération de graphiques en hébreu
"""

import sys
import os
from datetime import datetime, timedelta
from io import BytesIO

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_hebrew_chart_generation():
    """Teste spécifiquement la génération de graphiques en hébreu"""
    print("🇮🇱 Test de génération de graphiques en hébreu")
    print("=" * 50)
    
    try:
        from handlers.pdf import create_daily_consumption_chart
        
        # Créer des données de test
        test_entries = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            for j in range(2):
                amount = 100 + (i * 10) + (j * 20)
                entry_time = date.replace(hour=8 + j * 6, minute=30, second=0, microsecond=0)
                test_entries.append({
                    'time': entry_time,
                    'amount': amount
                })
        
        test_data = {'entries': test_entries}
        print(f"✅ Données de test créées: {len(test_entries)} biberons")
        
        # Vérifier la présence de la police Noto Sans Hebrew
        font_path = os.path.join("assets", "fonts", "NotoSansHebrew-Regular.ttf")
        if os.path.exists(font_path):
            print(f"✅ Police Noto Sans Hebrew trouvée: {font_path}")
        else:
            print(f"⚠️ Police Noto Sans Hebrew non trouvée, utilisation des polices système")
        
        # Tester la génération en hébreu
        print("\n📊 Génération du graphique en hébreu...")
        try:
            chart_buffer = create_daily_consumption_chart(test_data, 7, 'he')
            
            if chart_buffer.getvalue():
                print(f"✅ Graphique généré avec succès")
                print(f"📊 Taille: {len(chart_buffer.getvalue())} bytes")
                
                # Sauvegarder pour inspection
                filename = "test_hebrew_chart.png"
                with open(filename, 'wb') as f:
                    f.write(chart_buffer.getvalue())
                print(f"💾 Sauvegardé: {filename}")
                
                return True
            else:
                print(f"❌ Échec de génération du graphique")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def check_font_availability():
    """Vérifie la disponibilité des polices pour l'hébreu"""
    print("\n🔤 Vérification des polices pour l'hébreu")
    print("=" * 40)
    
    try:
        import matplotlib.font_manager as fm
        
        # Polices importantes pour l'hébreu
        hebrew_fonts = [
            'Noto Sans Hebrew',
            'Arial Unicode MS',
            'Arial',
            'DejaVu Sans',
            'Liberation Sans'
        ]
        
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        
        print("📋 Polices disponibles pour l'hébreu:")
        for font in hebrew_fonts:
            if font in available_fonts:
                print(f"✅ {font}")
            else:
                print(f"❌ {font}")
        
        # Vérifier la police locale
        font_path = os.path.join("assets", "fonts", "NotoSansHebrew-Regular.ttf")
        if os.path.exists(font_path):
            print(f"✅ Police locale: {font_path}")
        else:
            print(f"❌ Police locale non trouvée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧪 Test spécifique des graphiques en hébreu")
    print("=" * 60)
    
    # Vérifier les polices
    fonts_ok = check_font_availability()
    
    # Tester la génération
    chart_ok = test_hebrew_chart_generation()
    
    print("\n" + "=" * 60)
    if fonts_ok and chart_ok:
        print("🎉 Test réussi! Les graphiques en hébreu fonctionnent correctement.")
    else:
        print("⚠️ Certains tests ont échoué.")
    
    print("\n💡 Si vous voyez encore des erreurs 'findfont', c'est normal -")
    print("   matplotlib essaie différentes polices jusqu'à en trouver une qui fonctionne.")

if __name__ == "__main__":
    main() 