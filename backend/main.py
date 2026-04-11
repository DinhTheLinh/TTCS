# ============================================================================
# 🔐 DRAW & FIND BACKEND - FastAPI Authentication Server
# ============================================================================
# File này là backend chính của ứng dụng tìm kiếm hình ảnh "Draw & Find"
# Chức năng: Xác thực người dùng (đăng ký/đăng nhập) và xử lý tìm kiếm
# ============================================================================

# ========== IMPORT CÁC THƯ VIỆN CẦN THIẾT ==========
from fastapi import FastAPI, HTTPException, File, UploadFile           # Framework web API
from fastapi.middleware.cors import CORSMiddleware  # Cho phép kết nối từ frontend
from pydantic import BaseModel                       # Xác định cấu trúc dữ liệu request/response
from passlib.context import CryptContext             # Mã hóa password
import sqlite3                                        # Database SQLite
import os                                             # Làm việc với file/folder
from datetime import datetime                        # Xử lý thời gian
from contextlib import asynccontextmanager           # Quản lý vòng đời ứng dụng
import shutil
import uuid
from fastapi.staticfiles import StaticFiles
from inference import SketchRetrievalModel


# ========== CẤU HÌNH CƠ SỞ DỮ LIỆU ==========
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

model = SketchRetrievalModel(
    model_path="clip_triplet.pth",
    embeddings_path="photo_embeddings.pt",
    paths_json_path="photo_paths.json"
)

DATABASE = "auth.db" # Tên file database SQLite

def init_db():
    """
    Khởi tạo database - Tạo bảng nếu chưa có:
    1. users: lưu tài khoản người dùng
    """
    if not os.path.exists(DATABASE):
        # Nếu file database chưa tồn tại thì tạo mới
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # ===== Bảng users: lưu thông tin tài khoản =====
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,        -- ID tự động tăng
                username TEXT UNIQUE NOT NULL,               -- Tên đăng nhập (không được trùng)
                password_hash TEXT NOT NULL,                 -- Mật khẩu được mã hóa
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Ngày tạo
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database khởi tạo thành công")

# ========== QUẢN LÝ VÒNG ĐỜI ỨNG DỤNG ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý sự kiện khởi động và tắt ứng dụng
    - Khởi động: Khởi tạo database
    - Tắt: In thông báo dừng ứng dụng
    """
    # ===== KHI ỨNG DỤNG KHỞI ĐỘNG =====
    init_db()
    yield
    # ===== KHI ỨNG DỤNG TẮTED =====
    print("🛑 Ứng dụng đang dừng...")

# ========== TẠO FASTAPI APP ==========
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="data/photo"), name="static")
# ========== CẤU HÌNH CORS ==========
# CORS cho phép frontend (React) trên các port khác nhau có thể gọi API này
app.add_middleware(
    CORSMiddleware,
    # Cho phép các địa chỉ frontend này kết nối
    allow_origins=[
        "http://localhost:3000",      # React dev server (mặc định)
        "http://localhost:5173",      # Vite dev server (port 5173)
        "http://localhost:5174",      # Vite dev server (port 5174)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",  # Cho phép bất kỳ port nào
    allow_credentials=True,           # Cho phép gửi cookie
    allow_methods=["*"],              # Cho phép tất cả HTTP methods (GET, POST, PUT, DELETE...)
    allow_headers=["*"],              # Cho phép tất cả headers
)

# ========== CẤU HÌNH MÃ HÓA MẬT KHẨU ==========
# Sử dụng pbkdf2_sha256 để mã hóa mật khẩu trước khi lưu
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ========== CÁC MODEL DỮ LIỆU ==========
# Các class này định nghĩa cấu trúc của request/response

class UserRegister(BaseModel):
    """Model cho request đăng ký tài khoản"""
    username: str   # Tên đăng nhập
    password: str   # Mật khẩu

class UserLogin(BaseModel):
    """Model cho request đăng nhập"""
    username: str   # Tên đăng nhập
    password: str   # Mật khẩu

class TokenResponse(BaseModel):
    """Model cho response trả về token"""
    access_token: str  # Token để xác thực các request tiếp theo
    token_type: str    # Loại token (mặc định là 'bearer')

class SearchRequest(BaseModel):
    """Model cho request tìm kiếm"""
    category: str    # Loại tìm kiếm: 'animal' (con vật) hoặc 'product' (sản phẩm)
    sketch_data: str # Dữ liệu hình vẽ được chuyển thành base64
    username: str    # Tên người dùng

# ==================== CÁC HÀM QUẢN LÝ DATABASE ====================

def get_user(username: str):
    """
    TÌM KIẾM USER TRONG DATABASE
    - Input: username (tên người dùng)
    - Output: (id, username, password_hash) hoặc None nếu không tìm thấy
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username: str, password: str):
    """
    TẠO USER MỚI
    - Input: username (tên người dùng) và password (mật khẩu)
    - Output: True (tạo thành công) hoặc False (tạo thất bại)
    - Mật khẩu được mã hóa trước khi lưu
    """
    password_hash = pwd_context.hash(password)  # Mã hóa mật khẩu
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
        # Lỗi này xảy ra khi username đã tồn tại (UNIQUE constraint)
        conn.close()
        return False

