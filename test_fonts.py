#!/usr/bin/env python3
"""
Script de test pour vérifier les polices disponibles et la génération de graphiques
"""

import sys
import os
from datetime import datetime, timedelta
from io import BytesIO

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_font_availability():
    """Teste la disponibilité des polices"""
    print("🔤 Test de disponibilité des polices")
    print("=" * 40)
    
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import rcParams
        import matplotlib.font_manager as fm
        
        print("✅ Matplotlib importé avec succès")
        
        # Lister les polices disponibles
        fonts = [f.name for f in fm.fontManager.ttflist]
        
        # Polices importantes à vérifier
        important_fonts = [
            'DejaVu Sans',
            'Arial',
            'Helvetica',
            'Liberation Sans',
            'Arial Unicode MS'
        ]
        
        print("\n📋 Polices importantes disponibles:")
        for font in important_fonts:
            if font in fonts:
                print(f"✅ {font}")
            else:
                print(f"❌ {font}")
        
        # Tester la configuration de police
        print("\n🔧 Test de configuration de police:")
        try:
            rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
            rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'Liberation Sans']
            rcParams['axes.unicode_minus'] = False
            print("✅ Configuration de police réussie")
        except Exception as e:
            print(f"❌ Erreur configuration police: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des polices: {e}")
        return False

def test_chart_generation_with_fonts():
    """Teste la génération de graphiques avec différentes polices"""
    print("\n📊 Test de génération de graphiques avec polices")
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
        
        # Tester dans différentes langues
        languages = ['fr', 'en', 'he']
        
        for lang in languages:
            print(f"\n🌍 Test en {lang.upper()}:")
            try:
                chart_buffer = create_daily_consumption_chart(test_data, 7, lang)
                
                if chart_buffer.getvalue():
                    print(f"✅ Graphique généré avec succès en {lang}")
                    print(f"📊 Taille: {len(chart_buffer.getvalue())} bytes")
                    
                    # Sauvegarder pour inspection
                    filename = f"test_fonts_{lang}.png"
                    with open(filename, 'wb') as f:
                        f.write(chart_buffer.getvalue())
                    print(f"💾 Sauvegardé: {filename}")
                else:
                    print(f"❌ Échec de génération en {lang}")
                    
            except Exception as e:
                print(f"❌ Erreur en {lang}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de génération: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Test complet des polices et graphiques")
    print("=" * 60)
    
    # Test des polices
    fonts_ok = test_font_availability()
    
    # Test de génération
    charts_ok = test_chart_generation_with_fonts()
    
    print("\n" + "=" * 60)
    if fonts_ok and charts_ok:
        print("🎉 Tous les tests sont passés avec succès!")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("\n💡 Conseils en cas de problème:")
    print("- Installez les polices système manquantes")
    print("- Vérifiez que matplotlib est correctement installé")
    print("- Sur Linux, installez: sudo apt-get install fonts-dejavu")
    print("- Sur Windows, les polices Arial sont généralement disponibles")

if __name__ == "__main__":
    main() 