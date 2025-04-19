// WanderMatch Frontend Scripts

document.addEventListener('DOMContentLoaded', function() {
    console.log("Document loaded, initializing survey form");
    
    const surveyForm = document.getElementById('surveyForm');
    if (!surveyForm) {
        console.error("Survey form not found in the document!");
        return;
    }
    
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    // Create loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Submitting your answers...</p>
    `;
    document.body.appendChild(loadingOverlay);
    loadingOverlay.style.display = 'none';
    
    // Create alert container if it doesn't exist
    function createAlertContainer() {
        console.log("Creating alert container");
        const container = document.createElement('div');
        container.id = 'alertContainer';
        container.className = 'mb-4';
        
        // Insert before the form or at the beginning of the body
        if (surveyForm) {
            surveyForm.parentNode.insertBefore(container, surveyForm);
        } else {
            document.body.insertBefore(container, document.body.firstChild);
        }
        
        return container;
    }
    
    // Set up destination autofill
    setupDestinationAutofill();
    
    // Default values for survey fields
    const defaultValues = {
        'name': 'Anonymous',
        'age': 'Not specified',
        'gender': 'Not specified',
        'nationality': 'Not specified',
        'destination': 'Not specified',
        'cultural_symbol': 'Not specified',
        'bucket_list': 'Not specified',
        'healthcare': 'Not specified',
        'budget': 'Not specified',
        'payment_preference': 'Not specified',
        'insurance': 'Not specified',
        'insurance_issues': 'Not specified',
        'travel_season': 'Not specified',
        'stay_duration': 'Not specified',
        'interests': 'Not specified',
        'personality_type': 'Not specified', 
        'communication_style': 'Not specified',
        'travel_style': 'Not specified',
        'accommodation_preference': 'Not specified',
        'origin_city': 'Not specified',
        'destination_city': 'Not specified'
    };
    
    // Handle form submission
    surveyForm.addEventListener('submit', function(event) {
        console.log("Form submission started");
        event.preventDefault();
        
        // Clear previous alerts
        alertContainer.innerHTML = '';
        
        try {
            // Show loading overlay
            loadingOverlay.style.display = 'flex';
            
            // Auto-fill destination_city with destination if empty
            const destinationField = document.querySelector('[name="destination"]');
            const destinationCityField = document.querySelector('[name="destination_city"]');
            if (destinationField && destinationCityField && !destinationCityField.value.trim() && destinationField.value.trim()) {
                destinationCityField.value = destinationField.value;
                console.log("Auto-filled destination_city with destination value");
            }
            
            // Collect form data
            const formData = {};
            const formElements = surveyForm.elements;
            
            for (let i = 0; i < formElements.length; i++) {
                const element = formElements[i];
                if (element.name && element.name !== '' && element.type !== 'submit') {
                    formData[element.name] = element.value.trim();
                }
            }
            
            console.log('Collecting form data:', formData);
            
            // Send data to server
            fetch('http://localhost:5000/api/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Server response:', data);
                
                if (data.error) {
                    showAlert('warning', `Server reported an error: ${data.error}. Please try again.`);
                    return;
                }
                
                if (data.file_saved) {
                    console.log('Survey data saved server-side');
                    
                    // Create a success message with file path information
                    const filepath = data.filepath || "Unknown path";
                    const filename = data.filename || "Unknown file";
                    const directory = data.directory || "Unknown directory";
                    
                    const successHtml = `
                        <div class="alert alert-success" role="alert">
                            <h4 class="alert-heading">Survey Submitted Successfully!</h4>
                            <p>Your survey data has been saved.</p>
                            <hr>
                            <div class="file-path-info">
                                <p class="mb-1"><strong>File:</strong> ${filename}</p>
                                <p class="mb-1"><strong>Directory:</strong> ${directory}</p>
                                <p class="mb-0"><strong>Full path:</strong> ${filepath}</p>
                            </div>
                        </div>
                    `;
                    
                    // Create a survey completion section
                    const completionSection = document.createElement('div');
                    completionSection.className = 'survey-complete mt-4 p-4 border rounded';
                    completionSection.innerHTML = successHtml;
                    
                    // Add a "Start New Survey" button
                    const resetButton = document.createElement('button');
                    resetButton.className = 'btn btn-primary mt-3';
                    resetButton.textContent = 'Start New Survey';
                    resetButton.addEventListener('click', function() {
                        window.location.reload();
                    });
                    completionSection.appendChild(resetButton);
                    
                    // Add a "Copy Path" button
                    const copyButton = document.createElement('button');
                    copyButton.className = 'btn btn-secondary mt-3 ms-2';
                    copyButton.textContent = 'Copy File Path';
                    copyButton.addEventListener('click', function() {
                        navigator.clipboard.writeText(filepath)
                            .then(() => {
                                copyButton.textContent = 'Copied!';
                                setTimeout(() => { copyButton.textContent = 'Copy File Path'; }, 2000);
                            })
                            .catch(err => {
                                console.error('Could not copy text: ', err);
                                copyButton.textContent = 'Failed to copy';
                                setTimeout(() => { copyButton.textContent = 'Copy File Path'; }, 2000);
                            });
                    });
                    completionSection.appendChild(copyButton);
                    
                    // Replace form with completion message
                    const formContainer = surveyForm.parentNode;
                    formContainer.insertBefore(completionSection, surveyForm);
                    surveyForm.style.display = 'none';
                    
                    // Show success message in the alert container too
                    showAlert('success', 'Your survey has been successfully submitted and saved.');
                    
                    // Send message to parent window if it exists
                    if (window.opener && !window.opener.closed) {
                        try {
                            const message = {
                                type: 'survey_complete',
                                filepath: filepath,
                                filename: filename,
                                directory: directory
                            };
                            window.opener.postMessage(message, '*');
                            console.log('Notified parent window of survey completion');
                        } catch (e) {
                            console.error('Failed to notify parent window:', e);
                        }
                    }
                    
                    // Also send the information directly to the parent app's server
                    try {
                        fetch('http://localhost:4000/survey-file-info', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                filepath: filepath,
                                filename: filename,
                                directory: directory
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log('File information sent to parent app:', data);
                        })
                        .catch(error => {
                            console.error('Error sending file information to parent app:', error);
                        });
                    } catch (e) {
                        console.error('Failed to send file information to parent app:', e);
                    }
                    
                    // Scroll to top to show the message
                    window.scrollTo(0, 0);
                } else {
                    showAlert('warning', 'Survey data could not be saved. Please try again later.');
                }
            })
            .catch(error => {
                console.error('Server error:', error);
                showAlert('danger', 'Error contacting server. Please try again later.');
                
                // Hide loading overlay on error
                loadingOverlay.style.display = 'none';
            })
            .finally(() => {
                // Hide loading overlay
                loadingOverlay.style.display = 'none';
            });
        } catch (error) {
            console.error('Error in form submission:', error);
            loadingOverlay.style.display = 'none';
            showAlert('danger', 'An unexpected error occurred: ' + error.message);
        }
    });
    
    // Show an alert message
    function showAlert(type, message) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        alertContainer.innerHTML = alertHtml;
    }
    
    // Setup destination field autofill
    function setupDestinationAutofill() {
        console.log("Setting up destination autofill");
        const destinationField = document.querySelector('[name="destination"]');
        const destinationCityField = document.querySelector('[name="destination_city"]');
        
        if (destinationField && destinationCityField) {
            console.log("Found destination fields, setting up listeners");
            
            // When destination changes, update destination_city if it's empty
            destinationField.addEventListener('input', function() {
                if (!destinationCityField.value.trim()) {
                    destinationCityField.value = this.value.trim();
                }
            });
            
            // Initial fill if destination is already set
            if (destinationField.value.trim() && !destinationCityField.value.trim()) {
                destinationCityField.value = destinationField.value.trim();
            }
        } else {
            console.warn("Could not find destination fields for autofill");
        }
    }
});

function mapFormFieldNames() {
    // Get all form elements
    const form = document.getElementById('questionnaireForm');
    if (!form) return;
    
    // Mapping of form field IDs to expected server field names
    const fieldMapping = {
        'name': 'name',
        'age': 'age',
        'gender': 'gender',
        'nationality': 'nationality',
        'destination': 'destination',
        'cultural_symbol': 'cultural_symbol',
        'bucket_list': 'bucket_list',
        'healthcare': 'healthcare',
        'budget': 'budget',
        'payment_preference': 'payment_preference',
        'insurance': 'insurance',
        'insurance_issues': 'insurance_issues',
        'travel_season': 'travel_season',
        'stay_duration': 'stay_duration',
        'interests': 'interests',
        'personality_type': 'personality_type',
        'communication_style': 'communication_style',
        'travel_style': 'travel_style',
        'accommodation_preference': 'accommodation_preference',
        'origin_city': 'origin_city',
        'destination_city': 'destination_city'
    };
    
    // Update name attributes to match the server's expected field names
    Object.entries(fieldMapping).forEach(([formId, serverName]) => {
        const element = form.querySelector(`#${formId}`);
        if (element) {
            element.setAttribute('name', serverName);
        }
    });
}

function showLoadingOverlay(message = 'Processing...') {
    // Remove existing overlay if any
    hideLoadingOverlay();
    
    // Create loading overlay
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.classList.add('loading-overlay');
    
    const spinner = document.createElement('div');
    spinner.classList.add('spinner');
    
    const messageEl = document.createElement('p');
    messageEl.textContent = message;
    messageEl.classList.add('mt-3', 'text-center');
    
    overlay.appendChild(spinner);
    overlay.appendChild(messageEl);
    document.body.appendChild(overlay);
    document.body.classList.add('overflow-hidden');
}

function hideLoadingOverlay() {
    const existingOverlay = document.getElementById('loadingOverlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    document.body.classList.remove('overflow-hidden');
}

function showErrorMessage(message) {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.className = 'alert-container';
        document.body.appendChild(alertContainer);
    }
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.role = 'alert';
    
    // Add message
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 500);
    }, 5000);
}

function showSuccessMessage(message) {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.className = 'alert-container';
        document.body.appendChild(alertContainer);
    }
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show';
    alert.role = 'alert';
    
    // Add message
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alert);
} 