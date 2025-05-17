// Script for waste management application

document.addEventListener('DOMContentLoaded', function() {
    // Toggle between upload and webcam options
    const optionUpload = document.getElementById('option-upload');
    const optionWebcam = document.getElementById('option-webcam');
    const uploadContainer = document.getElementById('upload-container');
    const webcamContainer = document.getElementById('webcam-option-container');

    if (optionUpload && optionWebcam) {
        optionUpload.addEventListener('change', function() {
            if (this.checked) {
                uploadContainer.classList.remove('d-none');
                webcamContainer.classList.add('d-none');
            }
        });

        optionWebcam.addEventListener('change', function() {
            if (this.checked) {
                uploadContainer.classList.add('d-none');
                webcamContainer.classList.remove('d-none');
            }
        });
    }

    // File upload preview
    const fileInput = document.getElementById('waste-image');
    const previewContainer = document.getElementById('image-preview-container');
    const previewImage = document.getElementById('preview-image');

    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const img = new Image();
                img.onload = function() {
                    const aspectRatio = this.width / this.height;
                    if (aspectRatio > 1) {
                        // Landscape image
                        previewImage.style.width = '100%';
                        previewImage.style.height = 'auto';
                    } else {
                        // Portrait image
                        previewImage.style.width = 'auto';
                        previewImage.style.height = '100%';
                    }
                };
                img.src = event.target.result;
                previewImage.src = event.target.result;
                previewContainer.style.display = 'flex';
                previewContainer.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        }
    });
    const uploadForm = document.getElementById('upload-form');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadSpinner = document.getElementById('upload-spinner');

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();

                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    previewContainer.classList.remove('d-none');
                }

                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Show spinner on form submit
    if (uploadForm) {
        uploadForm.addEventListener('submit', function() {
            uploadBtn.disabled = true;
            uploadSpinner.classList.remove('d-none');
        });
    }

    // Material icon selection based on material type
    const materialIcons = document.querySelectorAll('.material-icon');
    materialIcons.forEach(icon => {
        const material = icon.dataset.material.toLowerCase();
        let iconClass = 'fa-question';

        // Select appropriate icon based on material
        switch(material) {
            case 'plastic':
                iconClass = 'fa-wine-bottle';
                break;
            case 'paper':
                iconClass = 'fa-newspaper';
                break;
            case 'metal':
                iconClass = 'fa-cog';
                break;
            case 'glass':
                iconClass = 'fa-glass-martini';
                break;
            case 'electronic':
                iconClass = 'fa-laptop';
                break;
            case 'textile':
                iconClass = 'fa-tshirt';
                break;
            case 'organic':
                iconClass = 'fa-leaf';
                break;
            default:
                iconClass = 'fa-recycle';
        }

        // Add the selected icon class
        icon.classList.add('fas', iconClass);
    });

    // Copy analysis text
    const copyBtn = document.getElementById('copy-analysis');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            // Get text from all tabs to provide comprehensive analysis
            let fullContent = '';

            // Try to get content from each tab
            const summaryTab = document.getElementById('summary');
            const recyclingTab = document.getElementById('recycling');
            const impactTab = document.getElementById('impact');
            const fullTab = document.getElementById('full');

            if (fullTab && fullTab.querySelector('#analysis-text')) {
                // If full analysis is available, use that
                fullContent = fullTab.querySelector('#analysis-text').innerText;
            } else {
                // Otherwise compile from individual tabs
                if (summaryTab) {
                    fullContent += "SUMMARY:\n" + summaryTab.innerText + "\n\n";
                }
                if (recyclingTab) {
                    fullContent += "RECYCLING INSTRUCTIONS:\n" + recyclingTab.innerText + "\n\n";
                }
                if (impactTab) {
                    fullContent += "ENVIRONMENTAL IMPACT:\n" + impactTab.innerText + "\n\n";
                }
            }

            // Copy to clipboard
            navigator.clipboard.writeText(fullContent).then(() => {
                // Show success message
                this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    this.innerHTML = '<i class="fas fa-copy"></i> Copy analysis';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy: ', err);
                this.innerHTML = '<i class="fas fa-times"></i> Failed to copy';
                setTimeout(() => {
                    this.innerHTML = '<i class="fas fa-copy"></i> Copy analysis';
                }, 2000);
            });
        });
    }

    // Bootstrap tooltips initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
// Image Preview text was removed.
