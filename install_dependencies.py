#!/usr/bin/env python3
"""
Script d'installation des dépendances pour le Baby Bottle Tracker
"""

import subprocess
import sys
import os

def install_dependencies():
    """Installe les dépendances nécessaires"""
    print("🔧 Installation des dépendances pour Baby Bottle Tracker")
    print("=" * 50)
    
    # Liste des dépendances
    dependencies = [
        "matplotlib==3.7.2",
        "numpy",  # Dépendance de matplotlib
        "requests"  # Pour télécharger les polices
    ]
    
    for dep in dependencies:
        print(f"\n📦 Installation de {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} installé avec succès")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'installation de {dep}: {e}")
            return False
    
    print("\n🎉 Toutes les dépendances ont été installées avec succès!")
    print("\n📊 La fonctionnalité de graphiques de consommation quotidienne est maintenant disponible.")
    return True

def test_matplotlib():
    """Teste que matplotlib fonctionne correctement"""
    print("\n🧪 Test de matplotlib...")
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        import numpy as np
        print("✅ Matplotlib importé avec succès")
        
        # Test de création d'un graphique simple
        plt.switch_backend('Agg')
        fig, ax = plt.subplots()
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y)
        plt.close()
        print("✅ Test de création de graphique réussi")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test de matplotlib: {e}")
        return False

if __name__ == "__main__":
    if install_dependencies():
        test_matplotlib()
    else:
        print("\n❌ Installation échouée. Veuillez vérifier votre connexion internet et réessayer.")
        sys.exit(1) 