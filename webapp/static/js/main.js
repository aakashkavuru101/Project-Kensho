document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const loader = document.getElementById('loader');
    const resultsSection = document.getElementById('results-section');
    const jsonOutput = document.getElementById('json-output').querySelector('code');
    const handsButtons = document.getElementById('hands-buttons');
    const messageArea = document.getElementById('message-area');

    let currentPlanData = null;
    let currentTaskId = null;
    let statusPollingInterval = null;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        
        resultsSection.classList.add('hidden');
        loader.classList.remove('hidden');
        messageArea.classList.add('hidden');
        setButtonsDisabled(true);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Analysis failed');
            }

            currentPlanData = result;
            jsonOutput.textContent = JSON.stringify(currentPlanData, null, 2);
            resultsSection.classList.remove('hidden');
            setButtonsDisabled(false);
            
            showMessage('Document analyzed successfully!', 'success');

        } catch (error) {
            showMessage(`Error: ${error.message}`, 'error');
        } finally {
            loader.classList.add('hidden');
        }
    });

    handsButtons.addEventListener('click', async (e) => {
        if (e.target.tagName !== 'BUTTON') return;
        
        const target = e.target.dataset.target;
        if (!currentPlanData || !target) {
            alert('No plan data available to execute.');
            return;
        }

        // Clear any existing polling
        if (statusPollingInterval) {
            clearInterval(statusPollingInterval);
            statusPollingInterval = null;
        }

        loader.classList.remove('hidden');
        messageArea.classList.add('hidden');
        setButtonsDisabled(true);

        try {
            // Start async execution
            const response = await fetch('/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plan: currentPlanData, target: target }),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to start execution');
            }
            
            currentTaskId = result.task_id;
            showMessage(`Execution started for ${target}. Task ID: ${currentTaskId}`, 'info');
            
            // Start polling for status
            startStatusPolling(target);

        } catch (error) {
            showMessage(`Error: ${error.message}`, 'error');
            loader.classList.add('hidden');
            setButtonsDisabled(false);
        }
    });

    function startStatusPolling(target) {
        if (!currentTaskId) return;
        
        statusPollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${currentTaskId}`);
                const status = await response.json();
                
                if (!response.ok) {
                    throw new Error('Failed to get task status');
                }
                
                updateStatusDisplay(status, target);
                
                // Stop polling if task is complete
                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(statusPollingInterval);
                    statusPollingInterval = null;
                    loader.classList.add('hidden');
                    setButtonsDisabled(false);
                }
                
            } catch (error) {
                console.error('Status polling error:', error);
                clearInterval(statusPollingInterval);
                statusPollingInterval = null;
                loader.classList.add('hidden');
                setButtonsDisabled(false);
                showMessage('Failed to get task status', 'error');
            }
        }, 2000); // Poll every 2 seconds
    }
    
    function updateStatusDisplay(status, target) {
        let message = `${target} execution: ${status.message}`;
        let type = 'info';
        
        if (status.status === 'completed') {
            if (status.success) {
                message = `✅ ${target} execution completed successfully!`;
                type = 'success';
                if (status.logs) {
                    console.log('Execution Logs:', status.logs);
                }
            } else {
                message = `❌ ${target} execution failed`;
                type = 'error';
            }
        } else if (status.status === 'failed') {
            message = `❌ ${target} execution failed: ${status.message}`;
            type = 'error';
            if (status.logs) {
                console.error('Error Logs:', status.logs);
            }
        } else if (status.status === 'running') {
            message = `⏳ ${target} execution in progress...`;
            type = 'info';
        }
        
        showMessage(message, type);
    }

    function showMessage(text, type) {
        messageArea.textContent = text;
        messageArea.className = 'p-4 rounded-md mb-4 text-sm'; // Reset classes
        
        if (type === 'success') {
            messageArea.classList.add('bg-green-100', 'text-green-800');
        } else if (type === 'info') {
            messageArea.classList.add('bg-blue-100', 'text-blue-800');
        } else {
            messageArea.classList.add('bg-red-100', 'text-red-800');
        }
        messageArea.classList.remove('hidden');
    }

    function setButtonsDisabled(disabled) {
        handsButtons.querySelectorAll('button').forEach(button => {
            button.disabled = disabled;
            if (disabled) {
                button.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                button.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        });
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (statusPollingInterval) {
            clearInterval(statusPollingInterval);
        }
    });
});
