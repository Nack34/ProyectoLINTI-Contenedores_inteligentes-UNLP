const video = document.getElementById('webcam');
const canvas = document.getElementById('overlay');
const ctx = canvas.getContext('2d');
const btn = document.getElementById("btn");
const resultEl = document.getElementById("result");
const loading = document.getElementById("loading");
const qrContainer = document.querySelector(".qr");

// Hidden canvas to capture frames for the server
const captureCanvas = document.createElement('canvas');
captureCanvas.width = 640;
captureCanvas.height = 480;
const captureCtx = captureCanvas.getContext('2d');

let isLoopRunning = false;
let qrLoaded = false; 
let qrTimer = null;

async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 }, 
                height: { ideal: 480 } 
            } 
        });
        video.srcObject = stream;
        video.onloadedmetadata = () => {
            btn.disabled = false; 
        };
    } catch (err) {
        console.error("Error accessing webcam:", err);
        alert("No se pudo acceder a la cámara. Por favor verifica los permisos.");
    }
}

const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

function startDetectionLoop() {
    if (isLoopRunning) return;
    isLoopRunning = true;
    requestAnimationFrame(sendFrameToServer);
}

async function sendFrameToServer() {
    if (!isLoopRunning) return;

    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
        requestAnimationFrame(sendFrameToServer);
        return;
    }

    captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
    const imageData = captureCanvas.toDataURL('image/jpeg', 0.6); 

    try {
        const response = await fetch('/process_frame/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ image: imageData })
        });

        if (response.ok) {
            const data = await response.json();
            
            if (isLoopRunning) {
                drawDetections(data.detections);
                handleServerState(data);
            }
        }
    } catch (error) {
        console.error("Error processing frame:", error);
    } finally {
        if (isLoopRunning) {
            setTimeout(() => {
                requestAnimationFrame(sendFrameToServer);
            }, 50); 
        }
    }
}

function drawDetections(detections) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!detections || detections.length === 0) return;

    detections.forEach(det => {
        const [x, y, w, h] = det.bbox;
        const color = `rgb(${det.color[2]}, ${det.color[1]}, ${det.color[0]})`; 

        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, w, h);

        ctx.fillStyle = color;
        const text = det.label;
        const textMetrics = ctx.measureText(text);
        const textHeight = 16; 
        ctx.fillRect(x, y - textHeight - 5, textMetrics.width + 10, textHeight + 5);

        ctx.fillStyle = '#FFFFFF';
        ctx.font = '20px Arial';
        ctx.fillText(text, x + 5, y - 5);
    });
}

function handleServerState(data) {
    if (data.final_result) {
        isLoopRunning = false;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        resultEl.innerText = data.final_result;
        resultEl.style.display = "block";
        loading.style.display = "none";
        
        btn.disabled = false;
        
        if (data.qr_ready && !qrLoaded) {
            qrLoaded = true;
            loadQr();
        }
    }
}

function startClassification() {
    // UI Cleanup for new run
    btn.disabled = true;
    resultEl.style.display = "none";
    loading.style.display = "block";
    qrContainer.style.display = "none"; 
    qrLoaded = false; 

    if (qrTimer) {
        clearTimeout(qrTimer);
        qrTimer = null;
    }

    fetch(`/start_analyzing/`)
        .then(response => {
            if (response.ok) {
                startDetectionLoop();
            }
        })
        .catch(err => {
            console.error("Error starting analysis:", err);
            btn.disabled = false; 
        });
}

async function loadQr() {
    try {
        const response = await fetch("/qr/");
        if (!response.ok) throw new Error("QR Fetch failed");

        const blob = await response.blob();
        const imgUrl = URL.createObjectURL(blob);

        qrContainer.querySelector("#qr").src = imgUrl;
        qrContainer.style.display = "block";
        
        qrTimer = setTimeout(() => {
            qrContainer.style.display = "none";
            resultEl.style.display = "none";
            URL.revokeObjectURL(imgUrl);
            qrTimer = null;
        }, 10000);

    } catch (e) {
        console.error("Could not load QR", e);
    } 
}

initCamera();