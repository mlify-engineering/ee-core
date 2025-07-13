# 🇨🇦 Immigration Draw Data Processor

A Python-based pipeline to fetch, process, and analyze Canada's Express Entry immigration draw data. This project uses FastAPI, APScheduler, and Azure Blob Storage to automate data updates and serve results via an HTTP endpoint.

---

## 🚀 Features

- ✅ Fetch latest data from IRCC JSON endpoint
- 📊 Generate CRS, pool, and draw size trends
- 🧠 Organize & structure data for frontend visualization
- ☁️ Upload processed results to Azure Blob Storage
- 🔁 Run automatically on a daily schedule (cron via APScheduler)
- 🌐 Manual run endpoint (`/run-now`) via FastAPI
- 🔄 Auto-deploy to Azure using GitHub Actions

---

## 🧱 Project Structure

```

ee-core/
│
├── data/                         # Input + output JSON files
│   └── input.json
│   └── processed\_data\_\*.json
│
├── src/
│   ├── main.py                   # FastAPI + orchestrator
│   └── immigration\_processor.py # Data processing logic
│
├── .github/
│   └── workflows/
│       └── azure-webapps-python.yml # GitHub Actions CI/CD
│
├── .env                          # Environment variables (for local testing)
├── requirements.txt              # Python dependencies
└── README.md

````

---

## ⚙️ Environment Variables

Create a `.env` file or set these in Azure App Service → Configuration:

```env
AZURE_STORAGE_CONN=<your-azure-blob-connection-string>
AZURE_CONTAINER_NAME=<your-container-name>
DATA_FETCH_URL=https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json
````

---

## 🏃‍♂️ Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI app
uvicorn src.main:app --reload
```

* Visit [http://localhost:8000/run-now](http://localhost:8000/run-now) to manually trigger the full pipeline.

---

## ☁️ Deploy to Azure (via GitHub Actions)

1. Push this project to a **GitHub repository**
2. In **Azure Portal**:

   * Create or use an existing App Service
   * Go to **Deployment Center**
   * Choose **GitHub**, select your repo and branch
3. Azure will auto-generate a GitHub Actions workflow and deploy on every push
4. Go to **Configuration** → **Application Settings** and set your environment variables (`.env` contents)
5. Ensure **Always On** is enabled under **General Settings**

---

## 📅 Automation (Scheduled Daily Run)

The app uses `APScheduler` to run daily at 3:00 AM server time:

```python
scheduler.add_job(lambda: asyncio.run(orchestrate()), trigger="cron", hour=3, minute=0)
```

No Azure Functions or cron jobs needed — it’s handled inside the app.

---

## 📂 Output Files (Uploaded to Blob)

* `processed_data_crs_trend.json`
* `processed_data_pool_trend.json`
* `processed_data_draw_size.json`

These files are uploaded to the Azure Blob container you configure.

---

## 📬 API Endpoints

| Method                | Endpoint   | Description                               |
| --------------------- | ---------- | ----------------------------------------- |
| GET                   | `/run-now` | Manually trigger fetch → process → upload |


---

## ✅ TODO / Ideas

* [x] Add frontend dashboard using Plotly.js or React
* [ ] Add health check endpoint (`/status`)

---

## 🧑‍💻 Author

**Habibur Rahman**

MIT License