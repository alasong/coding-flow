from datetime import datetime


class UserManagementService:
    def __init__(self):
        self._users = {}
        self._next_id = 1

    def create_user(self, username, email, password_hash=None, full_name=None, is_active=True):
        if not username or not email:
            raise ValueError("Username and email are required")
        if username in self._users:
            raise ValueError(f"User with username '{username}' already exists")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Invalid email format")

        user_id = self._next_id
        self._next_id += 1
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash or "default_hash",
            "full_name": full_name or "",
            "is_active": is_active,
            "created_at": datetime.now().isoformat()
        }
        self._users[username] = user
        return user

    def get_user_by_username(self, username):
        if not username:
            return None
        return self._users.get(username)

    def get_user_by_id(self, user_id):
        if not isinstance(user_id, int) or user_id < 1:
            return None
        for user in self._users.values():
            if user["id"] == user_id:
                return user
        return None

    def update_user(self, username, **updates):
        if not username or username not in self._users:
            raise ValueError(f"User '{username}' not found")
        allowed_fields = {"email", "password_hash", "full_name", "is_active"}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields: {invalid_fields}")
        if "email" in updates and "@" not in updates["email"]:
            raise ValueError("Invalid email format")
        self._users[username].update(updates)
        self._users[username]["updated_at"] = datetime.now().isoformat()
        return self._users[username]

    def delete_user(self, username):
        if not username or username not in self._users:
            raise ValueError(f"User '{username}' not found")
        deleted_user = self._users.pop(username)
        deleted_user["deleted_at"] = datetime.now().isoformat()
        return deleted_user

    def list_users(self, active_only=False, limit=None, offset=0):
        users = list(self._users.values())
        if active_only:
            users = [u for u in users if u.get("is_active", False)]
        if offset >= len(users):
            return []
        end_idx = min(len(users), offset + (limit if limit else len(users)))
        return users[offset:end_idx]

    def count_users(self, active_only=False):
        if active_only:
            return sum(1 for u in self._users.values() if u.get("is_active", False))
        return len(self._users)