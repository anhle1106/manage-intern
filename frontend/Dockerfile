FROM nginx:1.25-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html

# Adjust permissions for non-root nginx execution on port 8080
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /usr/share/nginx/html

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
