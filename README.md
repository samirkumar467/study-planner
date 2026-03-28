# Student Planner

Student Planner is a Flask web app for tracking study tasks, monitoring progress, and staying ahead of deadlines.

## Why your deploy showed a 404

This project is a Python web application, not a static website. If you deploy it to a static host such as GitHub Pages, the host looks for a root `index.html` file and returns a 404 because Flask templates only work when a Python server is running.

## Deploy on a Python host

Use a platform that supports Python web apps, such as Render, Railway, PythonAnywhere, or a Vercel Python setup.

Recommended start command:

```bash
gunicorn app:app
```

## Local run

```bash
pip install -r requirements.txt
python app.py
```

## Notes

- Set a real `SECRET_KEY` environment variable in production.
- `database.db` is ignored from git because SQLite data should not be committed for deployment workflows.
- If `venv/` or `database.db` were already pushed earlier, remove them from git tracking before your next deploy.
