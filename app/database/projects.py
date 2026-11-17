from app.database.connection import get_connection


def create_project(title, project_type, description=""):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO projects (title, project_type, description)
            VALUES (?, ?, ?)
            """,
            (title, project_type, description)
        )
        conn.commit()
        return cursor.lastrowid


def get_projects():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM projects ORDER BY id DESC"
        ).fetchall()


def get_project(project_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()


def delete_project(project_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM projects WHERE id = ?",
            (project_id,)
        )
        conn.commit()
        return cursor.rowcount > 0