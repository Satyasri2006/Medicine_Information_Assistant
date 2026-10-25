# Medicine Information Assistant

#Live Website: [https://your-mia.streamlit.app/](https://your-mia.streamlit.app/)

An NLP-based medicine information assistant that helps users explore medicine-related information through a conversational interface. The application combines **Natural Language Processing (NLP), Machine Learning, Streamlit, and MongoDB** to process user queries, identify their intent, and provide relevant medicine information.

Built as an academic project to explore how machine learning and conversational interfaces can make structured medicine information easier to access.

## ✨ Features

- **Conversational Interface:** Ask medicine-related questions through a chat-based interface built with Streamlit.
- **Intent Classification:** Uses TF-IDF text features and Logistic Regression to classify user queries into supported intents.
- **Medicine Information:** Supports queries related to medicine uses, dosage information, side effects, warnings, and summaries, depending on the available data.
- **Medicine Name Matching:** Uses text matching to identify medicine names in user queries.
- **User Authentication:** Includes user registration and login functionality.
- **Conversation History:** Stores conversations and allows users to revisit previous interactions.
- **Machine Learning Evaluation:** Evaluates the intent classification model using accuracy and macro F1-score.
- **Database Integration:** Uses MongoDB to persist application data.

## 🛠️ Tech Stack

| Component | Technologies |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| Natural Language Processing | TF-IDF Vectorization |
| Machine Learning | Logistic Regression, scikit-learn |
| Text Processing | Unigrams and Bigrams |
| Database | MongoDB |
| Database Driver | PyMongo |
| Authentication | Password hashing with PBKDF2-HMAC and SHA-256 |
| Data Handling | CSV and Python data-processing libraries |

## 🧠 How It Works

The application follows a machine-learning-based query-processing workflow.

1. **User input:** The user enters a question about a medicine.
2. **Text vectorization:** TF-IDF converts the text into numerical features, using unigrams and bigrams.
3. **Intent prediction:** The trained Logistic Regression model predicts the intent of the query.
4. **Medicine identification:** The application processes the query to identify a matching medicine name.
5. **Response generation:** The application uses the predicted intent and available medicine information to prepare a relevant response.
6. **Conversation storage:** Conversation data is persisted for later access through the application's history functionality.

### Architecture

```text
           User
            |
            v
     Streamlit Chat UI
            |
            v
      Query Processing
            |
            v
    TF-IDF Vectorization
            |
            v
  Logistic Regression Model
            |
            v
   Intent Classification
            |
            v
    Medicine Name Matching
            |
            v
   Response Preparation
            |
            v
      Display Response

   MongoDB: User and Chat Data
```

## 📁 Project Structure

```text
Medicine_Information_Assistant/
│
├── app.py              # Streamlit application and chat interface
├── model.py            # ML model training, prediction and evaluation
├── database.py         # Database operations
├── models/             # Saved machine learning artifacts
├── data/               # Medicine and training datasets, if present
├── assets/             # Application assets, if present
├── requirements.txt    # Python dependencies
├── .gitignore          # Git exclusion rules
└── README.md           # Project documentation
```

*Note: The directory descriptions above are intended to explain the project layout. Adjust them to match the files and folders currently present in your repository.*

## ⚙️ Getting Started

Follow these steps to run the project locally.

### Prerequisites

Make sure you have the following installed:

- Python 3.10 or a compatible version supported by your dependencies
- Git
- A MongoDB deployment and valid connection details

### 1. Clone the Repository

```bash
git clone https://github.com/Satyasri2006/Medicine_Information_Assistant.git
```

Navigate into the project directory:

```bash
cd Medicine_Information_Assistant
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

If you use Command Prompt instead:

```cmd
venv\Scripts\activate.bat
```

### 3. Install Dependencies

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Configure the Database

Configure the MongoDB connection using the environment variable expected by `database.py`.

For local development, you can use a `.env` file if the application is configured to load it, or configure the variable in your terminal.

**Important:** Do not commit database credentials, passwords, or other secrets to GitHub. Ensure that `.env` is excluded in `.gitignore` when applicable.

### 5. Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal, typically:

```text
http://localhost:8501
```

Follow the interface to register or log in and begin exploring the supported medicine-related queries.

## 🤖 Machine Learning Approach

The project uses a supervised text-classification pipeline to interpret user queries.

### TF-IDF Vectorization

Term Frequency–Inverse Document Frequency (TF-IDF) transforms textual input into numerical feature vectors. Both unigrams and bigrams are used to capture individual words and two-word expressions.

### Logistic Regression

Logistic Regression is used to classify the vectorized text into the intent categories represented in the training dataset.

### Model Evaluation

The implementation evaluates the classifier using:

- **Accuracy:** Measures the proportion of test samples classified correctly.
- **Macro F1-score:** Calculates the F1-score for each class and averages them equally, helping assess performance across different intent categories.

Actual model performance depends on the quality, size, class distribution, and representativeness of the training dataset.

## 🗄️ Database

MongoDB is used for persistent application data.

The database layer supports user-related operations and conversation storage. Passwords are processed using a salted PBKDF2-HMAC SHA-256 hashing approach rather than being stored as plain-text passwords.

Database availability and correct connection configuration are required for database-dependent functionality.

## 📌 Future Improvements

- Improve medicine name recognition and handling of spelling variations.
- Expand and validate the intent-classification dataset.
- Add confusion matrices and per-class precision, recall, and F1-scores.
- Improve handling of ambiguous, unsupported, or out-of-scope queries.
- Integrate trusted, traceable medicine information sources.
- Display source references and information update dates alongside responses.
- Improve automated testing and application error handling.
- Enhance the interface for accessibility and usability.
- Add deployment instructions and a publicly accessible demo, if available.

## ⚠️ Disclaimer

This project is developed for **educational and informational purposes only**. It is not a substitute for advice from a qualified healthcare professional.

Medicine information displayed by the application depends on the available dataset and application logic and may be incomplete or outdated. Do not use the application to make independent decisions about medication dosage, treatment, drug interactions, or medical emergencies. Always consult a qualified healthcare professional or an authoritative medical source.

## 👩‍💻 Author

**Satyasri**

B.Tech — Computer Science and Engineering

GitHub: [@Satyasri2006](https://github.com/Satyasri2006)

---

⭐ If you find this project interesting, feel free to explore the repository and share feedback.
