# Project Makefile Usage Guide

This Makefile provides convenient targets to manage your Django project, such as creating a virtual environment, installing dependencies, starting the development server, and more.

## Prerequisites

- Python 3.11 or change it to your python version in make file

## Getting Started

1. Clone or download the project to your local machine.
2. Navigate to the project directory in your terminal.

## Setup

### 1. Create Virtual Environment and Install Dependencies

To set up your development environment:

```bash
make setup
```
This command will create a virtual environment (if not already present) and install the required dependencies from `requirements.txt`.


### 2. Start the Django Development Server
To run the Django development server with .env variables:

```bash
make start
```
The server will start, and you can access your Django application at http://localhost:8000/.

### 3. Create Superuser

To create a superuser with a specific password (default: 12345678, username: admin):
```bash
make create_superuser
```
This command will create a superuser account with administrative privileges to access admin portal at 
http://localhost:8000/admin/.

### Other Useful Commands

`make install`: Install dependencies from requirements.txt into the virtual environment.
`make clean`:  Delete the virtual environment and start fresh.

# Important Note

`*` to test the flow use custom api `/api/v1/custom/collect/` to set date based on your need and functions will calculate based on today's date
ex. if you want to test frozen and your threshold is 2 days add datetime which will point to 2 days ago with early time
so if today is 2024-05-07 00:06:22.499937 so you can send 2024-05-05 00:06:10.306930 and test if frozen or not


#### Project Description (Api):

to access swagger enter http://localhost:8000/api/docs/

`-` first you need to users (not supervisors as it means not manager) 

`-` create tasks for you users

`-` go to swagger and log in to gain access key ( expires after 1 hour ) 

`-` start collecting tasks using `/api/v1/collect/`

`-` You can list old done tasks using `/api/v1/tasks/`

`-` You can list logged-in user next task using `/api/v1/next-task/`

`-` You can check if logged-in user is frozen or not using `/api/v1/status/`

`-` You can pay all collected money for logged-in user using `/api/v1/pay/all/`

`-` You can pay some of collected money for logged-in user using `/api/v1/pay/some/`
