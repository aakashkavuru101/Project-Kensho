document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const loader = document.getElementById('loader');
    const resultsSection = document.getElementById('results-section');
    const jsonOutput = document.getElementById('json-output').querySelector('code');
    const handsButtons = document.getElementById('hands-buttons');
    const messageArea = document.getElementById('message-area');

    let currentPlanData = null;

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
