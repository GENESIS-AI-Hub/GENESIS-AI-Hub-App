# Stage 1: Build the React app
FROM node:18-alpine as build
WORKDIR /app
COPY package.json ./
COPY package-lock.json ./
RUN npm install
COPY . ./
# This line grabs the backend URL you pass in the deploy script
ARG REACT_APP_BACKEND_URL
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html

# 1. Remove the old default config
RUN rm /etc/nginx/conf.d/default.conf

# 2. Copy our new config file (from Step 1) into the
#    Nginx "template" directory. Nginx's startup
#    script will automatically process this file.
COPY nginx.conf /etc/nginx/templates/default.conf.template

# The default Nginx command is all we need.
# It will automatically find our template, replace ${PORT},
# and start the server correctly.
CMD ["nginx", "-g", "daemon off;"]