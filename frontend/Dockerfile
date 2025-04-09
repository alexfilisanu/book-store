FROM node:21

WORKDIR /frontend

COPY . /frontend

RUN npm install -g @angular/cli

RUN npm install

EXPOSE 4200

CMD ["ng", "serve", "--host", "0.0.0.0"]
