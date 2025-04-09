FROM python:3.9

WORKDIR /backend

COPY ./requirements.txt /backend/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /backend

EXPOSE 3050

CMD ["python3", "main.py"]
