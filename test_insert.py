from database import get_supabase_client, GROUPS_TABLE


def test_insert_user_id(user_id):
    client = get_supabase_client()
    # On force l'insertion d'un entier
    data = {
        'name': f'test_group_{user_id}',
        'users': [int(user_id)],
        'time_difference': 0,
        'bottles_to_show': 5,
        'poops_to_show': 1
    }
    print("Inserting:", data)
    client.table(GROUPS_TABLE).insert(data).execute()
    print("Insertion done.")

    # Lecture du groupe pour vérifier le type dans la colonne users
    result = client.table(GROUPS_TABLE).select("id,users").eq('name', f'test_group_{user_id}').execute()
    print("Lecture du groupe inséré :")
    for row in result.data:
        print(f"users = {row['users']} (types: {[type(u) for u in row['users']]})")

    # Test de lecture directe de tous les groupes
    print("\nTest de lecture de tous les groupes :")
    all_groups = client.table(GROUPS_TABLE).select("id,name,users").execute()
    for group in all_groups.data:
        print(f"Groupe {group['name']}: users = {group['users']} (types: {[type(u) for u in group['users']]})")


if __name__ == "__main__":
    test_insert_user_id(755577808) 