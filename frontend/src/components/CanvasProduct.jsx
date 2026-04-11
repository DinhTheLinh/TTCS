import { useEffect, useRef } from 'react';
import '../styles/CanvasProduct.css';

export default function CanvasProduct({
  canvasRef,
  brushSize,
  color,
  mode,
  onStartDrawing,
  onDraw,
  onStopDrawing,
}) {
  const wrapperRef = useRef(null);

  // Vẽ lưới, thước kẻ, và các hình khối cơ bản ở nền
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Canvas trắng
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Vẽ lưới grid chính (50px)
    ctx.strokeStyle = '#E8E8E8';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 400; i += 50) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, 400);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(400, i);
      ctx.stroke();
    }
    
    // Vẽ lưới grid phụ (10px) nhẹ hơn
    ctx.strokeStyle = '#F5F5F5';
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 400; i += 10) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, 400);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(400, i);
      ctx.stroke();
    }
    
    // Vẽ các hình khối mô phỏng sản phẩm (mờ nhạt)
    ctx.globalAlpha = 0.05;
    
    // Hình vuông
    ctx.fillStyle = '#FF9800';
    ctx.fillRect(50, 50, 80, 80);
    
    // Hình tròn
    ctx.fillStyle = '#2196F3';
    ctx.beginPath();
    ctx.arc(300, 100, 50, 0, Math.PI * 2);
    ctx.fill();
    
    // Hình chữ nhật
    ctx.fillStyle = '#E91E63';
    ctx.fillRect(80, 250, 120, 60);
    
    // Hình tam giác
    ctx.fillStyle = '#4CAF50';
    ctx.beginPath();
    ctx.moveTo(300, 200);
    ctx.lineTo(350, 280);
    ctx.lineTo(250, 280);
    ctx.closePath();
    ctx.fill();
    
    // Vẽ thước kẻ ở cạnh trái
    ctx.strokeStyle = '#CCCCCC';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(0, 400);
    ctx.stroke();
    
    // Vẽ tick marks thước dọc
    ctx.fillStyle = '#999999';
    ctx.font = '10px Arial';
    for (let i = 0; i <= 400; i += 50) {
      ctx.beginPath();
      ctx.moveTo(-5, i);
      ctx.lineTo(0, i);
      ctx.stroke();
      if (i > 0) {
        ctx.fillText(i, -28, i + 3);
      }
    }
    
    // Vẽ thước kẻ ở cạnh trên
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(400, 0);
    ctx.stroke();
    
    // Vẽ tick marks thước ngang
    for (let i = 0; i <= 400; i += 50) {
      ctx.beginPath();
      ctx.moveTo(i, -5);
      ctx.lineTo(i, 0);
      ctx.stroke();
      if (i > 0) {
        ctx.fillText(i, i - 8, -8);
      }
    }
    
    // ✅ RESET LẠI TẤT CẢ CONTEXT PROPERTIES CHO VẼ CHÍNH
    ctx.globalAlpha = 1;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#000000';
    ctx.fillStyle = 'white';
    ctx.globalCompositeOperation = 'source-over';
    
  }, [canvasRef]);

  return (
    <div className="canvas-wrapper canvas-product" ref={wrapperRef}>
      <div className="canvas-mode-label">
        <span className="mode-icon">📦</span>
        <span className="mode-text">Product Mode</span>
      </div>
      <canvas
        ref={canvasRef}
        width={400}
        height={400}
        onMouseDown={onStartDrawing}
        onMouseMove={onDraw}
        onMouseUp={onStopDrawing}
        onMouseLeave={onStopDrawing}
        onTouchStart={onStartDrawing}
        onTouchMove={onDraw}
        onTouchEnd={onStopDrawing}
        onTouchCancel={onStopDrawing}
        className="drawing-canvas"
      />
    </div>
  );
}
