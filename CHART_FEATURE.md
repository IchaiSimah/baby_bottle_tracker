# 📈 Fonctionnalité de Graphiques de Consommation Quotidienne

## Vue d'ensemble

La nouvelle fonctionnalité de graphiques ajoute des courbes de consommation quotidienne aux rapports PDF du Baby Bottle Tracker. Ces graphiques permettent de visualiser facilement les tendances de consommation de lait de votre bébé sur une période donnée.

## ✨ Fonctionnalités

### Graphique de Consommation Quotidienne
- **Courbe temporelle** : Affiche la quantité totale de lait consommée chaque jour
- **Valeurs sur la courbe** : Chaque point affiche la quantité exacte en ml
- **Remplissage coloré** : Zone colorée sous la courbe pour une meilleure visualisation
- **Statistiques intégrées** : Moyenne, maximum et minimum affichés sur le graphique
- **Axes clairement expliqués** : Dates sur l'axe X, quantités en ml sur l'axe Y

### Caractéristiques Techniques
- **Haute résolution** : Graphiques générés en 300 DPI pour une qualité optimale
- **Thème cohérent** : Couleurs assorties au design général de l'application
- **Support multilingue** : Titres et labels traduits en français, anglais et hébreu
- **Gestion d'erreurs** : Le PDF continue de se générer même si le graphique échoue
- **Optimisation mémoire** : Graphiques générés en mémoire sans fichiers temporaires

## 🎨 Design du Graphique

### Couleurs
- **Couleur principale** : #2E86AB (bleu)
- **Couleur secondaire** : #A23B72 (rose)
- **Arrière-plan** : #F8F9FA (gris clair)

### Éléments Visuels
- **Courbe** : Ligne bleue épaisse avec points marqueurs
- **Remplissage** : Zone bleue semi-transparente sous la courbe
- **Valeurs** : Étiquettes blanches avec bordure bleue
- **Grille** : Lignes pointillées grises pour faciliter la lecture
- **Statistiques** : Boîte blanche avec bordure bleue en haut à droite

## 📊 Informations Affichées

### Sur la Courbe
- **Points de données** : Un point pour chaque jour avec consommation
- **Valeurs en ml** : Quantité exacte affichée au-dessus de chaque point
- **Jours sans données** : Affichés à 0ml pour montrer les jours sans biberons

### Statistiques Intégrées
- **📊 Moyenne** : Consommation moyenne par jour (jours avec données uniquement)
- **📈 Maximum** : Jour avec la plus forte consommation
- **📉 Minimum** : Jour avec la plus faible consommation (jours avec données uniquement)

## 🌍 Support Multilingue

### Français
- Titre : "Consommation Quotidienne"
- Axe X : "Date"
- Axe Y : "Quantité (ml)"
- Statistiques : "Moyenne", "Maximum", "Minimum"

### English
- Titre : "Daily Consumption Chart"
- Axe X : "Date"
- Axe Y : "Quantity (ml)"
- Statistiques : "Average", "Maximum", "Minimum"

### עברית (Hébreu)
- Titre : "גרף מזומן יומי"
- Axe X : "תאריך"
- Axe Y : "כמות (מ"ל)"
- Statistiques : "ממוצע", "מקסימום", "מינימום"

### Support Multilingue
- **Titres et labels** traduits en français, anglais et hébreu
- **Statistiques** adaptées à chaque langue
- **Lien d'information** traduit et cliquable dans toutes les langues

### Lien d'Information Officielle
Après le graphique, un lien cliquable est inclus pour rediriger vers des informations officielles sur les besoins nutritionnels des bébés :
- **Texte traduit** selon la langue sélectionnée
- **Lien cliquable** dans le PDF
- **Couleur distinctive** (bleu) pour indiquer qu'il s'agit d'un lien
- **Source officielle** : AlloBébé (lien configurable)

## 🔧 Installation

### Dépendances Requises
```bash
pip install matplotlib==3.7.2
pip install numpy
```

