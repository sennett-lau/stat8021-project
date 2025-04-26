FROM node:22.2.0

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install

COPY . .

EXPOSE 8020

CMD ["yarn", "run", "dev", "--host", "0.0.0.0"] 