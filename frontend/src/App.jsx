// file App.jsx: giao diện chính và logic vẽ canvas + Xác thực

import { useRef, useState, useEffect } from 'react'; 
import './App.css';
import { Trash2, ArrowLeft, Rocket, Eraser, Pen, LogOut } from 'lucide-react';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import CanvasAnimal from './components/CanvasAnimal';
import CanvasProduct from './components/CanvasProduct';

function App() {
  // tham chiếu tới phần tử <canvas>
  const canvasRef = useRef(null);
  
  // 🔐 Trạng thái xác thực
  const [authStatus, setAuthStatus] = useState('authenticated'); // 'login' | 'register' | 'authenticated'
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  
  const [isStarted, setIsStarted] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  // danh sách kết quả trả về (mock)
  const [results, setResults] = useState([]); 
  // 🔍 Trạng thái cho lựa chọn danh mục tìm kiếm
  const [searchCategory, setSearchCategory] = useState(null); // null | 'animal' | 'product'

  // trạng thái điều khiển thanh công cụ
  const [color, setColor] = useState('#000000');
  const [brushSize, setBrushSize] = useState(2);
  const [mode, setMode] = useState('brush'); 
  const [history, setHistory] = useState([]);

  // 🔐 Kiểm tra localStorage khi render để xác thực hiện tại
  useEffect(() => {
    setCurrentUser("demo_user");
    setAuthStatus("authenticated");
  }, []);

  // 🔐 Xử lý đăng nhập thành công
  const handleLoginSuccess = () => {
    const username = localStorage.getItem('username');
    setCurrentUser(username);
    setAuthStatus('authenticated');
  };

  // 🔐 Xử lý đăng ký thành công
  const handleRegisterSuccess = () => {
    const username = localStorage.getItem('username');
    setCurrentUser(username);
    setAuthStatus('authenticated');
  };

  // 🔐 Xử lý đăng xuất
  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    localStorage.removeItem('isAuthenticated');
    setCurrentUser(null);
    setAuthStatus('login');
    setIsStarted(false); // Đặt lại màn hình vẽ
    setSearchCategory(null); // Đặt lại lựa chọn danh mục tìm kiếm
    setResults([]); // Xóa kết quả tìm kiếm
    clearCanvas();
  };

  // 🔐 Chuyển đổi giữa các biểu mẫu đăng nhập và đăng ký
  const switchToRegister = () => {
    setAuthStatus('register');
  };

  const switchToLogin = () => {
    setAuthStatus('login');
  };

 
  useEffect(() => {
    if (!isStarted || !canvasRef.current) return; 
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.lineCap = 'round';          // đầu nét tròn
    ctx.lineJoin = 'round';         // góc nối tròn
    ctx.lineWidth = brushSize;      // độ dày mặc định
    ctx.strokeStyle = color;
    ctx.globalCompositeOperation = 'source-over'; 

    // lưu trạng thái canvas ban đầu (trắng) vào history
    setHistory([canvas.toDataURL()]);
  }, [isStarted]);

 
  useEffect(() => {
    if (!canvasRef.current) return; // bỏ qua nếu canvas chưa render
    const ctx = canvasRef.current.getContext('2d'); 
    ctx.lineWidth = brushSize; 
    if (mode === 'eraser') {
   
      ctx.globalCompositeOperation = 'destination-out'; 
      ctx.strokeStyle = 'rgba(0,0,0,1)'; 
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = color;
    }
  }, [color, brushSize, mode]);

  // lấy toạ độ chuột hoặc chạm so với canvas
  const getCoords = (e) => {
    const rect = canvasRef.current.getBoundingClientRect(); 
    let clientX, clientY;
    if (e.touches && e.touches.length) { 
      // hỗ trợ touch event
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  };
  
  // lưu trạng thái hiện tại của canvas để undo sau này
  const pushHistory = () => {
    const canvas = canvasRef.current;
    setHistory((h) => [...h, canvas.toDataURL()]); 
  };

  // xử lý bắt đầu vẽ (mousedown hoặc touchstart)
  const startDrawing = (e) => {
    e.preventDefault(); // ngăn cuộn trang khi touch trên mobile
    const { x, y } = getCoords(e); 
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.beginPath(); // bắt đầu một đường mới
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  // xử lý vẽ khi di chuyển chuột/touch
  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault(); 
    const { x, y } = getCoords(e);
    const ctx = canvasRef.current.getContext('2d');
    ctx.lineTo(x, y); 
    ctx.stroke(); 
  };

 
  const stopDrawing = () => {
    if (isDrawing) {
      pushHistory();
    }
    setIsDrawing(false);
  };

  // Xóa trắng toàn bộ canvas và đặt lại lịch sử
  const clearCanvas = () => {
    const canvas = canvasRef.current;  
    const ctx = canvas.getContext('2d'); 
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // đặt lại lịch sử
    setHistory([canvas.toDataURL()]);
  };

  // Xử lý tìm kiếm - gửi sketch + danh mục tới backend
  const handleSearch = async () => {
    if (isLoading || !searchCategory) return;

    setIsLoading(true);
    setResults([]);

    try {
      const canvas = canvasRef.current;

      const blob = await new Promise((resolve) => {
        canvas.toBlob((b) => resolve(b), 'image/png');
      });

      if (!blob) {
        throw new Error('Không tạo được ảnh từ canvas');
      }

      const formData = new FormData();
      formData.append('file', blob, 'sketch.png');

      const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();

      const items = data.results.map((result, i) => ({
        image: result.image_url,
        name: result.class_name || `result_${i + 1}`,
        type: result.class_name,
        match_score: result.score,
      }));

      setResults(items);
      console.log('✅ Predict thành công:', data);
      console.log("Items:", items);
    } catch (error) {
      console.error('❌ Lỗi tìm kiếm:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Quay lại trạng thái trước đó trong lịch sử
  const undo = () => {
    if (history.length <= 1) return; 
    const newHist = [...history]; 
    newHist.pop();
    const previous = newHist[newHist.length - 1];
    const canvas = canvasRef.current; 
    const ctx = canvas.getContext('2d');
    
    // Xóa canvas trước
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Vẽ lại từ ảnh lưu trong lịch sử
    if (previous) { 
      const img = new Image(); 
      img.onload = () => { 
        ctx.drawImage(img, 0, 0); 
      };
      img.src = previous;
    }
    
    setHistory(newHist);
  };

  // Nút gửi thực chất gọi handleSearch hiện tại
  const handleSend = () => {
    handleSearch();
  };

  return (
    <div className="app-container">
      {/* 🔐 Hiển thị biểu mẫu đăng nhập nếu không xác thực */}
      {authStatus === 'login' && (
        <LoginForm
          onLoginSuccess={handleLoginSuccess}
          onSwitchToRegister={switchToRegister}
          onLoading={setIsAuthLoading}
        />
      )}

      {/* 🔐 Hiển thị biểu mẫu đăng ký nếu người dùng chuyển đổi */}
      {authStatus === 'register' && (
        <RegisterForm
          onRegisterSuccess={handleRegisterSuccess}
          onSwitchToLogin={switchToLogin}
          onLoading={setIsAuthLoading}
        />
      )}

      {/* Ứng dụng chính - chỉ hiển thị khi xác thực */}
      {authStatus === 'authenticated' && (
        <>
          {!isStarted ? (
            // Màn hình chào
            <div className="welcome-screen">
              <div className="welcome-header">
                <h1 className="welcome-title-small">Draw & Find</h1>
                <button className="logout-btn" onClick={handleLogout} title="Đăng xuất">
                  <LogOut size={18} />
                </button>
              </div>
              <div className="welcome-logo">
                <span className="paper"></span>
                <span className="pencil"></span>
              </div>
              <p className="welcome-message">Xin chào, <strong>{currentUser}</strong>!</p> 
              <p className="welcome-subtitle">Sketch your idea, we find the match.</p>
              
              {/* 🔍 Lựa chọn danh mục tìm kiếm */}
              <div className="search-category-container">
                <button
                  className={`search-category-option ${searchCategory === 'animal' ? 'selected' : ''}`}
                  onClick={() => setSearchCategory('animal')}
                  title="Tìm kiếm con vật"
                >
                  <span className="category-icon">🐾</span>
                  <span className="category-text">Con vật</span>
                </button>
                <button
                  className={`search-category-option ${searchCategory === 'product' ? 'selected' : ''}`}
                  onClick={() => setSearchCategory('product')}
                  title="Tìm kiếm sản phẩm"
                >
                  <span className="category-icon">📦</span>
                  <span className="category-text">Sản phẩm</span>
                </button>
              </div>
              
              <button 
                className="start-btn" 
                disabled={searchCategory === null}
                onClick={() => setIsStarted(true)}
              >
                Bắt đầu vẽ
              </button>
            </div>
          ) : (
            // Màn hình vẽ
            <>
              <div className="app-header">
                <h1>🎨 Phác họa tìm kiếm</h1>
                <button className="logout-btn" onClick={handleLogout} title="Đăng xuất">
                  <LogOut size={18} />
                </button>
              </div>

              {/* Thanh công cụ: chứa các điều khiển vẽ, nút hoàn tác, xóa, gửi tìm kiếm */}
              <div className="toolbar">
                <label>
                  Màu:
                  <input
                    type="color"
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                  />
                </label>
                <button
                  className={mode === 'brush' ? 'active' : ''} 
                  onClick={() => setMode('brush')}
                >
                  <Pen size={16}  />
                  Bút
                </button>
                <button
                  className={mode === 'eraser' ? 'active' : ''}
                  onClick={() => setMode('eraser')}
                >
                  <Eraser size={16} />
                  Tẩy
                </button>
                <label>
                  Size:
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={brushSize}
                    onChange={(e) => setBrushSize(parseInt(e.target.value, 10))}
                  />
                </label>
                <button onClick={undo} title="Undo">
                  <ArrowLeft size={16} />
                </button>
                <button className="clear-all" onClick={clearCanvas}>
                  <Trash2 size={16} /> Xóa hết
                </button>
                <button className="send-btn" onClick={handleSend} disabled={isLoading}>
                  {isLoading ? <div className="spinner"></div> : <Rocket size={16} />} {isLoading ? 'Đang tìm...' : 'Gửi tìm kiếm'}
                </button>
              </div>

              {/* Phần canvas - Render khác nhau theo chế độ */}
              {searchCategory === 'animal' && (
                <CanvasAnimal
                  canvasRef={canvasRef}
                  brushSize={brushSize}
                  color={color}
                  mode={mode}
                  onStartDrawing={startDrawing}
                  onDraw={draw}
                  onStopDrawing={stopDrawing}
                />
              )}
              {searchCategory === 'product' && (
                <CanvasProduct
                  canvasRef={canvasRef}
                  brushSize={brushSize}
                  color={color}
                  mode={mode}
                  onStartDrawing={startDrawing}
                  onDraw={draw}
                  onStopDrawing={stopDrawing}
                />
              )}

              {/* Lưới kết quả */}
              {results.length > 0 && (
                <div className="results-grid">
                  {results.map((r, idx) => ( 
                    <div className="result-card" key={idx}>
                      <img
                        src={r.image}
                        alt={r.name}
                        style={{ width: '220px', height: '220px', objectFit: 'contain', border: '1px solid #ccc' }}
                      />
                      <div className="result-name">{r.name}</div>
                      <a href="#" className="details-link">
                        Xem chi tiết
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

export default App;
