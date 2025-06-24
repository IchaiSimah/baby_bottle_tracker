#!/usr/bin/env python3
"""
Script pour créer une solution de police hébreu alternative
"""

import os
import urllib.request
import shutil

def download_alternative_hebrew_font():
    """Télécharge une police hébreu alternative"""
    
    # Créer le dossier assets/fonts s'il n'existe pas
    assets_fonts_dir = os.path.join("assets", "fonts")
    if not os.path.exists(assets_fonts_dir):
        os.makedirs(assets_fonts_dir)
        print(f"📁 Dossier créé : {assets_fonts_dir}")
    
    font_path = os.path.join(assets_fonts_dir, "hebrew_font.ttf")
    
    # URLs alternatives pour des polices hébreu
    font_urls = [
        "https://fonts.gstatic.com/s/notosans/v28/o-0IIpQlx3QUlC5A4PNr5TRA.woff2",
        "https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxK.woff2",
        "https://fonts.gstatic.com/s/opensans/v40/memSYaGs126MiZpBA-UvWbX2vVnXBbObj2OVZyOOSr4dVJWUgsjZ0B4gaVI.woff2"
    ]
    
    for i, url in enumerate(font_urls, 1):
        try:
            print(f"📥 Tentative {i}/3 : Téléchargement d'une police Unicode...")
            
            # Télécharger la police
            urllib.request.urlretrieve(url, font_path)
            
            # Vérifier que le fichier a été téléchargé
            if os.path.exists(font_path) and os.path.getsize(font_path) > 0:
                print(f"✅ Police Unicode téléchargée : {font_path}")
                print(f"📁 Taille : {os.path.getsize(font_path)} bytes")
                return font_path
            else:
                print("❌ Fichier téléchargé mais vide ou corrompu")
                
        except Exception as e:
            print(f"❌ Erreur avec l'URL {i} : {e}")
            continue
    
    return None

def create_hebrew_font_info():
    """Crée un fichier d'information sur la police hébreu"""
    info_path = os.path.join("assets", "fonts", "hebrew_font_info.txt")
    
    info_content = """Police Hébreu - Information

Ce fichier contient les informations sur la configuration de la police hébreu.

SOLUTIONS RECOMMANDÉES :

1. POLICE SYSTÈME (Recommandée)
   - Arial Unicode MS (Windows)
   - DejaVuSans (Linux)
   - Helvetica (Mac)

2. TÉLÉCHARGEMENT MANUEL
   - Téléchargez Noto Sans Hebrew depuis Google Fonts
   - Placez le fichier dans assets/fonts/NotoSansHebrew-Regular.ttf

3. POLICE ALTERNATIVE
   - Utilisez une police Unicode standard
   - La plupart des polices modernes supportent l'hébreu

CONFIGURATION :
- Le système essaiera d'abord la police du projet
- Puis les polices système avec support Unicode
- En dernier recours : Helvetica

POUR RENDER :
- Incluez la police dans le projet
- Ou utilisez les polices système disponibles
"""
    
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print(f"📝 Fichier d'information créé : {info_path}")
    return info_path

def copy_system_font():
    """Essaie de copier une police système qui supporte l'hébreu"""
    system_fonts = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialuni.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    
    assets_fonts_dir = os.path.join("assets", "fonts")
    if not os.path.exists(assets_fonts_dir):
        os.makedirs(assets_fonts_dir)
    
    for font_path in system_fonts:
        if os.path.exists(font_path):
            try:
                dest_path = os.path.join(assets_fonts_dir, "system_hebrew_font.ttf")
                shutil.copy2(font_path, dest_path)
                print(f"✅ Police système copiée : {font_path} -> {dest_path}")
                return dest_path
            except Exception as e:
                print(f"❌ Erreur copie {font_path} : {e}")
                continue
    
    return None

def main():
    """Fonction principale"""
    print("🔤 Configuration de la police hébreu\n")
    
    # Essayer de télécharger une police alternative
    font_path = download_alternative_hebrew_font()
    
    if not font_path:
        print("📥 Échec du téléchargement, essai de copie de police système...")
        font_path = copy_system_font()
    
    if not font_path:
        print("📝 Création d'un fichier d'information...")
        create_hebrew_font_info()
    
    print("\n📊 Résumé :")
    assets_fonts_dir = os.path.join("assets", "fonts")
    if os.path.exists(assets_fonts_dir):
        files = os.listdir(assets_fonts_dir)
        print(f"📁 Contenu du dossier {assets_fonts_dir}:")
        for file in files:
            file_path = os.path.join(assets_fonts_dir, file)
            size = os.path.getsize(file_path)
            print(f"  • {file} ({size} bytes)")
    
    if font_path:
        print(f"\n🎉 Police prête : {font_path}")
    else:
        print("\n⚠️ Aucune police téléchargée.")
        print("💡 Le système utilisera les polices système avec fallback.")

if __name__ == "__main__":
    main() 