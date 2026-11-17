from app.database.connection import get_connection


def create_character(project_id, name, description=""):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO characters (project_id, name, description)
            VALUES (?, ?, ?)
            """,
            (project_id, name, description)
        )
        conn.commit()
        return cursor.lastrowid


def get_characters(project_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM characters
            WHERE project_id = ?
            ORDER BY id
            """,
            (project_id,)
        ).fetchall()


def get_character(character_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM characters WHERE id = ?",
            (character_id,)
        ).fetchone()