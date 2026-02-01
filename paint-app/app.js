// ペイントアプリ メインスクリプト

class PaintApp {
    constructor() {
        // キャンバス
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');

        // 状態
        this.isDrawing = false;
        this.currentTool = 'pen';
        this.brushSize = 5;
        this.brushShape = 'round';
        this.currentColor = '#000000';
        this.startX = 0;
        this.startY = 0;

        // 履歴管理
        this.history = [];
        this.historyIndex = -1;
        this.maxHistory = 50;

        // 一時キャンバス（図形描画用）
        this.tempCanvas = document.createElement('canvas');
        this.tempCtx = this.tempCanvas.getContext('2d');

        // カラーパレット
        this.colors = [
            '#000000', '#ffffff', '#ff0000', '#ff6b6b', '#ffa500',
            '#ffff00', '#90ee90', '#00ff00', '#00ced1', '#00bfff',
            '#0000ff', '#8a2be2', '#ff1493', '#ff69b4', '#a0522d',
            '#808080', '#c0c0c0', '#ffd700', '#f0e68c', '#dda0dd'
        ];

        this.init();
    }

    init() {
        this.setupCanvas();
        this.setupColorPalette();
        this.setupEventListeners();
        this.saveState();
        this.updateUndoRedoButtons();
    }

    // キャンバスのセットアップ
    setupCanvas() {
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const container = document.querySelector('.canvas-area');
        const padding = 40;
        const width = container.clientWidth - padding;
        const height = container.clientHeight - padding;

        // 現在の画像を保存
        const imageData = this.canvas.width > 0 ?
            this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height) : null;

        this.canvas.width = width;
        this.canvas.height = height;
        this.tempCanvas.width = width;
        this.tempCanvas.height = height;

        // 背景を白で塗りつぶし
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(0, 0, width, height);

