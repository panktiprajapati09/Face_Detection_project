// Ultra-simple camera system - No classes, no complexity
console.log('🎥 SIMPLE CAMERA SYSTEM LOADED');

// Global variables
let cameraStream = null;
let currentLectureId = null;

// Wait for page to load
window.addEventListener('load', function() {
    console.log('📄 Page fully loaded');
    setupCameraSystem();
});

function setupCameraSystem() {
    console.log('⚙️ Setting up camera system...');
    
    // Get buttons
    const startBtn = document.getElementById('start-camera');
    const captureBtn = document.getElementById('capture-btn'); 
    const stopBtn = document.getElementById('stop-camera');
    const lectureSelect = document.getElementById('lecture_id');
    
    console.log('🔍 Found buttons:', {
        start: !!startBtn,
        capture: !!captureBtn,
        stop: !!stopBtn,
        lecture: !!lectureSelect
    });
    
    // Setup start button - SIMPLE CLICK HANDLER
    if (startBtn) {
        startBtn.onclick = function() {
            console.log('🎬 START button clicked!');
            startCamera();
        };
        startBtn.disabled = false;
        console.log('✅ Start button ready');
    }
    
    // Setup lecture selection
    if (lectureSelect) {
        lectureSelect.onchange = function() {
            currentLectureId = this.value;
            console.log('📚 Lecture selected:', currentLectureId);
            updateCaptureButton();
        };
    }
    
    // Setup stop button
    if (stopBtn) {
        stopBtn.onclick = function() {
            console.log('🛑 STOP button clicked!');
            stopCamera();
        };
    }
    
    // Setup capture button
    if (captureBtn) {
        captureBtn.onclick = function() {
            console.log('📸 CAPTURE button clicked!');
            captureAttendance();
        };
    }
    
    console.log('🎊 Camera system setup complete!');
}

// START CAMERA function
async function startCamera() {
    console.log('🚀 Starting camera...');
    
    try {
        const video = document.getElementById('video');
        const startBtn = document.getElementById('start-camera');
        const stopBtn = document.getElementById('stop-camera');
        const cameraPlaceholder = document.getElementById('camera-placeholder');
        const cameraPreview = document.getElementById('camera-preview');
        
        // Show loading
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.textContent = 'Starting...';
        }
        
        // Get camera access
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: 640,
                height: 480 
            } 
        });
        
        console.log('✅ Camera access granted');
        
        // Setup video
        if (video) {
            video.srcObject = cameraStream;
            
            video.onloadedmetadata = function() {
                console.log('📹 Video ready');
                
                // Setup canvas
                const canvas = document.getElementById('canvas');
                if (canvas) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                }
                
                // Update UI
                if (cameraPlaceholder) cameraPlaceholder.style.display = 'none';
                if (cameraPreview) cameraPreview.style.display = 'block';
                if (startBtn) startBtn.style.display = 'none';
                if (stopBtn) stopBtn.style.display = 'inline-flex';
                
                updateCaptureButton();
                
                console.log('🎉 Camera started successfully!');
            };
        }
        
    } catch (error) {
        console.error('❌ Camera error:', error);
        alert('Camera Error: ' + error.message);
        
        // Reset button
        const startBtn = document.getElementById('start-camera');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = 'Start Camera';
        }
    }
}

// STOP CAMERA function
function stopCamera() {
    console.log('🛑 Stopping camera...');
    
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    // Reset UI
    const cameraPlaceholder = document.getElementById('camera-placeholder');
    const cameraPreview = document.getElementById('camera-preview');
    const startBtn = document.getElementById('start-camera');
    const stopBtn = document.getElementById('stop-camera');
    const captureBtn = document.getElementById('capture-btn');
    const video = document.getElementById('video');
    
    if (cameraPlaceholder) cameraPlaceholder.style.display = 'block';
    if (cameraPreview) cameraPreview.style.display = 'none';
    if (startBtn) {
        startBtn.style.display = 'inline-flex';
        startBtn.disabled = false;
        startBtn.textContent = 'Start Camera';
    }
    if (stopBtn) stopBtn.style.display = 'none';
    if (captureBtn) captureBtn.style.display = 'none';
    if (video) video.srcObject = null;
    
    console.log('✅ Camera stopped');
}

// UPDATE CAPTURE BUTTON function
function updateCaptureButton() {
    const captureBtn = document.getElementById('capture-btn');
    
    if (captureBtn) {
        if (cameraStream && currentLectureId) {
            captureBtn.style.display = 'inline-flex';
            console.log('🟢 Capture button VISIBLE');
        } else {
            captureBtn.style.display = 'none';
            console.log('🔴 Capture button HIDDEN');
        }
    }
}

// CAPTURE ATTENDANCE function
async function captureAttendance() {
    console.log('📸 Capturing attendance...');
    
    if (!cameraStream) {
        alert('Please start camera first');
        return;
    }
    
    if (!currentLectureId) {
        alert('Please select lecture first');
        return;
    }
    
    const captureBtn = document.getElementById('capture-btn');
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    
    // Show loading
    if (captureBtn) {
        captureBtn.disabled = true;
        captureBtn.textContent = 'Processing...';
    }
    
    try {
        // Capture frame
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Convert to blob
        const blob = await new Promise(resolve => {
            canvas.toBlob(resolve, 'image/jpeg');
        });
        
        console.log('🔄 Sending to face recognition...');
        
        // Send for face recognition
        const formData = new FormData();
        formData.append('image', blob);
        
        const response = await fetch('/recognize_faces_api', {
            method: 'POST',
            body: formData
        });
        
        const faces = await response.json();
        console.log('👥 Faces found:', faces);
        
        // Mark attendance
        for (const face of faces) {
            if (face.id && face.name !== "Unknown") {
                try {
                    await fetch('/process_attendance', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            student_id: face.id,
                            lecture_id: currentLectureId
                        })
                    });
                } catch (error) {
                    console.error('Error marking attendance:', error);
                }
            }
        }
        
        alert(`✅ Attendance processed! Found ${faces.length} face(s)`);
        
    } catch (error) {
        console.error('❌ Capture error:', error);
        alert('Error: ' + error.message);
    } finally {
        // Reset button
        if (captureBtn) {
            captureBtn.disabled = false;
            captureBtn.textContent = 'Mark Attendance';
        }
    }
}

console.log('🎊 Simple camera system ready!');