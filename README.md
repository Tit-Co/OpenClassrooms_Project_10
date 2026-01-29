# Django app - OpenClassrooms Project 09
**Develop a web application using Django**

---

## DESCRIPTION

This project was completed as part of the "Python Developer" path at OpenClassrooms.

The goal was to develop a secured API Restful using Django REST Framework capable of:
- serving front-end applications on different platforms
- processing datas in a standard way

The application must:
- comply with OWASP security and optimization requirements
- comply with the "green code" requirements
- comply with GDPR specifications

---

## EXPLANATIONS OF WHAT THE APP DOES

### <u>User management</u>

- 

### <u>Projects management</u>

- 

### <u>Tasks & issues management</u>

-

### <u>Comments management</u>

- 

---

## PROJECT STRUCTURE
<p align="center">
<img src="docs/structure_1.png" width="auto" style="border: 1px solid grey; border-radius: 10px;">
<img src="docs/structure_2.png" width="auto" style="border: 1px solid grey; border-radius: 10px;">
</p>

---

## INSTALLATION

### - Clone the repository :
`git clone https://github.com/Tit-Co/OpenClassrooms_Project_10.git`

### - Navigate into the project directory :
`cd OpenClassrooms_Project_10`

### - Create a virtual environment and dependencies :
### Option 1 - with [uv](https://docs.astral.sh/uv/)

`uv` is an environment and dependencies manager.

#### - Install environment and dependencies

`uv sync`

### Option 2 - with pip

#### - Install the virtual env :

`python -m venv env`

#### - Activate the virtual env :
`source env/bin/activate`  
Or  
`env\Scripts\activate` on Windows  

### - Install dependencies 
#### Option 1 - with [uv](https://docs.astral.sh/uv/)

`uv pip install -U -r requirements.txt`

#### Option 2 - with pip

`pip install -r requirements.txt` 

---

## USAGE

### Launching server
- Open a terminal
- Go to project folder - example : `cd softdesk_support`
- If needed, make migrations and execute them : 
  - `python manage.py makemigrations`
  - `python manage.py migrate`
- Launch the Django server : `python manage.py runserver`

### Launching the website
- Open a web browser
- And type the URL : `http://127.0.0.1:8000/`
---

## EXAMPLES

- Log in
<p align="center">
    <img src="docs/screenshots/homepage_screenshot.png" width="auto" style="border: 1px solid grey; border-radius: 10px;">
</p>



## PEP 8 CONVENTIONS

- Flake 8 report
<p align="center">
    <img src="docs/screenshots/flake8_screenshot.png" width="auto" style="border: 1px solid grey; border-radius: 10px;">
</p>

---

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## AUTHOR
**Name**: Nicolas MARIE  
**Track**: Python Developer – OpenClassrooms  
**Project – Develop a web app using Django – December 2025**
