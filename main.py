import os
import sqlite3
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Papkalarni yaratish
UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
TEMPLATES_DIR = "templates"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI()

# Static fayllar va templatlar
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Ma'lumotlar bazasini sozlash
def init_database():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()

    # Portfolio items jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio_items
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     title
                     TEXT
                     NOT
                     NULL,
                     description
                     TEXT,
                     category
                     TEXT,
                     image_path
                     TEXT
                     NOT
                     NULL,
                     created_at
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP
                 )''')

    # Projects jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     title
                     TEXT
                     NOT
                     NULL,
                     description
                     TEXT,
                     technologies
                     TEXT,
                     github_link
                     TEXT,
                     live_link
                     TEXT,
                     image_path
                     TEXT,
                     created_at
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP
                 )''')

    # Skills jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     name
                     TEXT
                     NOT
                     NULL,
                     level
                     INTEGER,
                     category
                     TEXT,
                     icon
                     TEXT
                 )''')

    # Contacts jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS contacts
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     name
                     TEXT
                     NOT
                     NULL,
                     email
                     TEXT
                     NOT
                     NULL,
                     message
                     TEXT
                     NOT
                     NULL,
                     created_at
                     TIMESTAMP
                     DEFAULT
                     CURRENT_TIMESTAMP
                 )''')

    conn.commit()
    conn.close()


# Bazani ishga tushirish
init_database()


# Rasm yuklash uchun funksiya
def save_upload_file(upload_file: UploadFile, folder: str = "uploads") -> str:
    try:
        # Unique filename yaratish
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{upload_file.filename}"
        file_path = os.path.join(folder, filename)

        # Rasmni saqlash
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return filename
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rasm saqlashda xatolik: {str(e)}")
    finally:
        upload_file.file.close()


# Asosiy sahifa
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Mening Portfolio"
        }
    )


# Admin panel
@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )


# ============= PORTFOLIO ITEMS API =============
@app.post("/api/portfolio")
async def create_portfolio_item(
        title: str = None,
        description: str = None,
        category: str = None,
        file: UploadFile = File(None)
):
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()

        image_path = None
        if file:
            filename = save_upload_file(file)
            image_path = f"/uploads/{filename}"

        c.execute("""INSERT INTO portfolio_items (title, description, category, image_path)
                     VALUES (?, ?, ?, ?)""",
                  (title, description, category, image_path))

        item_id = c.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "id": item_id,
            "message": "Portfolio item qo'shildi"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/portfolio")
async def get_portfolio_items():
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute("""SELECT id, title, description, category, image_path, created_at
                     FROM portfolio_items
                     ORDER BY created_at DESC""")
        items = c.fetchall()
        conn.close()

        portfolio_list = []
        for item in items:
            portfolio_list.append({
                "id": item[0],
                "title": item[1],
                "description": item[2],
                "category": item[3],
                "image": item[4],
                "created_at": item[5]
            })

        return {"success": True, "items": portfolio_list}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.delete("/api/portfolio/{item_id}")
async def delete_portfolio_item(item_id: int):
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()

        # Rasmni o'chirish
        c.execute("SELECT image_path FROM portfolio_items WHERE id = ?", (item_id,))
        result = c.fetchone()
        if result and result[0]:
            image_path = result[0].replace("/uploads/", "")
            full_path = os.path.join("uploads", image_path)
            if os.path.exists(full_path):
                os.remove(full_path)

        c.execute("DELETE FROM portfolio_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

        return {"success": True, "message": "O'chirildi"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============= PROJECTS API =============
@app.post("/api/projects")
async def create_project(
        title: str,
        description: str = None,
        technologies: str = None,
        github_link: str = None,
        live_link: str = None,
        file: UploadFile = File(None)
):
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()

        image_path = None
        if file:
            filename = save_upload_file(file)
            image_path = f"/uploads/{filename}"

        c.execute("""INSERT INTO projects (title, description, technologies, github_link, live_link, image_path)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (title, description, technologies, github_link, live_link, image_path))

        project_id = c.lastrowid
        conn.commit()
        conn.close()

        return {"success": True, "id": project_id, "message": "Loyiha qo'shildi"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/projects")
async def get_projects():
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute("""SELECT id,
                            title,
                            description,
                            technologies,
                            github_link,
                            live_link,
                            image_path,
                            created_at
                     FROM projects
                     ORDER BY created_at DESC""")
        items = c.fetchall()
        conn.close()

        projects_list = []
        for item in items:
            projects_list.append({
                "id": item[0],
                "title": item[1],
                "description": item[2],
                "technologies": item[3],
                "github_link": item[4],
                "live_link": item[5],
                "image": item[6],
                "created_at": item[7]
            })

        return {"success": True, "items": projects_list}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============= SKILLS API =============
@app.post("/api/skills")
async def create_skill(name: str, level: int = 0, category: str = None, icon: str = None):
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute("""INSERT INTO skills (name, level, category, icon)
                     VALUES (?, ?, ?, ?)""",
                  (name, level, category, icon))
        skill_id = c.lastrowid
        conn.commit()
        conn.close()

        return {"success": True, "id": skill_id}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/skills")
async def get_skills():
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute("SELECT id, name, level, category, icon FROM skills ORDER BY category, name")
        items = c.fetchall()
        conn.close()

        skills_list = []
        for item in items:
            skills_list.append({
                "id": item[0],
                "name": item[1],
                "level": item[2],
                "category": item[3],
                "icon": item[4]
            })

        return {"success": True, "items": skills_list}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============= CONTACT API =============
@app.post("/api/contact")
async def send_message(name: str, email: str, message: str):
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute("""INSERT INTO contacts (name, email, message)
                     VALUES (?, ?, ?)""",
                  (name, email, message))
        conn.commit()
        conn.close()

        return {"success": True, "message": "Xabar yuborildi"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)l()