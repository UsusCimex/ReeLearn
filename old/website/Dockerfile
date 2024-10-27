# Сборка
FROM node:14-alpine as build

WORKDIR /app

COPY package.json yarn.lock /app/
RUN yarn install

COPY . /app/

RUN yarn build

# Запуск
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
