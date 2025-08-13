# grobid2 - bibliography extracter

A brief description of your project and what it does. Explain its purpose and main features here.

***

## 🚀 Getting Started

Follow these instructions to get your project set up and running.

### **Installation**

1.  **Clone the repository (optional):**
    ```bash
    git clone https://github.com/HGTNewCoder/grobid2.git
    ```

2.  **Install required packages:**
    Run the following command in your terminal to install all the necessary dependencies.
    ```bash
    pip install -r requirements.txt
    ```

***

## ⚙️ Configuration

You'll need to configure a few things before you can run the script.

1.  **Download Google Cloud Credentials**
    * First, create a new project in the [Google Cloud Console](https://console.cloud.google.com/).
    * Enable the Google Sheets API for your project.
    * Create service account credentials and download the `credentials.json` file.
    * **IMPORTANT**: Place the downloaded `credentials.json` file in the root directory of this project.

2.  **Find Your Google Sheet ID**
    * Copy the `SHEET_ID` from your Google Sheets URL. It's the long string of characters between `/d/` and `/edit`.
    * **Example URL:** `https://docs.google.com/spreadsheets/d/SHEET_ID/edit?gid=0#gid=0`

3.  **Update Script Parameters**
    * Open the `secret_input.py` file.
    * Update the variables with your specific `SHEET_ID` and any other required parameters.

***

## ▶️ Usage

Once the installation and configuration are complete, you can run the main script:

```bash
python grobid_processor.py
