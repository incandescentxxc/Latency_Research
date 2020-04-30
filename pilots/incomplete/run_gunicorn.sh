#!/bin/bash -x

timestamp=$( date +%Y-%m-%d_%H-%M-%S )
#../../../env/bin/gunicorn --workers 7  --log-file search_study_gunicorn.log --log-level info --bind unix:search-study.sock -m 777 wsgi:application
gunicorn --workers 7  --log-file search_study_gunicorn_${timestamp}.log --log-level info --bind 0.0.0.0:5064 -m 777 wsgi:application
