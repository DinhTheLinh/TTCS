import { useEffect, useRef } from 'react';
import '../styles/CanvasAnimal.css';

export default function CanvasAnimal({
  canvasRef,
  brushSize,
  color,
  mode,
  onStartDrawing,
  onDraw,
  onStopDrawing,
}) {
  const wrapperRef = useRef(null);

  // Vẽ hình động vật mờ ở nền canvas khi khởi tạo
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Vẽ canvas trắng trước
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Vẽ các hình động vật mờ ở nền
    ctx.globalAlpha = 0.08;
    ctx.fillStyle = '#4CAF50';
    
    ctx.beginPath();
    ctx.arc(80, 100, 40, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.beginPath();
    ctx.arc(300, 150, 50, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.beginPath();
    ctx.arc(150, 300, 35, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.beginPath();
    ctx.ellipse(280, 280, 60, 40, 0.3, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.beginPath();
    ctx.ellipse(100, 250, 50, 35, -0.2, 0, Math.PI * 2);
    ctx.fill();
    
    // Vẽ grid nhệp nhạn
    ctx.strokeStyle = 'rgba(76, 175, 80, 0.05)';
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
    <div className="canvas-wrapper canvas-animal" ref={wrapperRef}>
      <div className="canvas-mode-label">
        <span className="mode-icon">🐾</span>
        <span className="mode-text">Animal Mode</span>
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
