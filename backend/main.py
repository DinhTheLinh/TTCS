

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
import sqlite3
import os
from datetime import datetime
from contextlib import asynccontextmanager

DATABASE = "auth.db"

def init_db():
    if not os.path.exists(DATABASE): 
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database khởi tạo thành công")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    print("Ứng dụng đang dừng...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class SearchRequest(BaseModel):
    category: str
    sketch_data: str
    username: str

def get_user(username: str):
    conn = sqlite3.connect(DATABASE) 
    cursor = conn.cursor() 
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,)) 
    user = cursor.fetchone() 
    conn.close()
    return user

def create_user(username: str, password: str):
    password_hash = pwd_context.hash(password)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)

def generate_token(username: str) -> str:
    import base64
    token_data = f"{username}:{datetime.now().isoformat()}"
    token = base64.b64encode(token_data.encode()).decode()
    return token

@app.get("/")
def read_root():
    return {
        "message": "🔐 Draw & Find Authentication Backend",
        "endpoints": {
            "register": "POST /register",
            "login": "POST /login"
        }
    }

@app.post("/register")
async def register(user: UserRegister):
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Username và password không được trống")
    
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username phải ít nhất 3 ký tự")
    
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải ít nhất 6 ký tự")
    
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    success = create_user(user.username, user.password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Lỗi khi tạo tài khoản")
    
    access_token = generate_token(user.username)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/login")
async def login(user: UserLogin):
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Username và password không được trống")
    
    db_user = get_user(user.username)
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Tên đăng nhập không tồn tại")
    
    user_id, username, password_hash = db_user
    
    if not verify_password(user.password, password_hash):
        raise HTTPException(status_code=401, detail="Mật khẩu không chính xác")
    
    access_token = generate_token(username)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer" 
    }

@app.post("/search") 
async def search(request: SearchRequest):
    if request.category not in ['animal', 'product']:
        raise HTTPException(
            status_code=400, 
            detail="Category phải là 'animal' hoặc 'product'"
        )
    
    if not request.username:
        raise HTTPException(status_code=400, detail="Username không được trống")
    
    db_user = get_user(request.username)
    if not db_user:
        raise HTTPException(status_code=401, detail="User không tồn tại")
    
    if request.category == 'animal':
        animals = ['dog', 'cat', 'rabbit']
        results = [
            {
                "id": i + 1,
                "name": f"{animals[i % 3]}_{str(i + 1).zfill(3)}",
                "type": ["Chó", "Mèo", "Thỏ"][i % 3],
                "match_score": round(0.95 - (i * 0.01), 2)
            }
            for i in range(14)
        ]
        message = f"Tìm thấy {len(results)} con vật phù hợp"
    
    else:
        products = ['shoe', 'bag', 'chair']
        results = [
            {
                "id": 100 + i + 1,
                "name": f"{products[i % 3]}_{str(i + 1).zfill(3)}",
                "type": ["Giày", "Túi xách", "Ghế"][i % 3],
                "match_score": round(0.92 - (i * 0.01), 2)
            }
            for i in range(14)
        ]
        message = f"Tìm thấy {len(results)} sản phẩm phù hợp"
    
    return {
        "category": request.category,
        "results": results,
        "total_count": len(results),
        "message": message
    }

@app.get("/health")
def health_check():
    return {"status": " Backend is running"}

if __name__ == "__main__":
    import uvicorn
    print(" Khởi động Draw & Find Backend...")
    print(" Server chạy tại: http://localhost:8000")
    print(" API Docs (Swagger UI) tại: http://localhost:8000/docs")
    print(" Alternative Docs (ReDoc) tại: http://localhost:8000/redoc")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
