# Record App

This Flask application reads data from MongoDB and allows administrators to edit
records through a web interface. Finalised data are stored in the `check_done`

collection. Use the toggle on the main page to switch between records from
`qa_bot` and those moved to the `problem` collection.

Completed records can be searched and edited from the "已录记录" page, which
lists entries ordered by number.

collection.


## Configuration

Secrets are provided via environment variables:

- `MONGO_URI` – MongoDB connection string
- `FLASK_SECRET_KEY` – secret key used for Flask sessions

You can create a `.env` file based on `.env.example` and load it in your
environment before running the application.
Start the app with:

```bash
python app.py
```
