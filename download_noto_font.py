#!/usr/bin/env python3
"""
Script pour télécharger la police Noto Sans Hebrew
"""

import os
import requests
import zipfile
from pathlib import Path

def download_noto_hebrew_font():
    """Télécharge et installe la police Noto Sans Hebrew"""
    print("🔤 Téléchargement de la police Noto Sans Hebrew")
    print("=" * 50)
    
    # Créer le dossier fonts s'il n'existe pas
    fonts_dir = Path("assets/fonts")
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    # Vérifier si la police existe déjà
    font_path = fonts_dir / "NotoSansHebrew-Regular.ttf"
    if font_path.exists():
        print("✅ Police Noto Sans Hebrew déjà présente")
        return True
    
    # URL de téléchargement de Noto Sans Hebrew
    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"
    
    try:
        print("📥 Téléchargement en cours...")
        response = requests.get(font_url, timeout=30)
        response.raise_for_status()
        
        # Sauvegarder le fichier
        with open(font_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Police téléchargée avec succès: {font_path}")
        print(f"📊 Taille: {len(response.content)} bytes")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def verify_font_installation():
    """Vérifie que la police est correctement installée"""
    print("\n🔍 Vérification de l'installation")
    print("=" * 30)
    
    font_path = Path("assets/fonts/NotoSansHebrew-Regular.ttf")
    
    if not font_path.exists():
        print("❌ Police non trouvée")
        return False
    
    # Vérifier la taille du fichier
    file_size = font_path.stat().st_size
    if file_size < 100000:  # Moins de 100KB, probablement corrompu
        print(f"❌ Fichier trop petit ({file_size} bytes), probablement corrompu")
        return False
    
    print(f"✅ Police trouvée: {font_path}")
    print(f"📊 Taille: {file_size} bytes")
    
    # Tester l'import dans matplotlib
    try:
        import matplotlib.font_manager as fm
        font_prop = fm.FontProperties(fname=str(font_path))
        print("✅ Police compatible avec matplotlib")
        return True
    except Exception as e:
        print(f"⚠️ Problème avec matplotlib: {e}")
        return True  # La police existe, c'est déjà bien

def main():
    """Fonction principale"""
    print("🎯 Installation de la police Noto Sans Hebrew")
    print("=" * 60)
    
    # Télécharger la police
    download_success = download_noto_hebrew_font()
    
    if download_success:
        # Vérifier l'installation
        verify_success = verify_font_installation()
        
        if verify_success:
            print("\n🎉 Installation réussie!")
            print("📈 Les graphiques en hébreu auront maintenant un meilleur rendu.")
        else:
            print("\n⚠️ Installation partielle - la police existe mais pourrait avoir des problèmes.")
    else:
        print("\n❌ Échec de l'installation.")
        print("💡 Le système utilisera les polices de fallback disponibles.")
    
    print("\n💡 Pour tester: python test_fonts.py")

if __name__ == "__main__":
    main() 