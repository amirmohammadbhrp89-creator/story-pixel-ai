from app.integrations.gemini import generate_text
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal
from contextlib import closing
import sqlite3
import html

app = FastAPI(
    title="STORY PIXEL AI",
    description="AI Film & Animation Production Studio",
    version="0.2.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(__file__).resolve().parent / "story_pixelai.db"

FOLDERS = {
    "series": BASE_DIR / "03_SERIES",
    "films": BASE_DIR / "04_STANDALONE_FILMS",
    "reels": BASE_DIR / "05_SHORT_REELS",
}

for folder in FOLDERS.values():
    folder.mkdir(parents=True, exist_ok=True)


# DATABASE

def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    with closing(db_connection()) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            project_type TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            episode_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            FOREIGN KEY(project_id) REFERENCES projects(id)
                ON DELETE CASCADE,
            UNIQUE(project_id, episode_number)
        );

        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            FOREIGN KEY(project_id) REFERENCES projects(id)
                ON DELETE CASCADE
        );
        """)
        conn.commit()


init_database()


# DATA MODELS

class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    project_type: Literal["series", "film", "reel"]
    description: str = Field(default="", max_length=1000)


class EpisodeCreate(BaseModel):
    episode_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


class CharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


# PROJECT API

@app.get("/api/projects")
def get_projects():
    with closing(db_connection()) as conn:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/projects")
def create_project(data: ProjectCreate):
    with closing(db_connection()) as conn:
        cursor = conn.execute(
            """INSERT INTO projects
            (title, project_type, description)
            VALUES (?, ?, ?)""",
            (data.title.strip(), data.project_type, data.description)
        )
        conn.commit()
        return {"message": "Project created", "id": cursor.lastrowid}


# EPISODE API

@app.get("/api/projects/{project_id}/episodes")
def get_episodes(project_id: int):
    with closing(db_connection()) as conn:
        project = conn.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(404, "Project not found")

        rows = conn.execute(
            """SELECT * FROM episodes
            WHERE project_id = ? ORDER BY episode_number""",
            (project_id,)
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/projects/{project_id}/episodes")
def create_episode(project_id: int, data: EpisodeCreate):
    with closing(db_connection()) as conn:
        project = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(404, "Project not found")

        if project["project_type"] != "series":
            raise HTTPException(400, "Episodes are only for series")

        try:
            cursor = conn.execute(
                """INSERT INTO episodes
                (project_id, episode_number, title, description)
                VALUES (?, ?, ?, ?)""",
                (project_id, data.episode_number,
                 data.title.strip(), data.description)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, "This episode number already exists")

        return {"message": "Episode created", "id": cursor.lastrowid}


# CHARACTER API

@app.get("/api/projects/{project_id}/characters")
def get_characters(project_id: int):
    with closing(db_connection()) as conn:
        project = conn.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(404, "Project not found")

        rows = conn.execute(
            "SELECT * FROM characters WHERE project_id = ? ORDER BY id",
            (project_id,)
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/projects/{project_id}/characters")
def create_character(project_id: int, data: CharacterCreate):
    with closing(db_connection()) as conn:
        project = conn.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(404, "Project not found")

        cursor = conn.execute(
            """INSERT INTO characters
            (project_id, name, description)
            VALUES (?, ?, ?)""",
            (project_id, data.name.strip(), data.description)
        )
        conn.commit()
        return {"message": "Character created", "id": cursor.lastrowid}


# DASHBOARD

@app.get("/", response_class=HTMLResponse)
def dashboard():
    with closing(db_connection()) as conn:
        projects = conn.execute(
            "SELECT * FROM projects ORDER BY id DESC"
        ).fetchall()

        counts = {
            "series": sum(1 for p in projects if p["project_type"] == "series"),
            "film": sum(1 for p in projects if p["project_type"] == "film"),
            "reel": sum(1 for p in projects if p["project_type"] == "reel"),
        }

        cards = ""

        for project in projects:
            pid = project["id"]
            title = html.escape(project["title"])
            description = html.escape(project["description"] or "")
            kind = project["project_type"]

            kind_name = {
                "series": "سریال",
                "film": "فیلم مستقل",
                "reel": "ویدیوی کوتاه"
            }.get(kind, kind)

            episodes = conn.execute(
                """SELECT * FROM episodes
                WHERE project_id = ? ORDER BY episode_number""",
                (pid,)
            ).fetchall()

            characters = conn.execute(
                "SELECT * FROM characters WHERE project_id = ?",
                (pid,)
            ).fetchall()

            episode_html = "".join(
                f"<li>قسمت {e['episode_number']}: "
                f"{html.escape(e['title'])}</li>"
                for e in episodes
            ) or "<li>هنوز قسمتی ثبت نشده</li>"

            character_html = "".join(
                f"<li>{html.escape(c['name'])}</li>"
                for c in characters
            ) or "<li>هنوز شخصیتی ثبت نشده</li>"

            episode_form = ""
            if kind == "series":
                episode_form = f"""
                <form class="subform" onsubmit="addEpisode(event,{pid})">
                    <input name="episode_number" type="number"
                        min="1" placeholder="شماره قسمت" required>
                    <input name="title" placeholder="نام قسمت" required>
                    <button>افزودن قسمت</button>
                </form>
                """

            cards += f"""
            <article class="project">
                <span class="tag">{kind_name}</span>
                <h3>{title}</h3>
                <p>{description}</p>
                <div class="details">
                    <div>
                        <b>قسمت‌ها</b>
                        <ul>{episode_html}</ul>
                    </div>
                    <div>
                        <b>شخصیت‌ها</b>
                        <ul>{character_html}</ul>
                    </div>
                </div>
                {episode_form}
                <form class="subform"
                    onsubmit="addCharacter(event,{pid})">
                    <input name="name" placeholder="نام شخصیت" required>
                    <input name="description"
                        placeholder="توضیح شخصیت">
                    <button>افزودن شخصیت</button>
                </form>
            </article>
            """

    if not cards:
        cards = '<p class="empty">هنوز پروژه‌ای نساختی. اولین پروژه‌ات رو ایجاد کن!</p>'

    page = """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>STORY PIXEL AI</title>
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0; padding: 28px;
                background: #10121b; color: #f4f2ff;
                font-family: Tahoma, sans-serif;
            }
            header {
                padding: 25px; border-radius: 20px;
                background: linear-gradient(120deg,#282344,#191d30);
                margin-bottom: 22px;
            }
            h1 { color: #c2a7ff; margin-top: 0; }
            .stats,.projects {
                display: grid;
                grid-template-columns: repeat(auto-fit,minmax(220px,1fr));
                gap: 16px; margin-bottom: 22px;
            }
            .stat,.project,.panel {
                background: #202436; padding: 20px;
                border-radius: 16px; border: 1px solid #343951;
            }
            .number { font-size: 30px; color: #c2a7ff; }
            input,select,button {
                width: 100%; padding: 12px; margin: 6px 0;
                border: 0; border-radius: 9px; font-family: inherit;
            }
            input,select { background: #111625; color: white; }
            button {
                background: #9b7bea; color: #fff;
                cursor: pointer; font-weight: bold;
            }
            button:hover { background: #805ed0; }
            .tag {
                color: #c2a7ff; font-size: 13px;
            }
            .details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            li { margin: 8px 0; color: #d0d2e0; }
            .subform {
                border-top: 1px solid #383d52;
                padding-top: 10px; margin-top: 12px;
            }
            .empty { color: #c5bddb; }
            @media(max-width:600px) {
                body { padding: 14px; }
                .details { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <header>
            <h1>STORY PIXEL AI</h1>
            <p>استودیوی هوشمند تولید فیلم، سریال و انیمیشن</p>
            <small>Production Engine v0.2</small>
        </header>

        <section class="stats">
            <div class="stat"><p>سریال‌ها</p>
                <div class="number">COUNT_SERIES</div></div>
            <div class="stat"><p>فیلم‌های مستقل</p>
                <div class="number">COUNT_FILMS</div></div>
            <div class="stat"><p>ویدیوهای کوتاه</p>
                <div class="number">COUNT_REELS</div></div>
        </section>

        <section class="panel">
            <h2>ساخت پروژه جدید</h2>
            <form onsubmit="createProject(event)">
                <input name="title" placeholder="نام پروژه" required>
                <select name="project_type">
                    <option value="series">سریال</option>
                    <option value="film">فیلم مستقل</option>
                    <option value="reel">ویدیوی کوتاه</option>
                </select>
                <input name="description" placeholder="توضیحات پروژه">
                <button>+ ساخت پروژه</button>
            </form>
        </section>

        <h2>پروژه‌های من</h2>
        <section class="projects">PROJECT_CARDS</section>

        <script>
            async function sendData(url, data) {
                const response = await fetch(url, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (!response.ok) {
                    alert(result.detail || "خطا در ثبت اطلاعات");
                    return false;
                }
                return true;
            }

            async function createProject(event) {
                event.preventDefault();
                const f = event.target;
                const ok = await sendData("/api/projects", {
                    title: f.title.value,
                    project_type: f.project_type.value,
                    description: f.description.value
                });
                if (ok) location.reload();
            }

            async function addEpisode(event, id) {
                event.preventDefault();
                const f = event.target;
                const ok = await sendData(
                    `/api/projects/${id}/episodes`, {
                        episode_number: Number(f.episode_number.value),
                        title: f.title.value
                    }
                );
                if (ok) location.reload();
            }

            async function addCharacter(event, id) {
                event.preventDefault();
                const f = event.target;
                const ok = await sendData(
                    `/api/projects/${id}/characters`, {
                        name: f.name.value,
                        description: f.description.value
                    }
                );
                if (ok) location.reload();
            }
        </script>
    </body>
    </html>
    """

    page = page.replace("COUNT_SERIES", str(counts["series"]))
    page = page.replace("COUNT_FILMS", str(counts["film"]))
    page = page.replace("COUNT_REELS", str(counts["reel"]))
    page = page.replace("PROJECT_CARDS", cards)

    return page


@app.get("/health")
def health():
    return {
        "status": "online",
        "studio": "STORY PIXEL AI",
        "version": "0.2.0"
    }
class AIGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)


@app.post("/api/ai/generate")
async def ai_generate(data: AIGenerateRequest):
    try:
        result =await generate_text(data.prompt)

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )