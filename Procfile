web: gunicorn --preload --log-file search_study_gunicorn.log --chdir pilots/incomplete --log-level info --bind 0.0.0.0:5000 -m 777 wsgi:application