def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    KIỂM TRA MẬT KHẨU
    - Input: plain_password (mật khẩu nhập vào) và password_hash (mật khẩu đã mã hóa từ database)
    - Output: True (mật khẩu đúng) hoặc False (mật khẩu sai)
    """
    return pwd_context.verify(plain_password, password_hash)

def generate_token(username: str) -> str:
    """
    TẠO TOKEN XÁC THỰC
    - Input: username (tên người dùng)
    - Output: token (chuỗi base64 chứa username và thời gian)
    - Token dùng để xác thực các request tiếp theo của user
    """
    import base64
    token_data = f"{username}:{datetime.now().isoformat()}"  # username + thời gian hiện tại
    token = base64.b64encode(token_data.encode()).decode()   # Mã hóa thành base64
    return token

# ==================== CÁC API ENDPOINTS (Xác thực) ====================

@app.get("/")
def read_root():
    """
    ENDPOINT GỐC - Trả về thông tin về API
    - Method: GET
    - URL: http://localhost:8000/
    """
    return {
        "message": "🔐 Draw & Find Authentication Backend",
        "endpoints": {
            "register": "POST /register",
            "login": "POST /login"
        }
    }

@app.post("/register")
async def register(user: UserRegister):
    """
    ENDPOINT ĐĂNG KÝ TÀI KHOẢN MỚI
    - Method: POST
    - URL: http://localhost:8000/register
    
    Request body (gửi từ frontend):
    {
        "username": "myuser",      // Tên đăng nhập (≥3 ký tự)
        "password": "mypassword123" // Mật khẩu (≥6 ký tự)
    }
    
    Response nếu thành công (status 200):
    {
        "access_token": "bXl1c2VyOjIwMjYtMDMtMjM...",
        "token_type": "bearer"
    }
    
    Response nếu thất bại (status 400):
    {
        "detail": "Tên đăng nhập đã tồn tại"
    }
    """
    # ===== KIỂM TRA TÍNH HỢP LỆ CỦA DỮ LIỆU =====
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Username và password không được trống")
    
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username phải ít nhất 3 ký tự")
    
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải ít nhất 6 ký tự")
    
    # ===== KIỂM TRA USERNAME ĐÃ TỒN TẠI CHƯA =====
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    # ===== TẠO USER MỚI TRONG DATABASE =====
    success = create_user(user.username, user.password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Lỗi khi tạo tài khoản")
    
    # ===== TẠO TOKEN VÀ TRẢ VỀ =====
    access_token = generate_token(user.username)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/login")
async def login(user: UserLogin):
    """
    ENDPOINT ĐĂNG NHẬP
    - Method: POST
    - URL: http://localhost:8000/login
    
    Request body (gửi từ frontend):
    {
        "username": "myuser",
        "password": "mypassword123"
    }
    
    Response nếu thành công (status 200):
    {
        "access_token": "bXl1c2VyOjIwMjYtMDMtMjM...",
        "token_type": "bearer"
    }
    
    Response nếu thất bại (status 401):
    {
        "detail": "Mật khẩu không chính xác"
    }
    """
    # ===== KIỂM TRA TÍNH HỢP LỆ =====
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Username và password không được trống")
    
    # ===== TÌM USER TRONG DATABASE =====
    db_user = get_user(user.username)
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Tên đăng nhập không tồn tại")
    
    # ===== LẤY THÔNG TIN USER =====
    user_id, username, password_hash = db_user
    
    # ===== KIỂM TRA MẬT KHẨU =====
    if not verify_password(user.password, password_hash):
        raise HTTPException(status_code=401, detail="Mật khẩu không chính xác")
    
    # ===== TẠO TOKEN VÀ TRẢ VỀ =====
    access_token = generate_token(username)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ==================== CÁC API ENDPOINTS (Tìm kiếm) ====================

@app.post("/search")
async def search(request: SearchRequest):
    """
    ENDPOINT TÌM KIẾM HÌNH ÃNH
    - Method: POST
    - URL: http://localhost:8000/search
    
    Request body (gửi từ frontend):
    {
        "category": "animal" hoặc "product",  // Loại tìm kiếm
        "sketch_data": "iVBORw0KGgoAAAANS...", // Dữ liệu hình vẽ (base64)
        "username": "myuser"                   // Tên người dùng
    }
    
    Response nếu thành công (status 200):
    {
        "category": "animal",
        "results": [
            {"id": 1, "name": "dog_001", "type": "Chó", "match_score": 0.95},
            {"id": 2, "name": "cat_001", "type": "Mèo", "match_score": 0.93},
            ...
        ],
        "total_count": 14,
        "message": "Tìm thấy 14 con vật phù hợp"
    }
    
    Lưu ý:
    - Hiện tại dùng mock data (dữ liệu giả)
    - Sau này có thể kết nối ML model hoặc database thực
    """
    
    # ===== KIỂM TRA CATEGORY HỢP LỆ =====
    if request.category not in ['animal', 'product']:
        raise HTTPException(
            status_code=400, 
            detail="Category phải là 'animal' hoặc 'product'"
        )
    
    # ===== KIỂM TRA USERNAME =====
    if not request.username:
        raise HTTPException(status_code=400, detail="Username không được trống")
    
    # ===== KIỂM TRA USER CÓ TỒN TẠI KHÔNG =====
    db_user = get_user(request.username)
    if not db_user:
        raise HTTPException(status_code=401, detail="User không tồn tại")
    
    # ===== XỬ LÝ TÌM KIẾM THEO LOẠI =====
    # Trong thực tế: gọi ML model hoặc truy vấn database
    # Hiện tại: tạo mock data để test
    
    if request.category == 'animal':
        # TẠO MOCK RESULTS CHO CON VẬT
        animals = ['dog', 'cat', 'rabbit']  # Danh sách tên con vật
        results = [
            {
                "id": i + 1,
                "name": f"{animals[i % 3]}_{str(i + 1).zfill(3)}",
                "type": ["Chó", "Mèo", "Thỏ"][i % 3],
                "match_score": round(0.95 - (i * 0.01), 2)  # Độ khớp từ 0.95 xuống
            }
            for i in range(14)
        ]
        message = f"Tìm thấy {len(results)} con vật phù hợp"
    
    else:  # category == 'product'
        # TẠO MOCK RESULTS CHO SẢN PHẨM
        products = ['shoe', 'bag', 'chair']  # Danh sách tên sản phẩm
        results = [
            {
                "id": 100 + i + 1,
                "name": f"{products[i % 3]}_{str(i + 1).zfill(3)}",
                "type": ["Giày", "Túi xách", "Ghế"][i % 3],
                "match_score": round(0.92 - (i * 0.01), 2)  # Độ khớp từ 0.92 xuống
            }
            for i in range(14)
        ]
        message = f"Tìm thấy {len(results)} sản phẩm phù hợp"
    
    # ===== TRẢ VỀ KẾT QUẢ =====
    return {
        "category": request.category,
        "results": results,
        "total_count": len(results),
        "message": message
    }

# ==================== HEALTH CHECK ====================

@app.get("/health")
def health_check():
    """
    ENDPOINT KIỂM TRA TRẠNG THÁI SERVER
    - Method: GET
    - URL: http://localhost:8000/health
    - Dùng để kiểm tra xem server có đang chạy không
    
    Response:
    {
        "status": "🟢 Backend is running"
    }
    """
    return {"status": "🟢 Backend is running"}
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"Saved upload to: {filepath}")

    result = model.predict(filepath, top_k=5)
    return result
# ==================== CHẠY SERVER ====================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Khởi động Draw & Find Backend...")
    print("📍 Server chạy tại: http://localhost:8000")
    print("📚 API Docs (Swagger UI) tại: http://localhost:8000/docs")
    print("📖 Alternative Docs (ReDoc) tại: http://localhost:8000/redoc")
    print("=" * 60)
    
    # Chạy server trên localhost:8000 với tự động reload (phát hiện thay đổi code)
    uvicorn.run(app, host="0.0.0.0", port=8000)
