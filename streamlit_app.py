# -*- coding: utf-8 -*-
"""
streamlit_app.py -- thin entry point for Streamlit Community Cloud.

Streamlit Cloud defaults to looking for a file named streamlit_app.py.
The real game lives in app.py; this module just imports and runs it
so the deployment default "just works" without renaming.
"""
import runpy
runpy.run_path("app.py", run_name="__main__")
