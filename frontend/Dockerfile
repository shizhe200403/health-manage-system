FROM node:20-alpine AS build

WORKDIR /app

RUN npm config set registry https://registry.npmmirror.com/

COPY package.json package-lock.json /app/
RUN npm ci --no-audit --no-fund

COPY . /app
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
