#!/usr/bin/env python3
"""
Script pour télécharger la police hébreu Noto Sans Hebrew
"""

import os
import urllib.request
import sys

def download_hebrew_font():
    """Télécharge la police hébreu Noto Sans Hebrew"""
    
    # Créer le dossier assets/fonts s'il n'existe pas
    assets_fonts_dir = os.path.join("assets", "fonts")
    if not os.path.exists(assets_fonts_dir):
        os.makedirs(assets_fonts_dir)
        print(f"📁 Dossier créé : {assets_fonts_dir}")
    
    font_path = os.path.join(assets_fonts_dir, "NotoSansHebrew-Regular.ttf")
    
    # Vérifier si la police existe déjà
    if os.path.exists(font_path):
        print(f"✅ Police déjà présente : {font_path}")
        print(f"📁 Taille : {os.path.getsize(font_path)} bytes")
        return True
    
    # URLs alternatives pour télécharger la police
    font_urls = [
        "https://github.com/google/fonts/raw/main/ofl/notosanshebrew/NotoSansHebrew-Regular.ttf",
        "https://fonts.gstatic.com/s/notosanshebrew/v1/ieVc2YdFI3GCY6SyQy1KfStzYKZgzN1z0w.woff2",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanshebrew/NotoSansHebrew-Regular.ttf"
    ]
    
    for i, url in enumerate(font_urls, 1):
        try:
            print(f"📥 Tentative {i}/3 : Téléchargement depuis {url}")
            
            # Télécharger la police
            urllib.request.urlretrieve(url, font_path)
            
            # Vérifier que le fichier a été téléchargé
            if os.path.exists(font_path) and os.path.getsize(font_path) > 0:
                print(f"✅ Police téléchargée avec succès : {font_path}")
                print(f"📁 Taille : {os.path.getsize(font_path)} bytes")
                return True
            else:
                print("❌ Fichier téléchargé mais vide ou corrompu")
                
        except Exception as e:
            print(f"❌ Erreur avec l'URL {i} : {e}")
            continue
    
    print("❌ Impossible de télécharger la police depuis toutes les sources")
    return False

def create_fallback_font():
    """Crée une police de fallback simple pour l'hébreu"""
    print("🔧 Création d'une police de fallback...")
    
    # Créer un fichier de police minimal (ceci est un exemple, pas une vraie police)
    fallback_path = os.path.join("assets", "fonts", "fallback_hebrew.txt")
    
    with open(fallback_path, 'w', encoding='utf-8') as f:
        f.write("Ce fichier indique que la police hébreu n'a pas pu être téléchargée.\n")
        f.write("Le système utilisera les polices système disponibles.\n")
    
    print(f"📝 Fichier de fallback créé : {fallback_path}")
    return True

def main():
    """Fonction principale"""
    print("🔤 Téléchargement de la police hébreu Noto Sans Hebrew\n")
    
    # Essayer de télécharger la police
    success = download_hebrew_font()
    
    if not success:
        print("\n⚠️ Échec du téléchargement, création d'un fallback...")
        create_fallback_font()
    
    print("\n📊 Résumé :")
    assets_fonts_dir = os.path.join("assets", "fonts")
    if os.path.exists(assets_fonts_dir):
        files = os.listdir(assets_fonts_dir)
        print(f"📁 Contenu du dossier {assets_fonts_dir}:")
        for file in files:
            file_path = os.path.join(assets_fonts_dir, file)
            size = os.path.getsize(file_path)
            print(f"  • {file} ({size} bytes)")
    
    if success:
        print("\n🎉 Police hébreu prête à être utilisée !")
    else:
        print("\n⚠️ La police hébreu n'a pas pu être téléchargée.")
        print("💡 Le système utilisera les polices système disponibles.")

if __name__ == "__main__":
    main() 