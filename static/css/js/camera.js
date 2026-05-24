// Camera functionality for face recognition
class FaceCamera {
    constructor(videoElement, canvasElement, overlayElement) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.overlay = overlayElement;
        this.ctx = canvas.getContext('2d');
        this.stream = null;
        this.recognitionInterval = null;
        this.faces = [];
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480 } 
            });
            this.video.srcObject = this.stream;
            
            return new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    this.canvas.width = this.video.videoWidth;
                    this.canvas.height = this.video.videoHeight;
                    resolve();
                };
            });
        } catch (err) {
            console.error('Error accessing camera:', err);
            throw err;
        }
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.recognitionInterval) {
            clearInterval(this.recognitionInterval);
            this.recognitionInterval = null;
        }
    }

    capture() {
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        return this.canvas.toDataURL('image/jpeg');
    }

    startRecognition(onFaceDetected) {
        this.recognitionInterval = setInterval(async () => {
            if (this.video.readyState !== this.video.HAVE_ENOUGH_DATA) return;
            
            // Capture current frame
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Send to server for face recognition
            try {
                const formData = new FormData();
                const blob = await new Promise(resolve => this.canvas.toBlob(resolve, 'image/jpeg'));
                formData.append('image', blob);
                
                const response = await fetch('/recognize_faces', {
                    method: 'POST',
                    body: formData
                });
                
                const faces = await response.json();
                this.faces = faces;
                
                // Update overlay with recognized faces
                this.updateOverlay();
                
                if (onFaceDetected && faces.length > 0) {
                    onFaceDetected(faces);
                }
            } catch (err) {
                console.error('Face recognition error:', err);
            }
        }, 1000); // Process every second
    }

    updateOverlay() {
        // Clear previous overlay
        this.overlay.innerHTML = '';
        
        // Add new face markers
        this.faces.forEach(face => {
            const rect = document.createElement('div');
            rect.className = 'face-overlay';
            rect.style.left = `${face.x}px`;
            rect.style.top = `${face.y}px`;
            rect.style.width = `${face.width}px`;
            rect.style.height = `${face.height}px`;
            
            const name = document.createElement('div');
            name.className = 'face-name';
            name.textContent = face.name;
            name.style.left = `${face.x}px`;
            name.style.top = `${face.y - 30}px`;
            
            this.overlay.appendChild(rect);
            this.overlay.appendChild(name);
        });
    }
}

// Initialize camera when page loads
document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const overlay = document.getElementById('overlay');
    
    if (video && canvas) {
        window.faceCamera = new FaceCamera(video, canvas, overlay);
        
        // Start camera on button click
        const startBtn = document.getElementById('start-camera');
        if (startBtn) {
            startBtn.addEventListener('click', async () => {
                try {
                    await window.faceCamera.start();
                    startBtn.style.display = 'none';
                    
                    // Start face recognition
                    window.faceCamera.startRecognition((faces) => {
                        console.log('Faces detected:', faces);
                    });
                } catch (err) {
                    alert('Error accessing camera: ' + err.message);
                }
            });
        }
    }
});