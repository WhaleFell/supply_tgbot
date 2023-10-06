#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# register/mount.py 挂载静态文件

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def register_mount(app: FastAPI):
    """挂载静态文件"""
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
