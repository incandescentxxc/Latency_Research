web: gunicorn --pythonpath pilots --workers 7 --log-file search_study_gunicorn.log --log-level info --bind 0.0.0.0:5000 -m 777 incomplete.wsgi:application
