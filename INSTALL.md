Installation Guide for Project Kensho
Follow these steps to set up the complete Project Kensho environment.

1. Prerequisites
Python 3.8+

pip (Python package installer)

2. Clone the Repository & Set Up Environment
git clone <your-repository-url>
cd project_kensho
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

3. Install Python Dependencies
Install all required libraries from the requirements.txt file.

pip install -r requirements.txt

4. Download NLP Model
The "Brain" requires a language model from spaCy. Download it with the following command:

python -m spacy download en_core_web_sm

5. Configure API Credentials
Rename config.ini.template to config.ini.

Open config.ini and fill in the required API keys, tokens, and IDs for each service you plan to use. This is essential for the "Hands" to function.

Your setup is now complete. Proceed to the GUIDE.md for instructions on how to run the application.