        // 画像を復元
        if (imageData) {
            this.ctx.putImageData(imageData, 0, 0);
        }
    }

    // カラーパレットのセットアップ
    setupColorPalette() {
        const palette = document.getElementById('color-palette');
        const currentColorDisplay = document.getElementById('current-color');

        this.colors.forEach((color, index) => {
            const swatch = document.createElement('div');
            swatch.className = 'color-swatch' + (index === 0 ? ' active' : '');
            swatch.style.backgroundColor = color;
            swatch.dataset.color = color;
            swatch.addEventListener('click', () => this.selectColor(color, swatch));
            palette.appendChild(swatch);
        });

        currentColorDisplay.style.backgroundColor = this.currentColor;
    }

    selectColor(color, swatch) {
        this.currentColor = color;
        document.getElementById('current-color').style.backgroundColor = color;

        document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
        swatch.classList.add('active');
    }

    // イベントリスナーのセットアップ
    setupEventListeners() {
        // キャンバスイベント
        this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
        this.canvas.addEventListener('mousemove', (e) => this.draw(e));
        this.canvas.addEventListener('mouseup', () => this.stopDrawing());
        this.canvas.addEventListener('mouseleave', () => this.stopDrawing());

        // タッチイベント
        this.canvas.addEventListener('touchstart', (e) => this.handleTouch(e, 'start'));
        this.canvas.addEventListener('touchmove', (e) => this.handleTouch(e, 'move'));
        this.canvas.addEventListener('touchend', () => this.stopDrawing());

        // ツール選択
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => this.selectTool(btn.dataset.tool, btn));
        });

        // ブラシサイズ
        const brushSizeSlider = document.getElementById('brush-size');
        brushSizeSlider.addEventListener('input', (e) => {
            this.brushSize = parseInt(e.target.value);
            document.getElementById('brush-size-value').textContent = this.brushSize;
        });

        // ブラシ形状
        document.querySelectorAll('.shape-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.shape-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.brushShape = btn.dataset.shape;
            });
        });

        // ファイル操作
        document.getElementById('btn-new').addEventListener('click', () => this.newCanvas());
        document.getElementById('btn-save').addEventListener('click', () => this.saveProject());
        document.getElementById('btn-load').addEventListener('click', () => this.loadProject());
        document.getElementById('btn-export').addEventListener('click', () => this.exportImage());
        document.getElementById('file-input').addEventListener('change', (e) => this.handleFileLoad(e));

        // Undo/Redo
        document.getElementById('btn-undo').addEventListener('click', () => this.undo());
        document.getElementById('btn-redo').addEventListener('click', () => this.redo());

        // キーボードショートカット
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    handleTouch(e, type) {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const mouseEvent = {
            offsetX: touch.clientX - rect.left,
            offsetY: touch.clientY - rect.top
        };

        if (type === 'start') {
            this.startDrawing(mouseEvent);
        } else {
            this.draw(mouseEvent);
        }
    }

    selectTool(tool, btn) {
        this.currentTool = tool;
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }

    // 描画開始
    startDrawing(e) {
        this.isDrawing = true;
        this.startX = e.offsetX;
        this.startY = e.offsetY;

        if (this.currentTool === 'pen' || this.currentTool === 'eraser') {
            this.ctx.beginPath();
            this.ctx.moveTo(this.startX, this.startY);
        } else if (this.currentTool === 'fill') {
            this.floodFill(Math.floor(this.startX), Math.floor(this.startY));
            this.saveState();
        }
    }

    // 描画中
    draw(e) {
        if (!this.isDrawing) return;

        const x = e.offsetX;
        const y = e.offsetY;

        switch (this.currentTool) {
            case 'pen':
                this.drawPen(x, y);
                break;
            case 'eraser':
                this.drawEraser(x, y);
                break;
            case 'line':
            case 'rect':
            case 'circle':
                this.drawShapePreview(x, y);
                break;
        }
    }

    // 描画終了
    stopDrawing() {
        if (!this.isDrawing) return;

        if (this.currentTool === 'line' || this.currentTool === 'rect' || this.currentTool === 'circle') {
            // 一時キャンバスの内容を本キャンバスに合成
            this.ctx.drawImage(this.tempCanvas, 0, 0);
            this.tempCtx.clearRect(0, 0, this.tempCanvas.width, this.tempCanvas.height);
        }

        if (this.currentTool !== 'fill') {
            this.saveState();
        }

        this.isDrawing = false;
    }

    // ペン描画
    drawPen(x, y) {
        this.ctx.lineCap = this.brushShape === 'round' ? 'round' : 'square';
        this.ctx.lineJoin = this.brushShape === 'round' ? 'round' : 'miter';
        this.ctx.lineWidth = this.brushSize;
        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
    }

    // 消しゴム描画
    drawEraser(x, y) {
        this.ctx.lineCap = this.brushShape === 'round' ? 'round' : 'square';
        this.ctx.lineJoin = this.brushShape === 'round' ? 'round' : 'miter';
        this.ctx.lineWidth = this.brushSize;
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
    }

    // 図形プレビュー描画
    drawShapePreview(x, y) {
        // 一時キャンバスをクリアして現在のキャンバスをコピー
        this.tempCtx.clearRect(0, 0, this.tempCanvas.width, this.tempCanvas.height);
        this.tempCtx.drawImage(this.canvas, 0, 0);

        this.tempCtx.strokeStyle = this.currentColor;
        this.tempCtx.lineWidth = this.brushSize;
        this.tempCtx.lineCap = 'round';

        switch (this.currentTool) {
            case 'line':
                this.tempCtx.beginPath();
                this.tempCtx.moveTo(this.startX, this.startY);
                this.tempCtx.lineTo(x, y);
                this.tempCtx.stroke();
                break;
            case 'rect':
                this.tempCtx.strokeRect(this.startX, this.startY, x - this.startX, y - this.startY);
                break;
            case 'circle':
                const radiusX = Math.abs(x - this.startX) / 2;
                const radiusY = Math.abs(y - this.startY) / 2;
                const centerX = this.startX + (x - this.startX) / 2;
                const centerY = this.startY + (y - this.startY) / 2;
                this.tempCtx.beginPath();
                this.tempCtx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2);
                this.tempCtx.stroke();
                break;
        }

        // 一時キャンバスを表示
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.tempCanvas, 0, 0);
    }

    // 塗りつぶし（フラッドフィル）
    floodFill(startX, startY) {
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;
        const width = this.canvas.width;
        const height = this.canvas.height;

        // 開始位置の色を取得
        const startPos = (startY * width + startX) * 4;
        const startR = data[startPos];
        const startG = data[startPos + 1];
        const startB = data[startPos + 2];
        const startA = data[startPos + 3];

        // 塗りつぶす色をパース
        const fillColor = this.hexToRgb(this.currentColor);

        // 同じ色なら終了
        if (startR === fillColor.r && startG === fillColor.g && startB === fillColor.b) {
            return;
        }

        const stack = [[startX, startY]];
        const visited = new Set();

        while (stack.length > 0) {
            const [x, y] = stack.pop();
            const key = `${x},${y}`;

            if (x < 0 || x >= width || y < 0 || y >= height || visited.has(key)) {
                continue;
            }

            const pos = (y * width + x) * 4;

            // 色が一致するか確認（許容誤差あり）
            if (Math.abs(data[pos] - startR) > 10 ||
                Math.abs(data[pos + 1] - startG) > 10 ||
                Math.abs(data[pos + 2] - startB) > 10 ||
                Math.abs(data[pos + 3] - startA) > 10) {
                continue;
            }

            visited.add(key);

            // 色を塗る
            data[pos] = fillColor.r;
            data[pos + 1] = fillColor.g;
            data[pos + 2] = fillColor.b;
            data[pos + 3] = 255;

            // 隣接ピクセルをスタックに追加
            stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
        }

        this.ctx.putImageData(imageData, 0, 0);
    }

    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    // 履歴管理
    saveState() {
        // 現在位置より後の履歴を削除
        this.history = this.history.slice(0, this.historyIndex + 1);

        // 新しい状態を追加
        this.history.push(this.canvas.toDataURL());

        // 最大履歴数を超えたら古いものを削除
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        } else {
            this.historyIndex++;
        }

        this.updateUndoRedoButtons();
    }

    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.restoreState(this.history[this.historyIndex]);
            this.updateUndoRedoButtons();
        }
    }

    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.restoreState(this.history[this.historyIndex]);
            this.updateUndoRedoButtons();
        }
    }

    restoreState(dataUrl) {
        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.drawImage(img, 0, 0);
        };
        img.src = dataUrl;
    }

    updateUndoRedoButtons() {
        document.getElementById('btn-undo').disabled = this.historyIndex <= 0;
        document.getElementById('btn-redo').disabled = this.historyIndex >= this.history.length - 1;
    }

    // ファイル操作
    newCanvas() {
        if (confirm('現在の作業内容は失われます。新規作成しますか？')) {
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.history = [];
            this.historyIndex = -1;
            this.saveState();
        }
    }

    saveProject() {
        const data = {
            version: 1,
            width: this.canvas.width,
            height: this.canvas.height,
            image: this.canvas.toDataURL()
        };

        const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = 'artwork.paint';
        a.click();

        URL.revokeObjectURL(url);
    }

    loadProject() {
        document.getElementById('file-input').click();
    }

    handleFileLoad(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);

                if (data.version && data.image) {
                    const img = new Image();
                    img.onload = () => {
                        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                        this.ctx.drawImage(img, 0, 0);
                        this.history = [];
                        this.historyIndex = -1;
                        this.saveState();
                    };
                    img.src = data.image;
                } else {
                    alert('無効なファイル形式です。');
                }
            } catch (err) {
                alert('ファイルの読み込みに失敗しました。');
            }
        };
        reader.readAsText(file);

        // ファイル入力をリセット
        e.target.value = '';
    }

    exportImage() {
        const a = document.createElement('a');
        a.href = this.canvas.toDataURL('image/png');
        a.download = 'artwork.png';
        a.click();
    }

    // キーボードショートカット
    handleKeyboard(e) {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'z':
                    e.preventDefault();
                    if (e.shiftKey) {
                        this.redo();
                    } else {
                        this.undo();
                    }
                    break;
                case 'y':
                    e.preventDefault();
                    this.redo();
                    break;
                case 's':
                    e.preventDefault();
                    this.saveProject();
                    break;
            }
        }
    }
}

// アプリケーション起動
document.addEventListener('DOMContentLoaded', () => {
    new PaintApp();
});
