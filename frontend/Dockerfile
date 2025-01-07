FROM node:22-alpine

ENV VITE_PRODUCT_LOGO=https://sg-ui-assets.s3.us-east-1.amazonaws.com/ta_bench_logo.svg
ENV VITE_PRODUCT_ICON=https://sg-ui-assets.s3.us-east-1.amazonaws.com/ta_bench_favicon.svg
ENV VITE_PRODUCT_PAGE_TITLE="AgenticBench"
ENV VITE_WEBSOCKET_URL=ws://localhost:8081/ws

WORKDIR /app

COPY package.json .

RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD [ "npm", "run", "dev" ]