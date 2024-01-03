#!/bin/bash

set -e

source /env/bin/activate

if [$1 == 'gunicorn']; then

    exec gunicorn StravaWebsite-master/StravaWebsite.wsgi:application -b 0.0.0.0:8000
    
     