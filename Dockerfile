FROM node:22-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG NEXT_PUBLIC_LMS_API_URL=/api/v1
ARG LMS_BACKEND_ORIGIN=http://backend:8000
ENV LMS_BACKEND_ORIGIN=$LMS_BACKEND_ORIGIN
ENV NEXT_PUBLIC_LMS_API_URL=$NEXT_PUBLIC_LMS_API_URL
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
