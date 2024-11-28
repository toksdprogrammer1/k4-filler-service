FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm install -g react-scripts

EXPOSE 3000

ENV CI=false
ENV WDS_SOCKET_PORT=0
CMD ["npm", "start"] 