### Script d'Installation Automatique
```bash
python install_dependencies.py
```

## 🧪 Tests

### Script de Test
```bash
python test_chart_generation.py
```

Ce script :
- Crée des données de test réalistes
- Génère des graphiques dans les 3 langues
- Sauvegarde les graphiques pour inspection
- Vérifie que la génération fonctionne correctement

## 📱 Utilisation

### Dans l'Application
1. Cliquez sur "📄 PDF" dans le menu principal
2. Choisissez la période (7 ou 30 jours)
3. Sélectionnez la langue
4. Le graphique sera automatiquement inclus dans le PDF

### Intégration dans le PDF
- Le graphique apparaît après les statistiques générales
- Taille optimisée : 6 pouces de large × 3.6 pouces de haut
- Centré dans la page
- Explication des axes incluse
- **🔗 Lien cliquable** vers des informations officielles sur les besoins du bébé

## 🐛 Dépannage

### Problèmes Courants

#### Erreur d'Import Matplotlib
```
ImportError: No module named 'matplotlib'
```
**Solution** : Installer matplotlib avec `pip install matplotlib==3.7.2`

#### Erreur de Backend
```
RuntimeError: Invalid DISPLAY variable
```
**Solution** : Le backend 'Agg' est automatiquement configuré pour éviter ce problème

#### Problèmes de Police
```
Font family ['DejaVu Sans'] not found
```
**Solutions** :
1. **Installation automatique** : Exécuter `python install_dependencies.py` (inclut le téléchargement de Noto Sans Hebrew)
2. **Police Noto Sans Hebrew** : `python download_noto_font.py` pour un meilleur support de l'hébreu
3. **Linux** : `sudo apt-get install fonts-dejavu`
4. **Windows** : Les polices Arial sont généralement disponibles
5. **macOS** : Les polices Helvetica sont incluses par défaut
6. **Test des polices** : Exécuter `python test_fonts.py` pour diagnostiquer

### Police Noto Sans Hebrew
Pour un rendu optimal de l'hébreu dans les graphiques :
- **Téléchargement automatique** : Inclus dans `install_dependencies.py`
- **Téléchargement manuel** : `python download_noto_font.py`
- **Emplacement** : `assets/fonts/NotoSansHebrew-Regular.ttf`
- **Fallback** : Si la police n'est pas disponible, le système utilise les polices système

#### Graphique Vide
Si le graphique n'apparaît pas dans le PDF :
- Vérifiez qu'il y a des données de biberons pour la période
- Consultez les logs pour les erreurs de génération
- Le PDF continuera sans le graphique en cas d'erreur

### Test des Polices
Exécutez le script de test pour diagnostiquer les problèmes de police :
```bash
python test_fonts.py
```

Ce script :
- Vérifie la disponibilité des polices système
- Teste la configuration matplotlib
- Génère des graphiques de test dans toutes les langues
- Fournit des conseils de résolution

### Logs de Débogage
Les erreurs de génération de graphique sont loggées avec le préfixe :
```
Erreur lors de la création du graphique: [détails]
Erreur lors de l'ajout du graphique au PDF: [détails]
```

## 🔮 Améliorations Futures

### Fonctionnalités Prévues
- **Graphiques comparatifs** : Comparer plusieurs périodes
- **Tendances** : Lignes de tendance automatiques
- **Alertes** : Mise en évidence des jours anormaux
- **Export séparé** : Télécharger uniquement le graphique
- **Personnalisation** : Choix des couleurs et styles

### Optimisations Techniques
- **Cache des graphiques** : Éviter la régénération
- **Compression** : Réduire la taille des fichiers
- **Rendu vectoriel** : SVG pour une meilleure qualité
- **Animations** : Graphiques interactifs (futur)

## 📄 Licence

Cette fonctionnalité fait partie du projet Baby Bottle Tracker et suit les mêmes conditions de licence que le projet principal. 