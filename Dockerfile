FROM node:22-alpine AS base
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY . .
ARG NEXT_PUBLIC_LMS_API_URL=http://127.0.0.1:8000/api/v1
ENV NEXT_PUBLIC_LMS_API_URL=$NEXT_PUBLIC_LMS_API_URL
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
