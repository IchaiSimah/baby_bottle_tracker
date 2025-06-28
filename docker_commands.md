# 🐳 Docker Commands - Baby Bottle Tracker Bot

## 📊 **Statut et Logs**

```bash
# Voir le statut des containers
docker-compose ps

# Voir les logs du bot
docker-compose logs bot

# Voir les logs en temps réel
docker-compose logs -f bot

# Voir tous les logs
docker-compose logs -f
```

## 🚀 **Démarrage/Arrêt**

```bash
# Démarrer le bot
docker-compose up -d

# Arrêter le bot
docker-compose down

# Redémarrer le bot (rapide)
docker-compose restart bot

# Redémarrer tout
docker-compose restart
```

## 🔧 **Développement**

```bash
# Rebuild après modification du code
docker-compose down
docker-compose up --build -d

# Entrer dans le container bot
docker exec -it baby_bottle_tracker_bot bash

# Voir les logs depuis l'intérieur
docker exec -it baby_bottle_tracker_bot python main.py
```

## 📁 **Base de données**

```bash
# Voir le contenu de la base
docker exec -it baby_bottle_tracker_db sqlite3 /data/baby_bottle_tracker.db ".tables"

# Voir les groupes
docker exec -it baby_bottle_tracker_db sqlite3 /data/baby_bottle_tracker.db "SELECT * FROM groups;"

# Voir les entrées
docker exec -it baby_bottle_tracker_db sqlite3 /data/baby_bottle_tracker.db "SELECT * FROM entries LIMIT 5;"
```

## 🧹 **Nettoyage**

```bash
# Arrêter et supprimer les volumes (ATTENTION: supprime les données)
docker-compose down -v

# Supprimer les images
docker rmi bottle-track-server-version_bot

# Nettoyer tout
docker system prune -a
```

## 🆘 **Dépannage**

```bash
# Voir les logs d'erreur
docker-compose logs bot | grep -i error

# Vérifier l'espace disque
docker system df

# Voir les processus dans le container
docker exec -it baby_bottle_tracker_bot ps aux
```

## 📝 **Commandes rapides**

```bash
# Statut rapide
docker-compose ps

# Logs rapides
docker-compose logs --tail=20 bot

# Redémarrage rapide
docker-compose restart bot
``` 