FROM node:20.9.0 AS build

WORKDIR /app

COPY app/package*.json ./
RUN npm install

COPY app .

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

COPY app/frontend.conf /etc/nginx/conf.d/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]