# Storyteller

This repository contains the application for the Storyteller project. Storyteller is an adventure where you cooperate with AI to tell a story. The story is visualized with images. The project was created as an entry for the AMD Pervasive AI Developer Contest on [Hackster.io](https://www.hackster.io/contests/amd2023). Additional information about the project are available at [Storyteller](https://www.hackster.io/uhudo/storyteller-8f7ce6).

The project consists of the frontend application which we implemented in Streamlit and two AI model servers that provide the access to LLM and text-to-image models. We used Llama3.1 model for the LLM and stable-diffusion-3-medium-diffusers for the text-to-image model.

Project is implemented in Python and was developed to work with [AMD Accelerator Cloud](https://aac.amd.com) where we used [AMD Instinct MI210](https://www.amd.com/en/products/accelerators/instinct/mi200/mi210.html) accelerators by using [AMD ROCm Software](https://www.amd.com/en/products/software/rocm.html). In the development we used prepared containers with PyTorch v2.1.2 and ROCm v6.1.2 but the project can be deployed on other platforms using ROCm.

## Initial step
Gain access to models on huggingface.co:
 - [stabilityai/stable-diffusion-3-medium](https://huggingface.co/stabilityai/stable-diffusion-3-medium)
 - [meta-llama/Meta-Llama-3.1-8B](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)

## Servers
First, we will present how to run the servers and later we will show how to do initial setup specific for the cloud. If not running the servers in a container, create a python virtual environment first and provide additional packages specific to your hardware.
### Instal requirements
In folder storyteller/storyteller_servers/ run command:
```
pip install -r requirements.txt
```
### Running servers
In folder storyteller/storyteller_servers in two seperate terminals run:
```
python llama_server.py
```
```
python stable_diffusion_server.py
```
Wait some time for the models to be downloaded. For this to happen you need to have huggingface key set. You can check in the Cloud section for instructions.

## Application
After the servers are running and you can access the servers on localhost (check tunnelling section below for running on cloud), start the application. You should run the application on your PC (not in the cloud).
### Install requirements
In folder storyteller/
```
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```
### Running application
In folder storyteller/ run:
```
.venv\Scripts\activate.bat
streamlit run storyteller.py
```
By default you can access the application on http://localhost:8501.

## AMD Accelerator Cloud
This is preparation for running the AI model servers in the AMD Accelerator Cloud.
### Setup
 - When logged in the [AMD Accelerator Cloud](https://aac.amd.com).
 - Create new workload where you select PyTorch container with PyTorch v2.1.2 and ROCm v6.1.2.
 - In the next step no input files are need.
 - Then you set the time limit to for example 4h and enable telemetry to monitor your workload resource usage.
 - We selected AIG MI210 queue.
 - Overview the selection and run the workload.
 - Than wait until you see Connect button for the workload.
### Connection
 - On windows open CMD or terminal on Linux and paste in the connection details provided on Connect button in the cloud interface. Where XXXX is your port number provided.
```
ssh -p XXXX aac@aac1.amd.com
```
Save the credentials with typing 'yes' and paste in the key from the online interface. You will gain access to the container.
### First time setup
In the container for the first time enable huggingface connection. Under your account on huggingface.co go to account>setting>access tokens and create a new token. There you set read access for the personal models and public gated models. Wait before you close the generated key by first running the below commands in the terminal in the container.
```
pip install --upgrade huggingface_hub
python
from huggingface_hub import login
login()
```
Now paste in your key. Select n for git credential option and exit python.
```
exit()
```
### Repository setup
Clone this git repository:
```
git clone https://github.com/uhudo/storyteller.git
```
And continue with Servers section.
### Tunnelling the connection with ssh
When you have the servers running in the cloud use ssh tunnelling to be able to access servers on your localhost.
Use the following command in new terminal on your PC. Here XXXX is the port specified in the online AMD cloud interface when creating the workload. This will tunnel the default set ports in the config files for the servers.
```
ssh -p XXXX -L 3001:127.0.0.1:3001 -L 3002:127.0.0.1:3002 aac@aac1.amd.com
```
You will be asked for the password the same as by ssh connection.
