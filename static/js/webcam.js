// Webcam handling for WasteWorks application

class WebcamCapture {
    constructor(videoElement, canvasElement, startButton, captureButton, closeButton) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.startButton = startButton;
        this.captureButton = captureButton;
        this.closeButton = closeButton;
        this.stream = null;
        this.capturedImage = null;
        
        // Bind methods to this instance
        this.start = this.start.bind(this);
        this.capture = this.capture.bind(this);
        this.stop = this.stop.bind(this);
        
        // Set up event listeners
        if (this.startButton) {
            this.startButton.addEventListener('click', this.start);
        }
        if (this.captureButton) {
            this.captureButton.addEventListener('click', this.capture);
        }
        if (this.closeButton) {
            this.closeButton.addEventListener('click', this.stop);
        }
    }
    
    async start() {
        try {
            // Request access to the webcam
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment', // Prefer back camera on mobile
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });
            
            // Connect the stream to the video element
            this.video.srcObject = this.stream;
            this.video.play();
            
            // Show the webcam container
            const webcamContainer = document.getElementById('webcam-container');
            if (webcamContainer) {
                webcamContainer.classList.remove('d-none');
            }
            
            // Hide the start button, show capture and close buttons
            if (this.startButton) this.startButton.classList.add('d-none');
            if (this.captureButton) this.captureButton.classList.remove('d-none');
            if (this.closeButton) this.closeButton.classList.remove('d-none');
            
        } catch (error) {
            console.error('Error accessing webcam:', error);
            alert('Could not access your camera. Please make sure you have a camera connected and have granted permission to use it.');
        }
    }
    
   capture() {
    if (!this.stream) return;

    const context = this.canvas.getContext('2d');

    // Set fixed canvas dimensions (you can change as needed)
    const maxWidth = 640;
    const maxHeight = 480;
    this.canvas.width = maxWidth;
    this.canvas.height = maxHeight;

    // Get video frame dimensions
    const videoWidth = this.video.videoWidth;
    const videoHeight = this.video.videoHeight;

    // Calculate scaling to fit image in canvas while maintaining aspect ratio
    const scale = Math.min(maxWidth / videoWidth, maxHeight / videoHeight);
    const scaledWidth = videoWidth * scale;
    const scaledHeight = videoHeight * scale;

    // Center the image in the canvas
    const x = (maxWidth - scaledWidth) / 2;
    const y = (maxHeight - scaledHeight) / 2;

    // Draw scaled and centered image
    context.clearRect(0, 0, maxWidth, maxHeight);
    context.drawImage(this.video, x, y, scaledWidth, scaledHeight);

    // Get image data
    this.capturedImage = this.canvas.toDataURL('image/jpeg');

    // Display preview
    const previewContainer = document.getElementById('image-preview-container');
    const previewImage = document.getElementById('preview-image');

    if (previewImage && previewContainer) {
        previewImage.src = this.capturedImage;
        previewContainer.classList.remove('d-none');
    }

    const imageDataInput = document.getElementById('webcam-image-data');
    if (imageDataInput) {
        imageDataInput.value = this.capturedImage;
    }

    this.stop();

    // Show alert
    const captureAlert = document.createElement('div');
    captureAlert.className = 'alert alert-success mt-2';
    captureAlert.innerHTML = '<i class="fas fa-check-circle me-2"></i>Image captured successfully. You can now analyze it or retake.';

    const alertContainer = document.getElementById('webcam-alerts');
    if (alertContainer) {
        alertContainer.innerHTML = '';
        alertContainer.appendChild(captureAlert);
        setTimeout(() => {
            captureAlert.remove();
        }, 3000);
    }
}

    stop() {
        if (this.stream) {
            // Stop all tracks in the stream
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            
            // Reset video source
            this.video.srcObject = null;
            
            // Hide the webcam container
            const webcamContainer = document.getElementById('webcam-container');
            if (webcamContainer) {
                webcamContainer.classList.add('d-none');
            }
            
            // Show the start button, hide capture and close buttons
            if (this.startButton) this.startButton.classList.remove('d-none');
            if (this.captureButton) this.captureButton.classList.add('d-none');
            if (this.closeButton) this.closeButton.classList.add('d-none');
        }
    }
    
    getImageData() {
        return this.capturedImage;
    }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    const videoElement = document.getElementById('webcam-video');
    const canvasElement = document.getElementById('webcam-canvas');
    const startButton = document.getElementById('start-webcam');
    const captureButton = document.getElementById('capture-image');
    const closeButton = document.getElementById('close-webcam');
    
    if (videoElement && canvasElement) {
        // Check if browser supports getUserMedia
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            // Create webcam instance
            window.webcamCapture = new WebcamCapture(
                videoElement,
                canvasElement,
                startButton,
                captureButton,
                closeButton
            );
            
            // Enable webcam button
            if (startButton) {
                startButton.disabled = false;
            }
        } else {
            console.error('getUserMedia is not supported in this browser');
            // Disable webcam button and show error message
            if (startButton) {
                startButton.disabled = true;
                startButton.title = 'Webcam not supported in this browser';
                
                const alertElement = document.createElement('div');
                alertElement.className = 'alert alert-warning mt-2';
                alertElement.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Webcam is not supported in your browser. Please use a modern browser or upload an image.';
                
                const alertContainer = document.getElementById('webcam-alerts');
                if (alertContainer) {
                    alertContainer.appendChild(alertElement);
                }
            }
        }
    }
});