document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const loader = document.getElementById('loader');
    const resultsSection = document.getElementById('results-section');
    const jsonOutput = document.getElementById('json-output').querySelector('code');
    const handsButtons = document.getElementById('hands-buttons');
    const messageArea = document.getElementById('message-area');

    let currentPlanData = null;

    // Check configuration status on page load
    checkConfigurationStatus();

    async function checkConfigurationStatus() {
        try {
            const response = await fetch('/get_config_status');
            const configStatus = await response.json();
            
            if (response.ok) {
                updateButtonsBasedOnConfig(configStatus);
            } else {
                console.error('Failed to get configuration status:', configStatus.error);
            }
        } catch (error) {
            console.error('Error checking configuration status:', error);
        }
    }

    function updateButtonsBasedOnConfig(configStatus) {
        handsButtons.querySelectorAll('button').forEach(button => {
            const target = button.dataset.target;
            const isConfigured = configStatus[target];
            
            if (!isConfigured) {
                button.disabled = true;
                button.title = `${target.toUpperCase()} is not configured. Check your config.ini file.`;
                button.classList.add('opacity-50', 'cursor-not-allowed');
                button.classList.remove('hover:bg-blue-900', 'hover:bg-pink-700', 'hover:bg-blue-600', 'hover:bg-green-700', 'hover:bg-purple-700', 'hover:bg-gray-700');
            } else {
                button.disabled = false;
                button.title = `Send to ${target.toUpperCase()}`;
                button.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        });
    }

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
            
            // Re-check configuration status when new plan is loaded
            checkConfigurationStatus();

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

        loader.classList.remove('hidden');
        messageArea.classList.add('hidden');
        setButtonsDisabled(true);

        try {
            const response = await fetch('/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plan: currentPlanData, target: target }),
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                console.error("Execution Logs:", result.logs);
                throw new Error(result.error || 'Execution failed. Check console for logs.');
            }
            
            showMessage(result.message, 'success');
            console.log('Execution Logs:', result.logs);

        } catch (error) {
            showMessage(`Error: ${error.message}`, 'error');
        } finally {
            loader.classList.add('hidden');
            setButtonsDisabled(false);
        }
    });

    function showMessage(text, type) {
        messageArea.textContent = text;
        messageArea.className = 'p-4 rounded-md mb-4 text-sm'; // Reset classes
        if (type === 'success') {
            messageArea.classList.add('bg-green-100', 'text-green-800');
        } else {
            messageArea.classList.add('bg-red-100', 'text-red-800');
        }
        messageArea.classList.remove('hidden');
    }

    function setButtonsDisabled(disabled) {
        handsButtons.querySelectorAll('button').forEach(button => {
            button.disabled = disabled;
        });
    }
});
